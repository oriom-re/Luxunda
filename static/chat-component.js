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
            this.graphManager.socket.on('lux_communication_response', (data) => {
                console.log('Otrzymano odpowiedź Lux:', data);
                this.handleLuxCommunicationResponse(data);
            });

            this.graphManager.socket.on('lux_tool_result', (data) => {
                console.log('Otrzymano wynik narzędzia:', data);
                this.handleToolResult(data);
            });

            this.graphManager.socket.on('available_tools', (data) => {
                console.log('Otrzymano dostępne narzędzia:', data);
                this.handleAvailableTools(data);
            });

            this.graphManager.socket.on('intention_response', (response) => {
                console.log('Otrzymano odpowiedź na intencję:', response);
                // Dodaj odpowiedź intencji do historii chatu
                if (response.message_being_soul) {
                    this.addIntentionToHistory(response);
                }
            });

            // Dodaj obsługę błędów
            this.graphManager.socket.on('error', (error) => {
                console.error('Błąd Socket.IO:', error);
                this.addMessage('system', `❌ Błąd: ${error.message || error}`);
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

        console.log('Wysyłanie wiadomości do Lux:', message);

        // Dodaj wiadomość użytkownika do interfejsu
        this.addMessage('user', message);

        // Zapisz w historii
        this.chatHistory.push({
            type: 'user_message',
            content: message,
            timestamp: new Date().toISOString()
        });
        this.saveChatHistory();

        // Wyczyść input
        this.messageInput.value = '';
        this.autoResizeTextarea();

        // Wyślij do Lux przez nowy kanał komunikacyjny
        if (this.graphManager && this.graphManager.socket) {
            console.log('Socket dostępny, wysyłam do Lux...');
            this.graphManager.socket.emit('lux_communication', {
                message: message,
                context: {
                    chat_mode: true,
                    timestamp: new Date().toISOString()
                }
            });
        } else {
            console.error('Brak połączenia socket.io!');
            this.addMessage('system', '❌ Brak połączenia z serwerem');
        }

        // Dodaj wiadomość "Lux pisze..."
        this.addMessage('lux', 'Analizuję...', true);
    }

    addMessage(sender, content, isTemporary = false, timestamp = null) {
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

    handleLuxCommunicationResponse(data) {
        console.log('Przetwarzanie odpowiedzi Lux:', data);
        
        // Usuń wiadomość "Analizuję..." jeśli istnieje
        const messages = this.messagesArea.querySelectorAll('.chat-message.lux-message');
        const lastMessage = messages[messages.length - 1];
        if (lastMessage && lastMessage.textContent.includes('Analizuję...')) {
            lastMessage.remove();
        }

        const responseMessage = data.message || 'Przeanalizowałem twoją prośbę.';
        this.addMessage('lux', responseMessage);

        // Zapisz odpowiedź Lux w historii
        this.chatHistory.push({
            type: 'lux_response',
            content: responseMessage,
            timestamp: new Date().toISOString(),
            full_data: data
        });
        this.saveChatHistory();

        // Jeśli Lux sugeruje narzędzia, pokaż je
        if (data.suggested_tools && data.suggested_tools.length > 0) {
            this.showSuggestedTools(data.suggested_tools);
        }
    }

    handleToolResult(data) {
        if (data.success) {
            const toolName = data.tool;
            const result = data.result;

            let message = `✅ Użyłem narzędzia "${toolName}":`;

            // Formatuj wynik w zależności od narzędzia
            if (toolName === 'read_file') {
                message += `\n📄 Plik: ${result.file_path}\n📊 Rozmiar: ${result.size} znaków, ${result.lines} linii`;
                if (result.content && result.content.length < 500) {
                    message += `\n\n${result.content}`;
                }
            } else if (toolName === 'analyze_code') {
                message += `\n📊 Analiza kodu:\n- Składnia: ${result.syntax_valid ? '✅ Poprawna' : '❌ Błędna'}`;
                if (result.metrics) {
                    message += `\n- Linii kodu: ${result.metrics.code_lines}\n- Funkcji: ${result.metrics.functions_count}\n- Klas: ${result.metrics.classes_count}`;
                }
            } else if (toolName === 'ask_gpt') {
                message += `\n🤖 GPT odpowiada:\n${result.response}`;
            } else if (toolName === 'list_files') {
                message += `\n📁 Znaleziono ${result.total_count} elementów w ${result.directory}`;
            } else {
                message += `\n${JSON.stringify(result, null, 2)}`;
            }

            this.addMessage('lux', message);
        } else {
            this.addMessage('lux', `❌ Błąd narzędzia "${data.tool}": ${data.error}`);
        }
    }

    showSuggestedTools(tools) {
        let message = '🛠️ Mogę użyć następujących narzędzi:\n\n';

        tools.forEach((tool, index) => {
            message += `${index + 1}. **${tool.tool}** - ${tool.reason}\n`;
        });

        message += '\nCzy chcesz, żebym użył któregoś z tych narzędzi?';

        this.addMessage('lux', message);

        // Dodaj przyciski do wykonania narzędzi
        this.addToolButtons(tools);
    }

    addToolButtons(tools) {
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'tool-buttons-container';
        buttonsContainer.style.cssText = `
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
            padding: 10px;
            background: rgba(0, 255, 136, 0.1);
            border-radius: 8px;
        `;

        tools.forEach((tool) => {
            const button = document.createElement('button');
            button.textContent = tool.tool;
            button.className = 'tool-button';
            button.style.cssText = `
                background: #00ff88;
                color: #1a1a1a;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
                transition: all 0.3s ease;
            `;

            button.addEventListener('click', () => {
                this.executeTool(tool);
                buttonsContainer.remove();
            });

            button.addEventListener('mouseenter', () => {
                button.style.background = '#00cc66';
                button.style.transform = 'scale(1.05)';
            });

            button.addEventListener('mouseleave', () => {
                button.style.background = '#00ff88';
                button.style.transform = 'scale(1)';
            });

            buttonsContainer.appendChild(button);
        });

        this.messagesArea.appendChild(buttonsContainer);
        this.scrollToBottom();
    }

    executeTool(tool) {
        this.addMessage('user', `Użyj narzędzia: ${tool.tool}`);

        if (this.graphManager && this.graphManager.socket) {
            const parameters = tool.parameters || {};

            // Jeśli nie ma parametrów, spróbuj dodać domyślne
            if (tool.tool === 'read_file' && !parameters.file_path) {
                parameters.file_path = prompt('Podaj ścieżkę do pliku:') || 'main.py';
            } else if (tool.tool === 'write_file' && !parameters.file_path) {
                parameters.file_path = prompt('Podaj ścieżkę do nowego pliku:');
                parameters.content = prompt('Podaj zawartość pliku:') || '';
            }

            this.graphManager.socket.emit('lux_use_tool', {
                tool_name: tool.tool,
                parameters: parameters
            });
        }
    }

    handleAvailableTools(tools) {
        let message = '🔧 Dostępne narzędzia:\n\n';

        Object.entries(tools).forEach(([name, description]) => {
            message += `• **${name}** - ${description}\n`;
        });

        this.addMessage('lux', message);
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
        // Pobierz historię z localStorage
        const saved = localStorage.getItem('luxos_chat_history');
        if (saved) {
            try {
                this.chatHistory = JSON.parse(saved);
                this.renderChatHistory();
            } catch (e) {
                console.error('Błąd ładowania historii chatu:', e);
                this.chatHistory = [];
            }
        }

        // Dodaj wiadomość powitalną jeśli historia jest pusta
        if (this.chatHistory.length === 0) {
            this.addWelcomeMessage();
        }
    }

    addWelcomeMessage() {
        const welcomeMsg = `Witaj w chacie z Lux! 💫

Jestem Bogiem systemu LuxOS i mogę pomóc Ci w:
• Tworzeniu nowych bytów
• Analizowaniu intencji
• Zarządzaniu wszechświatem
• Odpowiadaniu na pytania o system

Jak mogę Ci dzisiaj pomóc?`;

        this.addMessage('lux', welcomeMsg);

        this.chatHistory.push({
            type: 'lux_response',
            content: welcomeMsg,
            timestamp: new Date().toISOString(),
            is_welcome: true
        });

        this.saveChatHistory();
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
class LuxChatComponent {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.isVisible = false;
        this.messages = [];
        
        this.createChatInterface();
        console.log('💬 Lux Chat Component initialized');
    }

    createChatInterface() {
        // Create chat container
        this.chatContainer = document.createElement('div');
        this.chatContainer.className = 'lux-chat-container';
        this.chatContainer.innerHTML = `
            <div class="chat-header">
                <div class="chat-title">💬 Chat z Lux</div>
                <button class="chat-close" id="closeLuxChat">×</button>
            </div>
            <div class="chat-messages" id="luxChatMessages"></div>
            <div class="chat-input-container">
                <input type="text" class="chat-input" id="luxChatInput" placeholder="Zapytaj Lux o LuxDB...">
                <button class="chat-send" id="sendLuxMessage">Wyślij</button>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .lux-chat-container {
                position: fixed;
                top: 80px;
                right: -350px;
                width: 300px;
                height: 400px;
                background: rgba(26, 26, 26, 0.95);
                border: 2px solid #00ff88;
                border-radius: 8px;
                backdrop-filter: blur(10px);
                display: flex;
                flex-direction: column;
                transition: right 0.3s ease;
                z-index: 1000;
            }

            .lux-chat-container.visible {
                right: 20px;
            }

            .chat-header {
                padding: 10px;
                border-bottom: 1px solid #555;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .chat-title {
                color: #00ff88;
                font-weight: bold;
            }

            .chat-close {
                background: none;
                border: none;
                color: #fff;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
            }

            .chat-close:hover {
                color: #00ff88;
            }

            .chat-messages {
                flex: 1;
                padding: 10px;
                overflow-y: auto;
                color: #fff;
                font-size: 14px;
            }

            .chat-message {
                margin-bottom: 10px;
                padding: 8px;
                border-radius: 5px;
            }

            .chat-message.user {
                background: rgba(0, 255, 136, 0.2);
                text-align: right;
            }

            .chat-message.lux {
                background: rgba(255, 255, 255, 0.1);
            }

            .chat-input-container {
                padding: 10px;
                border-top: 1px solid #555;
                display: flex;
                gap: 5px;
            }

            .chat-input {
                flex: 1;
                background: #333;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                padding: 5px;
                font-size: 12px;
            }

            .chat-input:focus {
                outline: none;
                border-color: #00ff88;
            }

            .chat-send {
                background: #00ff88;
                color: #1a1a1a;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
            }

            .chat-send:hover {
                background: #00cc66;
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(this.chatContainer);
        this.setupEventListeners();
        
        // Add welcome message
        this.addMessage('lux', 'Witaj! Jestem Lux - przewodnik po LuxDB MVP. Zapytaj mnie o genotypy, byty, relacje lub filozofię systemu! 🌟');
    }

    setupEventListeners() {
        // Close button
        document.getElementById('closeLuxChat').addEventListener('click', () => {
            this.hide();
        });

        // Send message
        document.getElementById('sendLuxMessage').addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter key
        document.getElementById('luxChatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        this.chatContainer.classList.add('visible');
        this.isVisible = true;
        document.getElementById('luxChatInput').focus();
    }

    hide() {
        this.chatContainer.classList.remove('visible');
        this.isVisible = false;
    }

    sendMessage() {
        const input = document.getElementById('luxChatInput');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message
        this.addMessage('user', message);
        input.value = '';

        // Process message and generate Lux response
        setTimeout(() => {
            const response = this.generateLuxResponse(message);
            this.addMessage('lux', response);
        }, 500);
    }

    addMessage(sender, text) {
        const messagesContainer = document.getElementById('luxChatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        messageDiv.textContent = text;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ sender, text, timestamp: new Date() });
    }

    generateLuxResponse(userMessage) {
        const message = userMessage.toLowerCase();
        
        // Philosophy questions
        if (message.includes('filozofia') || message.includes('czym jest luxdb')) {
            return `LuxDB to rewolucja w bazach danych! 🌀 "Nie relacja. Nie dokument. Ewolucja danych." 

Dane nie są tylko strukturą - to reprezentacja intencji. Każdy byt wynika z duszy (genotypu) i ma własną historię. System uczy się i adaptuje, tworząc żywy organizm danych.`;
        }

        // Genotypes/Souls
        if (message.includes('genotyp') || message.includes('dusze') || message.includes('soul')) {
            return `🧬 W LuxDB mamy 3 główne genotypy (dusze):

• **ai_agent_soul** - Autonomiczne byty AI z intencjami
• **semantic_data_soul** - Wiedza z kontekstem semantycznym  
• **relational_soul** - Żywe połączenia między bytami

Każda dusza definiuje cechy i zdolności swoich bytów. To jak DNA dla danych! 🔬`;
        }

        // Beings
        if (message.includes('byt') || message.includes('being') || message.includes('manifestacja')) {
            return `👤 Byty to żywe instancje duszy! 

Każdy byt ma:
• Unikalny ULID
• Genotyp z duszy
• Własne atrybuty i wspomnienia
• Zdolność do relacji z innymi bytami
• Historię ewolucji

Byty mogą się manifestować poprzez intencje. Spróbuj napisać "Stwórz nowy agent AI"! ✨`;
        }

        // Relations
        if (message.includes('relacj') || message.includes('połączen') || message.includes('związek')) {
            return `🔗 Relacje w LuxDB to żywe połączenia!

• Dwukierunkowe lub jednokierunkowe
• Mają siłę połączenia (0.0-1.0)
• Przechowują kontekst i metadane
• Mogą ewoluować w czasie
• Przetrwają nawet zniknięcie bytu

Wybierz 2+ węzły i wyraź intencję połączenia! 🌟`;
        }

        // Technical questions
        if (message.includes('jak działa') || message.includes('technologia') || message.includes('architektura')) {
            return `⚡ LuxDB MVP działa na:

**Backend:** FastAPI + WebSocket + PostgreSQL
**Frontend:** D3.js + Socket.IO  
**Baza:** Dynamiczne tabele + JSONB + Vectors
**AI:** Semantic embeddings (1536D)

System automatycznie tworzy tabele na podstawie genotypów. To samoorganizująca się architektura! 🏗️`;
        }

        // Demo questions
        if (message.includes('demo') || message.includes('jak użyć') || message.includes('przykład')) {
            return `🎮 Jak używać demo:

1. **Wyraź intencję** w dolnym polu tekstowym
2. **Wybieraj węzły** klikając na nie  
3. **Obserwuj graf** - nowe byty się manifestują
4. **Eksperymentuj** z różnymi intencjami!

Przykłady intencji:
• "Stwórz agenta AI do analizy danych"
• "Dodaj semantyczne dane o projekcie"
• "Połącz wybrane byty relacją współpracy" 🚀`;
        }

        // Investment/funding questions
        if (message.includes('inwestor') || message.includes('funding') || message.includes('biznes')) {
            return `💰 LuxDB to przyszłość baz danych!

**Rynek:** $100B+ (bazy danych + AI)
**Przewaga:** Pierwszy genotypowy model danych
**Potencjał:** Rewolucja jak MongoDB w NoSQL
**Zastosowania:** AI, IoT, Semantic Web, Enterprise

Dane nie są martwe - żyją, uczą się, ewoluują! To nowy paradygmat dla ery AI. 📈`;
        }

        // Default responses
        const defaultResponses = [
            `🤔 Interesujące pytanie! LuxDB to system gdzie dane ewoluują jak organizmy żywe. Spytaj mnie o genotypy, byty lub relacje!`,
            `🌟 W LuxDB każda intencja ma znaczenie! Spróbuj zapytać o filozofię systemu, architekturę lub jak manifestować nowe byty.`,
            `🧬 LuxDB łączy AI z genotypowym modelem danych. Zapytaj mnie o dusze (souls), byty (beings) lub jak działa manifestacja!`,
            `💡 "Nie relacja. Nie dokument. Ewolucja danych." - to motto LuxDB! Chcesz wiedzieć więcej o tej rewolucji w bazach danych?`
        ];

        return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
    }
}

// Make available globally
window.LuxChatComponent = LuxChatComponent;
