from flask import Flask, render_template, request, jsonify
from test_autogen import init_chat, capture_output

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form['message']
    # 调用AI生成函数
    try:
        ai_response = capture_output(user_input)
    except Exception as e:
        ai_response = f"生成回答时出错: {str(e)}"
    return jsonify({'answer': ai_response})

if __name__ == '__main__':
    app.run(debug=True)