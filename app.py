from flask import Flask, render_template, request, Response, json
import re
import sys
import threading
from queue import Queue, Empty

app = Flask(__name__)

class StreamCapture:
    def __init__(self):
        self.queue = Queue()
        self.original_stdout = sys.stdout
        self.lock = threading.Lock()

    def write(self, text):
        with self.lock:
            self.original_stdout.write(text)  # 保持控制台输出
            self.queue.put(text)
    
    def flush(self):
        self.original_stdout.flush()

def capture_output_stream(params):
    capture = StreamCapture()
    sys.stdout = capture

    def run_init_chat():
        try:
            from test_autogen import init_chat
            # print(params)
            init_chat(params)
        finally:
            sys.stdout = capture.original_stdout
            capture.queue.put(None)  # 结束信号

    thread = threading.Thread(target=run_init_chat)
    thread.start()

    return capture

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    try:
        # 解析请求参数
        user_input = request.args.get('message', '')
        agents = json.loads(request.args.get('agents', '[]'))
        models = json.loads(request.args.get('models', '[]'))
        max_turns = int(request.args.get('max_turns', '2'))
        
        # 参数验证
        if len(agents) != 7 or len(models) != 7:
            raise ValueError("Invalid configuration: expected 7 agents and 7 models")
            
        # 构建参数字典
        params = {
            'prompt': user_input,
            'agents': agents,
            'models': models,
            'max_turns': max_turns
        }
        
    except Exception as e:
        def error_generator():
            yield f"data: {json.dumps({'speaker': 'System', 'content': f'配置错误: {str(e)}'})}\n\n"
            yield "event: end\ndata: \n\n"
        return Response(error_generator(), mimetype="text/event-stream")

    def generate():
        try:
            capture = capture_output_stream(params)
            current_speaker = "System"
            buffer = ""
            speaker_pattern = re.compile(r'Next speaker: (\S+)')

            while True:
                try:
                    text = capture.queue.get(timeout=360)  # 6分钟超时
                    if text is None:  # 结束信号
                        break

                    # 处理输出内容
                    parts = re.split(r'(Next speaker: \S+)', text)
                    for part in parts:
                        if not part:
                            continue
                        
                        # 检测发言人变更
                        match = speaker_pattern.match(part)
                        if match:
                            if buffer.strip():
                                yield format_message(current_speaker, buffer)
                            current_speaker = match.group(1)
                            buffer = ""
                        else:
                            buffer += part

                    # 发送缓冲区内容
                    if buffer.strip():
                        yield format_message(current_speaker, buffer)
                        buffer = ""

                except Empty:
                    yield format_message("System", "响应超时")
                    break
                except Exception as e:
                    yield format_message("System", f"处理错误: {str(e)}")
                    break

            # 发送剩余内容
            if buffer.strip():
                yield format_message(current_speaker, buffer)
                
            yield "event: end\ndata: \n\n"

        except Exception as e:
            yield format_message("System", f"系统错误: {str(e)}")
            yield "event: end\ndata: \n\n"

    return Response(generate(), mimetype="text/event-stream")

def format_message(speaker, content):
    return f"data: {json.dumps({'speaker': speaker, 'content': content.strip()})}\n\n"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)