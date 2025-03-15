from flask import Flask, render_template, request, Response, json, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
import sys
import threading
from queue import Queue, Empty

app = Flask(__name__)
app.secret_key = '031008'  # 生产环境需要更安全的密钥
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 登录检查装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('chat'))
        flash('用户名或密码错误')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
            
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

class StreamCapture:
    # 保持原有StreamCapture类不变
    def __init__(self):
        self.queue = Queue()
        self.original_stdout = sys.stdout
        self.lock = threading.Lock()

    def write(self, text):
        with self.lock:
            self.original_stdout.write(text)
            self.queue.put(text)
    
    def flush(self):
        self.original_stdout.flush()

def capture_output_stream(params):
    # 保持原有capture_output_stream函数不变
    capture = StreamCapture()
    sys.stdout = capture

    def run_init_chat():
        try:
            from test_autogen import init_chat
            init_chat(params)
        finally:
            sys.stdout = capture.original_stdout
            capture.queue.put(None)

    thread = threading.Thread(target=run_init_chat)
    thread.start()
    return capture

@app.route('/stream')
@login_required
def stream():
    try:
        # 保持原有参数处理逻辑
        user_input = request.args.get('message', '')
        agents = json.loads(request.args.get('agents', '[]'))
        models = json.loads(request.args.get('models', '[]'))
        max_turns = int(request.args.get('max_turns', '2'))
        
        if len(agents) != 7 or len(models) != 7:
            raise ValueError("Invalid configuration: expected 7 agents and 7 models")
            
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
        # 保持原有生成器逻辑不变
        try:
            capture = capture_output_stream(params)
            current_speaker = "System"
            buffer = ""
            speaker_pattern = re.compile(r'Next speaker: (\S+)')

            while True:
                try:
                    text = capture.queue.get(timeout=360)
                    if text is None: break

                    parts = re.split(r'(Next speaker: \S+)', text)
                    for part in parts:
                        if not part: continue
                        
                        match = speaker_pattern.match(part)
                        if match:
                            if buffer.strip():
                                yield format_message(current_speaker, buffer)
                            current_speaker = match.group(1)
                            buffer = ""
                        else:
                            buffer += part

                    if buffer.strip():
                        yield format_message(current_speaker, buffer)
                        buffer = ""

                except Empty:
                    yield format_message("System", "响应超时")
                    break
                except Exception as e:
                    yield format_message("System", f"处理错误: {str(e)}")
                    break

            if buffer.strip():
                yield format_message(current_speaker, buffer)
                
            yield "event: end\ndata: \n\n"

        except Exception as e:
            yield format_message("System", f"系统错误: {str(e)}")
            yield "event: end\ndata: \n\n"

    return Response(generate(), mimetype="text/event-stream")

def format_message(speaker, content):
    return f"data: {json.dumps({'speaker': speaker, 'content': content.strip()})}\n\n"

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(current_user=user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)