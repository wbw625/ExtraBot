from flask import Flask, render_template, request, Response
import re
import json
import threading
import sys
from queue import Queue, Empty
from test_autogen import init_chat

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

def capture_output_stream(args):
    capture = StreamCapture()
    sys.stdout = capture

    def run_init_chat():
        try:
            init_chat(args)
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
    user_input = request.args.get('message')
    
    def generate():
        capture = capture_output_stream(user_input)
        current_speaker = "AI Assistant"
        buffer = ""
        speaker_pattern = re.compile(r'Next speaker: (\S+)')

        while True:
            try:
                text = capture.queue.get(timeout=360)  # 超时时间360秒
                if text is None:  # 结束信号
                    break

                # 分割处理逻辑
                parts = re.split(r'(Next speaker: \S+)', text)
                for part in parts:
                    if not part:
                        continue
                    
                    match = speaker_pattern.match(part)
                    if match:
                        if buffer:
                            yield format_message(current_speaker, buffer)
                        current_speaker = match.group(1)
                        buffer = ""
                    else:
                        buffer += part

                # 发送当前缓冲区内容
                if buffer.strip():
                    yield format_message(current_speaker, buffer)
                    buffer = ""

            except Empty:
                yield format_message("System", "响应超时")
                break
            except Exception as e:
                yield format_message("System", f"错误: {str(e)}")
                break

        if buffer.strip():
            yield format_message(current_speaker, buffer)
        yield "event: end\ndata: \n\n"

    return Response(generate(), mimetype="text/event-stream")

def format_message(speaker, content):
    return f"data: {json.dumps({'speaker': speaker, 'content': content.strip()})}\n\n"

if __name__ == '__main__':
    app.run(debug=True)