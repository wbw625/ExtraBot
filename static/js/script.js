document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    function addMessage(content, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    
        // 创建头像
        const avatar = document.createElement('div');
        avatar.className = `avatar ${isUser ? 'user-avatar' : 'bot-avatar'}`;
        avatar.textContent = isUser ? 'You' : 'Bot';
    
        // 消息内容包装
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper';
    
        // 用户名
        const username = document.createElement('div');
        username.className = 'username';
        username.textContent = isUser ? 'You' : 'AI Assistant';
    
        // 消息内容
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
    
        wrapper.appendChild(username);
        wrapper.appendChild(contentDiv);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(wrapper);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return;

        input.value = '';
        addMessage(message, true);

        try {
            const response = await fetch('/get_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `message=${encodeURIComponent(message)}`
            });

            const data = await response.json();
            addMessage(data.answer, false);
        } catch (error) {
            addMessage('无法连接到服务器', false);
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 自动调整输入框高度
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
    });
});