from flask import Flask, render_template, request, Response
import re
import json
import threading
import io
import sys
from test_autogen import init_chat

app = Flask(__name__)

def capture_output(args):
    func = init_chat
    buffer = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buffer

    def target():
        try:
            func(args)
        except Exception as e:
            raise e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(360)

    if thread.is_alive():
        raise TimeoutError(f"Function execution exceeded {360} seconds.")

    sys.stdout = sys_stdout
    return buffer.getvalue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    user_input = request.args.get('message')
    
    def generate():
        try:
            full_output = capture_output(user_input)
            segments = re.split(r'(Next speaker: \S+)', full_output)
            
            current_speaker = "AI Assistant"
            buffer = ""
            
            for segment in segments:
                if segment.startswith("Next speaker: "):
                    if buffer:
                        yield f"data: {json.dumps({'speaker': current_speaker, 'content': buffer.strip()})}\n\n"
                    current_speaker = segment.split(": ")[1].strip()
                    buffer = ""
                else:
                    buffer += segment
            
            if buffer.strip():
                yield f"data: {json.dumps({'speaker': current_speaker, 'content': buffer.strip()})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'speaker': 'System', 'content': f'Error: {str(e)}'})}\n\n"
        finally:
            yield "event: end\ndata: \n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True)