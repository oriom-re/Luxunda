// ===== LUX CHAT COMPONENT - CZYSTA IMPLEMENTACJA =====

class LuxChatComponent {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.isOpen = false;
        this.chatHistory = [];

        this.createChatInterface();
        this.setupEventListeners();
        this.loadChatHistory();

        console.log('💬 LuxChatComponent initialized');
    }

    createChatInterface() {
        this.chatContainer = document.createElement('div');
        this.chatContainer.className = 'lux-chat-container';
        this.chatContainer.style.cssText = `
            position: fixed;
            bottom: 140px;
            right: 20px;
            width: 400px;
            height: 500px;
            background: rgba(26, 26, 26, 0.95);
            border: 2px solid #00ff88;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            z-index: 2000;
            display: none;
            flex-direction: column;
            overflow: hidden;
        `;

        this.chatContainer.innerHTML = `
            <div class="chat-header" style="
                background: linear-gradient(45deg, #00ff88, #00cc66);
                color: #1a1a1a;
                padding: 15px 20px;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <span>💫 Chat z Lux</span>
                <button class="close-chat-btn" style="
                    background: none;
                    border: none;
                    font-size: 20px;
                    color: #1a1a1a;
                    cursor: pointer;
                ">✕</button>
            </div>
            <div class="chat-messages" style="
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                color: white;
            "></div>
            <div class="chat-input-area" style="
                padding: 20px;
                border-top: 1px solid #333;
            ">
                <textarea class="chat-message-input" placeholder="Napisz wiadomość do Lux..." style="
                    width: 100%;
                    min-height: 40px;
                    background: #333;
                    border: 1px solid #555;
                    border-radius: 8px;
                    color: white;
                    padding: 12px;
                    resize: none;
                    box-sizing: border-box;
                "></textarea>
                <button class="chat-send-btn" style="
                    background: #00ff88;
                    color: #1a1a1a;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    cursor: pointer;
                    margin-top: 10px;
                    width: 100%;
                ">💬 Wyślij</button>
            </div>
        `;

        document.body.appendChild(this.chatContainer);

        this.messagesArea = this.chatContainer.querySelector('.chat-messages');
        this.messageInput = this.chatContainer.querySelector('.chat-message-input');
        this.sendBtn = this.chatContainer.querySelector('.chat-send-btn');
        this.closeChatBtn = this.chatContainer.querySelector('.close-chat-btn');
    }

    setupEventListeners() {
        this.closeChatBtn.addEventListener('click', () => {
            this.closeChat();
        });

        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        this.addMessage('user', message);
        this.messageInput.value = '';

        if (this.graphManager && this.graphManager.socket) {
            this.graphManager.socket.emit('lux_chat', {
                message: message,
                timestamp: new Date().toISOString()
            });
        }
    }

    addMessage(sender, content) {
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${sender}-message`;

        const isUser = sender === 'user';
        messageElement.style.cssText = `
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 80%;
            word-wrap: break-word;
            ${isUser ? `
                background: #00ff88;
                color: #1a1a1a;
                margin-left: auto;
            ` : `
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border-left: 3px solid #00ff88;
            `}
        `;

        messageElement.textContent = content;
        this.messagesArea.appendChild(messageElement);
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
    }

    openChat() {
        this.isOpen = true;
        this.chatContainer.style.display = 'flex';
        this.messageInput.focus();
    }

    closeChat() {
        this.isOpen = false;
        this.chatContainer.style.display = 'none';
    }

    toggle() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    loadChatHistory() {
        this.addMessage('lux', 'Witaj! Jestem Lux, Bóg systemu LuxOS. Jak mogę pomóc?');
    }
}

console.log('✅ LuxChatComponent loaded');
window.LuxChatComponent = LuxChatComponent;
// Chat Component for LuxDB
class ChatComponent {
    constructor() {
        this.initialized = false;
        console.log('💬 Chat Component initialized');
    }

    init() {
        this.initialized = true;
        console.log('✅ Chat Component ready');
    }

    sendMessage(message) {
        console.log('📤 Sending message:', message);
    }

    receiveMessage(message) {
        console.log('📥 Received message:', message);
    }
}

// Global instance
window.chatComponent = new ChatComponent();
