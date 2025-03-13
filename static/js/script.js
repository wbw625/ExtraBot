document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    function addMessage(content, speaker, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;

        // 创建头像
        const avatar = document.createElement('div');
        avatar.className = `avatar ${isUser ? 'user-avatar' : 'bot-avatar'}`;
        if (!isUser) {
            const icon = document.createElement('i');
            icon.className = 'fas fa-robot';
            avatar.appendChild(icon);
        } else {
            avatar.textContent = 'You';
        }

        // 消息包装
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper';

        // 用户名
        const username = document.createElement('div');
        username.className = 'username';
        username.textContent = isUser ? 'You' : speaker;

        // 消息内容
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = content.replace(/\n/g, '<br>');

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
        addMessage(message, 'User', true);

        const eventSource = new EventSource(`/stream?message=${encodeURIComponent(message)}`);
        
        eventSource.onmessage = (event) => {
            if (event.data.trim() === '') return;
            
            try {
                const data = JSON.parse(event.data);
                if (data.content) {
                    addMessage(data.content, data.speaker, false);
                }
            } catch (error) {
                console.error('Error parsing event:', error);
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            addMessage("对话已结束", "System", false);
        };
    }

    sendBtn.addEventListener('click', sendMessage);
    
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
    });
});