document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    let isGenerating = false;

    // 自动调整输入框高度
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
    });

    // 回车发送（Shift+Enter换行）
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !isGenerating) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 发送按钮点击事件
    sendBtn.addEventListener('click', (e) => {
        if (!isGenerating) sendMessage();
    });

    async function sendMessage() {
        const message = input.value.trim();
        if (!message || isGenerating) return;

        isGenerating = true;
        input.disabled = true;
        sendBtn.disabled = true;
        clearInput();
        addUserMessage(message);

        const eventSource = new EventSource(`/stream?message=${encodeURIComponent(message)}`);
        let currentSpeaker = null;
        let currentMessageElement = null;

        eventSource.onmessage = (event) => {
            try {
                // 处理结束信号
                if (event.data.trim() === '' || event.event === 'end') {
                    eventSource.close();
                    return;
                }

                const data = JSON.parse(event.data);
                
                // 处理新发言人
                if (data.speaker !== currentSpeaker) {
                    currentSpeaker = data.speaker;
                    currentMessageElement = createBotMessageElement(data.speaker);
                    chatMessages.appendChild(currentMessageElement);
                }

                // 追加内容
                if (currentMessageElement) {
                    const contentDiv = currentMessageElement.querySelector('.message-content');
                    contentDiv.innerHTML += escapeHtml(data.content).replace(/\n/g, '<br>');
                    scrollToBottom();
                }
            } catch (error) {
                console.error('Error parsing event:', error);
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            addSystemMessage('对话已结束');
            resetUI();
        };

        // 添加超时处理
        setTimeout(() => {
            if (isGenerating) {
                eventSource.close();
                addSystemMessage('响应超时，请重试');
                resetUI();
            }
        }, 360000); // 6分钟超时
    }

    // 工具函数：创建用户消息
    function addUserMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        
        const avatar = createAvatarElement('user');
        const wrapper = createMessageWrapper('You', content);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(wrapper);
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // 工具函数：创建机器人消息元素
    function createBotMessageElement(speaker) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(10px)';

        const avatar = createAvatarElement('bot', speaker);
        const wrapper = createMessageWrapper(speaker, '');

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(wrapper);

        // 添加渐入动画
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);

        return messageDiv;
    }

    // 工具函数：创建头像
    function createAvatarElement(type, speaker) {
        const avatar = document.createElement('div');
        avatar.className = `avatar ${type}-avatar`;

        if (type === 'bot') {
            const icon = document.createElement('i');
            icon.className = 'fas fa-robot';
            avatar.appendChild(icon);
        } else {
            avatar.textContent = 'You';
        }

        return avatar;
    }

    // 工具函数：创建消息包装
    function createMessageWrapper(username, content) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper';

        const usernameDiv = document.createElement('div');
        usernameDiv.className = 'username';
        usernameDiv.textContent = username;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = escapeHtml(content).replace(/\n/g, '<br>');

        wrapper.appendChild(usernameDiv);
        wrapper.appendChild(contentDiv);
        return wrapper;
    }

    // 工具函数：添加系统消息
    function addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message';
        messageDiv.innerHTML = `
            <div class="message-content">${content}</div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // 工具函数：滚动到底部
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 工具函数：清空输入框
    function clearInput() {
        input.value = '';
        input.style.height = 'auto';
    }

    // 工具函数：重置UI状态
    function resetUI() {
        isGenerating = false;
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }

    // 工具函数：HTML转义
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});