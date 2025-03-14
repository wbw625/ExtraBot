document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const configModal = document.getElementById('configModal');
    let isGenerating = false;
    let agentsConfig = [];
    let modelsConfig = [];

    // 初始化配置弹窗
    const agentConfigs = document.getElementById('agentConfigs');
    for (let i = 0; i < 6; i++) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <select class="agent-type" data-index="${i}">
                    <option value="none">none</option>
                    <option value="coder">coder</option>
                    <option value="product_manager">product_manager</option>
                    <option value="guardian">guardian</option>
                </select>
            </td>
            <td>
                <select class="model-select" data-index="${i}">
                    <option value="none">none</option>
                    <option value="llama">llama</option>
                    <option value="qwen">qwen</option>
                    <option value="deepseek" selected>deepseek</option>
                    <option value="mistralai">mistralai</option>
                    <option value="gemma">gemma</option>
                </select>
            </td>
        `;
        agentConfigs.appendChild(row);
    }

    // 初始化模型选择状态
    document.querySelectorAll('.agent-type').forEach((select, index) => {
        const modelSelect = document.querySelector(`.model-select[data-index="${index}"]`);
        if (select.value === 'none') {
            modelSelect.value = 'none';
            modelSelect.disabled = true;
        }
    });

    // Agent类型变化事件
    agentConfigs.addEventListener('change', (e) => {
        if (e.target.classList.contains('agent-type')) {
            const index = e.target.dataset.index;
            const agentSelect = e.target;
            const modelSelect = document.querySelector(`.model-select[data-index="${index}"]`);
            const originalOptions = modelSelect.querySelectorAll('option'); // 保存原始选项

            if (agentSelect.value === 'none') {
                // 当切换为none时
                modelSelect.innerHTML = '<option value="none">none</option>'; // 重置选项
                modelSelect.value = 'none';
                modelSelect.disabled = true;
            } else {
                // 当切换为非none时
                modelSelect.disabled = false;
                // 恢复原始选项（排除none）
                modelSelect.innerHTML = '<option value="llama">llama</option><option value="qwen">qwen</option><option value="deepseek" selected>deepseek</option><option value="mistralai">mistralai</option><option value="gemma">gemma</option>';
                // originalOptions.forEach(option => {
                //     if (option.value !== 'none') {
                //         modelSelect.appendChild(option.cloneNode(true));
                //     }
                // });
                // 设置默认值并检查当前值
                if (!modelSelect.value || modelSelect.value === 'none') {
                    modelSelect.value = 'deepseek';
                }
            }
        }
    });
    // 确认配置
    document.getElementById('confirmConfig').addEventListener('click', () => {
        // 验证所有配置
        let isValid = true;
        
        document.querySelectorAll('.agent-type').forEach((select, index) => {
            const agent = select.value;
            const model = document.querySelector(`.model-select[data-index="${index}"]`).value;

            if (agent !== 'none' && model === 'none') {
                isValid = false;
                select.classList.add('error');
            } else {
                select.classList.remove('error');
            }
        });

        if (!isValid) {
            alert('存在无效配置：Agent类型非none时必须选择模型！');
            return;
        }

        // 收集有效配置
        agentsConfig = [];
        modelsConfig = [];
        document.querySelectorAll('.agent-type').forEach((select, index) => {
            agentsConfig.push(select.value);
            modelsConfig.push(document.querySelector(`.model-select[data-index="${index}"]`).value);
        });

        // 添加第7个固定配置
        agentsConfig.push('user_proxy');
        modelsConfig.push('none');
        configModal.style.display = 'none';
    });

    // 输入框自适应高度
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
    });

    // 发送消息
    async function sendMessage() {
        const message = input.value.trim();
        if (!message || isGenerating) return;

        isGenerating = true;
        input.disabled = true;
        sendBtn.disabled = true;
        clearInput();
        addUserMessage(message);

        const params = new URLSearchParams({
            message: message,
            agents: JSON.stringify(agentsConfig),
            models: JSON.stringify(modelsConfig)
        });

        const eventSource = new EventSource(`/stream?${params.toString()}`);
        let currentSpeaker = null;
        let currentMessageElement = null;

        eventSource.onmessage = (event) => {
            if (event.data.trim() === '') return;

            try {
                const data = JSON.parse(event.data);
                
                if (data.speaker !== currentSpeaker) {
                    currentSpeaker = data.speaker;
                    currentMessageElement = createBotMessage(currentSpeaker);
                    chatMessages.appendChild(currentMessageElement);
                }

                if (currentMessageElement) {
                    const contentDiv = currentMessageElement.querySelector('.message-content');
                    contentDiv.innerHTML += escapeHtml(data.content).replace(/\n/g, '<br>');
                    scrollToBottom();
                }
            } catch (error) {
                console.error('解析错误:', error);
            }
        };

        eventSource.addEventListener('end', () => {
            eventSource.close();
            resetUI();
            addSystemMessage('对话结束');
        });

        eventSource.onerror = () => {
            eventSource.close();
            resetUI();
            addSystemMessage('连接中断');
        };

        // 6分钟超时
        setTimeout(() => {
            if (isGenerating) {
                eventSource.close();
                resetUI();
                addSystemMessage('响应超时');
            }
        }, 360000);
    }

    // 工具函数
    function addUserMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="avatar user-avatar">You</div>
            <div class="message-wrapper">
                <div class="username">You</div>
                <div class="message-content">${escapeHtml(content)}</div>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function createBotMessage(speaker) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(10px)';
        messageDiv.innerHTML = `
            <div class="avatar bot-avatar"><i class="fas fa-robot"></i></div>
            <div class="message-wrapper">
                <div class="username">${escapeHtml(speaker)}</div>
                <div class="message-content"></div>
            </div>
        `;
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'none';
        }, 10);
        return messageDiv;
    }

    function addSystemMessage(content) {
        const div = document.createElement('div');
        div.className = 'message system-message';
        div.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
        chatMessages.appendChild(div);
        scrollToBottom();
    }

    function clearInput() {
        input.value = '';
        input.style.height = 'auto';
    }

    function resetUI() {
        isGenerating = false;
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // 事件监听
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});