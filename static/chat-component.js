
class LuxChatComponent {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.isOpen = false;
        this.chatHistory = [];
        this.luxSoul = '00000000-0000-0000-0000-000000000001';
        
        this.createChatInterface();
        this.setupEventListeners();
        this.loadChatHistory();
        
        console.log('LuxChatComponent initialized');
    }

    createChatInterface() {
        // Główny kontener chatu
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
            box-shadow: 0 20px 40px rgba(0, 255, 136, 0.3);
        `;

        // Header chatu
        const chatHeader = document.createElement('div');
        chatHeader.className = 'chat-header';
        chatHeader.style.cssText = `
            background: linear-gradient(45deg, #00ff88, #00cc66);
            color: #1a1a1a;
            padding: 15px 20px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 13px 13px 0 0;
        `;

        chatHeader.innerHTML = `
            <div class="chat-title">
                <span>💫 Chat z Lux</span>
                <div style="font-size: 12px; font-weight: normal; opacity: 0.8;">
                    Bóg systemu LuxOS
                </div>
            </div>
            <button class="close-chat-btn" style="
                background: none;
                border: none;
                font-size: 20px;
                color: #1a1a1a;
                cursor: pointer;
                padding: 5px;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            ">✕</button>
        `;

        // Obszar wiadomości
        this.messagesArea = document.createElement('div');
        this.messagesArea.className = 'chat-messages';
        this.messagesArea.style.cssText = `
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            color: white;
            font-size: 14px;
            line-height: 1.6;
        `;

        // Pole wprowadzania wiadomości
        const inputArea = document.createElement('div');
        inputArea.className = 'chat-input-area';
        inputArea.style.cssText = `
            padding: 20px;
            border-top: 1px solid #333;
            background: rgba(0, 0, 0, 0.3);
        `;

        this.messageInput = document.createElement('textarea');
        this.messageInput.className = 'chat-message-input';
        this.messageInput.placeholder = 'Napisz wiadomość do Lux...';
        this.messageInput.style.cssText = `
            width: 100%;
            min-height: 40px;
            max-height: 120px;
            background: #333;
            border: 1px solid #555;
            border-radius: 8px;
            color: white;
            padding: 12px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            resize: none;
            box-sizing: border-box;
        `;

        const sendButton = document.createElement('button');
        sendButton.className = 'chat-send-btn';
        sendButton.textContent = '💬 Wyślij';
        sendButton.style.cssText = `
            background: #00ff88;
            color: #1a1a1a;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
            width: 100%;
            transition: all 0.3s ease;
        `;

        inputArea.appendChild(this.messageInput);
        inputArea.appendChild(sendButton);

        // Złóż wszystko
        this.chatContainer.appendChild(chatHeader);
        this.chatContainer.appendChild(this.messagesArea);
        this.chatContainer.appendChild(inputArea);

        document.body.appendChild(this.chatContainer);

        // Zapisz referencje do przycisków
        this.closeChatBtn = chatHeader.querySelector('.close-chat-btn');
        this.sendBtn = sendButton;
    }

    setupEventListeners() {
        // Zamknij chat
        this.closeChatBtn.addEventListener('click', () => {
            this.closeChat();
        });

        // Wyślij wiadomość
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter wysyła wiadomość
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });

        // Socket.IO listeners
        if (this.graphManager && this.graphManager.socket) {
            this.graphManager.socket.on('lux_chat_response', (response) => {
                this.handleLuxResponse(response);
            });

            this.graphManager.socket.on('intention_response', (response) => {
                // Dodaj odpowiedź intencji do historii chatu
                if (response.message_being_soul) {
                    this.addIntentionToHistory(response);
                }
            });
        }
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        const scrollHeight = this.messageInput.scrollHeight;
        const minHeight = 40;
        const maxHeight = 120;
        const newHeight = Math.max(minHeight, Math.min(maxHeight, scrollHeight));
        this.messageInput.style.height = newHeight + 'px';
    }

    openChat() {
        this.isOpen = true;
        this.chatContainer.style.display = 'flex';
        this.messageInput.focus();
        
        // Animacja wejścia
        this.chatContainer.style.transform = 'translateY(20px)';
        this.chatContainer.style.opacity = '0';
        
        setTimeout(() => {
            this.chatContainer.style.transition = 'all 0.3s ease';
            this.chatContainer.style.transform = 'translateY(0)';
            this.chatContainer.style.opacity = '1';
        }, 10);

        // Pobierz najnowszą historię przy otwieraniu
        this.loadChatHistory();
    }

    closeChat() {
        this.isOpen = false;
        this.chatContainer.style.transform = 'translateY(20px)';
        this.chatContainer.style.opacity = '0';
        
        setTimeout(() => {
            this.chatContainer.style.display = 'none';
        }, 300);
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Dodaj wiadomość użytkownika do interfejsu
        this.addMessage('user', message);

        // Wyczyść input
        this.messageInput.value = '';
        this.autoResizeTextarea();

        // Wyślij do serwera przez lux_communication dla natychmiastowego działania
        if (this.graphManager && this.graphManager.socket) {
            this.graphManager.socket.emit('lux_communication', {
                message: message,
                context: {
                    chat_mode: true,
                    timestamp: new Date().toISOString()
                }
            });
        }

        // Nie zapisujemy historii - Lux działa w trybie action-only
    }

    addMessage(sender, content, timestamp = null) {
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${sender}-message`;
        
        const isUser = sender === 'user';
        const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        
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
                text-align: right;
            ` : `
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border-left: 3px solid #00ff88;
            `}
        `;

        messageElement.innerHTML = `
            <div class="message-content" style="margin-bottom: 5px;">
                ${this.formatMessageContent(content)}
            </div>
            <div class="message-time" style="
                font-size: 11px;
                opacity: 0.7;
                ${isUser ? 'text-align: right;' : 'text-align: left;'}
            ">
                ${isUser ? 'Ty' : '💫 Lux'} • ${time}
            </div>
        `;

        this.messagesArea.appendChild(messageElement);
        this.scrollToBottom();
    }

    formatMessageContent(content) {
        // Formatuj tekst - dodaj podstawowe markdown
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background: rgba(0,255,136,0.2); padding: 2px 4px; border-radius: 3px;">$1</code>')
            .replace(/\n/g, '<br>');
    }

    scrollToBottom() {
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
    }

    handleLuxResponse(response) {
        // Obsłuż różne typy odpowiedzi od Lux
        if (response.lux_response) {
            this.addMessage('lux', response.lux_response, response.timestamp);
            
            // Dodaj sugestie następnych działań jeśli są
            if (response.next_suggestions && response.next_suggestions.length > 0) {
                const suggestionsText = "\n\n🎯 Następne kroki:\n" + 
                    response.next_suggestions.map(s => `• ${s}`).join('\n');
                this.addMessage('lux', suggestionsText, response.timestamp);
            }
            
            // Pokaż utworzone byty
            if (response.action_result && response.action_result.created_beings && response.action_result.created_beings.length > 0) {
                const beingsText = `\n✨ Utworzono ${response.action_result.created_beings.length} nowych bytów`;
                this.addMessage('lux', beingsText, response.timestamp);
            }
            
            // Pokaż manifestację jeśli utworzono
            if (response.manifestation) {
                this.addMessage('lux', "📜 Utworzono manifestację działania", response.timestamp);
            }
        }

        // Nie zapisujemy historii - komunikacja action-only
    }

    addIntentionToHistory(intentionResponse) {
        // Dodaj wpis o intencji do historii chatu
        const intentionSummary = `Intencja: "${intentionResponse.intention}" - ${intentionResponse.message}`;
        
        this.addMessage('system', intentionSummary, new Date().toISOString());

        this.chatHistory.push({
            type: 'intention',
            content: intentionResponse.intention,
            response: intentionResponse.message,
            timestamp: new Date().toISOString(),
            full_response: intentionResponse
        });

        this.saveChatHistory();
    }

    loadChatHistory() {
        // Lux nie pamięta historii - każda interakcja to nowy początek
        this.chatHistory = [];
        this.messagesArea.innerHTML = '';
        this.addWelcomeMessage();
    }

    addWelcomeMessage() {
        const welcomeMsg = `🚀 Lux gotowy do działania!

Co chcesz teraz osiągnąć?
• Stwórz nowe wydarzenie
• Manifestuj decyzję  
• Przeanalizuj system
• Połącz byty
• Zoptymalizuj przepływ

Powiedz mi co robić - działam natychmiast, bez długich rozmów.`;

        this.addMessage('lux', welcomeMsg);
        
        // Nie zapisujemy historii - Lux nie pamięta poprzednich rozmów
        console.log('Lux ready for action-focused communication');
    }

    renderChatHistory() {
        this.messagesArea.innerHTML = '';
        
        // Pokaż tylko ostatnie 20 wiadomości
        const recentHistory = this.chatHistory.slice(-20);
        
        recentHistory.forEach(item => {
            switch (item.type) {
                case 'user_message':
                    this.addMessage('user', item.content, item.timestamp);
                    break;
                case 'lux_response':
                    this.addMessage('lux', item.content, item.timestamp);
                    break;
                case 'intention':
                    const intentionText = `Intencja: "${item.content}" - ${item.response}`;
                    this.addMessage('system', intentionText, item.timestamp);
                    break;
            }
        });
    }

    saveChatHistory() {
        // Zachowaj tylko ostatnie 50 wpisów
        if (this.chatHistory.length > 50) {
            this.chatHistory = this.chatHistory.slice(-50);
        }
        
        localStorage.setItem('luxos_chat_history', JSON.stringify(this.chatHistory));
    }

    // Metoda do otwierania chatu z zewnątrz (np. po kliknięciu na Lux)
    openChatWithLux() {
        this.openChat();
        
        // Jeśli chat był zamknięty przez dłuższy czas, dodaj informację o statusie
        const lastMessage = this.chatHistory[this.chatHistory.length - 1];
        const timeSinceLastMessage = lastMessage ? 
            (Date.now() - new Date(lastMessage.timestamp).getTime()) / 1000 / 60 : 0;
        
        if (timeSinceLastMessage > 30) { // 30 minut
            this.addMessage('lux', `Witaj ponownie! Czy jest coś, z czym mogę Ci pomóc?`);
        }
    }

    toggle() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChatWithLux();
        }
    }
}

// Udostępnij globalnie
window.LuxChatComponent = LuxChatComponent;
