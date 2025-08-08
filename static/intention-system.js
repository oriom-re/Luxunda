
class IntentionAnalysisSystem {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.intentionTypes = [
            'question', 'idea', 'feedback', 'solution', 'problem', 
            'support', 'innovation', 'connection', 'inspiration'
        ];
        this.activeConnections = new Map();
        this.messageBeings = new Map();
        
        this.setupUI();
        this.setupSocketHandlers();
    }
    
    setupUI() {
        const container = document.createElement('div');
        container.id = 'intention-system';
        container.className = 'intention-system-container';
        container.innerHTML = `
            <div class="intention-header">
                <h3>🧠 System Analizy Intencji</h3>
                <div class="intention-stats">
                    <span id="message-beings-count">0 bytów-wiadomości</span>
                    <span id="connections-found">0 połączeń</span>
                </div>
            </div>
            
            <div class="message-input-section">
                <div class="input-group">
                    <textarea id="message-input" 
                             placeholder="Napisz swoją wiadomość z intencją..." 
                             rows="3"></textarea>
                    <button id="send-message-btn">📤 Wyślij</button>
                </div>
                
                <div class="intention-preview" id="intention-preview" style="display:none;">
                    <div class="detected-intention">
                        <strong>Wykryta intencja:</strong> <span id="intention-type"></span>
                        <div class="confidence">Pewność: <span id="intention-confidence"></span>%</div>
                    </div>
                    <div class="potential-connections" id="potential-connections">
                        <strong>Potencjalne połączenia:</strong>
                        <div id="connections-list"></div>
                    </div>
                </div>
            </div>
            
            <div class="active-messages" id="active-messages">
                <h4>🔗 Aktywne byty-wiadomości</h4>
                <div id="messages-list"></div>
            </div>
            
            <div class="connection-suggestions" id="connection-suggestions">
                <h4>💡 Sugerowane połączenia</h4>
                <div id="suggestions-list"></div>
            </div>
        `;
        
        document.body.appendChild(container);
        this.bindEvents();
    }
    
    bindEvents() {
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-message-btn');
        
        messageInput.addEventListener('input', (e) => {
            this.analyzeInputIntention(e.target.value);
        });
        
        sendBtn.addEventListener('click', () => {
            this.sendMessageBeing();
        });
        
        messageInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.sendMessageBeing();
            }
        });
    }
    
    analyzeInputIntention(messageText) {
        if (!messageText.trim()) {
            document.getElementById('intention-preview').style.display = 'none';
            return;
        }
        
        const analysis = this.performIntentionAnalysis(messageText);
        this.showIntentionPreview(analysis);
        
        // Znajdź potencjalne połączenia
        const connections = this.findPotentialConnections(analysis);
        this.showPotentialConnections(connections);
    }
    
    performIntentionAnalysis(text) {
        const lowerText = text.toLowerCase();
        
        // Wzorce intencji
        const patterns = {
            question: /\?|jak|dlaczego|czy|kiedy|gdzie|co to|pomoż/,
            idea: /pomysł|idea|może|co jeśli|innowacja|nowy/,
            feedback: /feedback|opinia|uwaga|sądzę|myślę/,
            solution: /rozwiązanie|sposób|można|zrobimy|naprawię/,
            problem: /problem|błąd|nie działa|issue|bug/,
            support: /wsparcie|pomoc|potrzebuję|proszę/,
            innovation: /innowacja|przełom|rewolucja|nowość/,
            connection: /połącz|razem|wspólnie|integracja/,
            inspiration: /inspiracja|motywacja|wizja|marzenie/
        };
        
        let bestMatch = { type: 'general', confidence: 30 };
        
        for (const [type, pattern] of Object.entries(patterns)) {
            if (pattern.test(lowerText)) {
                const matches = lowerText.match(pattern);
                const confidence = Math.min(95, 60 + (matches.length * 15));
                if (confidence > bestMatch.confidence) {
                    bestMatch = { type, confidence };
                }
            }
        }
        
        return {
            type: bestMatch.type,
            confidence: bestMatch.confidence,
            keywords: this.extractKeywords(text),
            sentiment: this.analyzeSentiment(text),
            text: text
        };
    }
    
    extractKeywords(text) {
        const stopWords = ['i', 'a', 'w', 'na', 'z', 'do', 'się', 'że', 'to', 'jest', 'by', 'być'];
        const words = text.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 2 && !stopWords.includes(word));
        
        // Zlicz częstotliwość
        const freq = {};
        words.forEach(word => freq[word] = (freq[word] || 0) + 1);
        
        // Zwróć najczęstsze
        return Object.entries(freq)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5)
            .map(([word]) => word);
    }
    
    analyzeSentiment(text) {
        const positiveWords = ['dobry', 'świetny', 'genialny', 'super', 'awesome', 'love', 'like'];
        const negativeWords = ['zły', 'problem', 'błąd', 'nie', 'hate', 'bad', 'wrong'];
        
        const lowerText = text.toLowerCase();
        const positive = positiveWords.reduce((count, word) => 
            count + (lowerText.includes(word) ? 1 : 0), 0);
        const negative = negativeWords.reduce((count, word) => 
            count + (lowerText.includes(word) ? 1 : 0), 0);
        
        if (positive > negative) return 'positive';
        if (negative > positive) return 'negative';
        return 'neutral';
    }
    
    showIntentionPreview(analysis) {
        const preview = document.getElementById('intention-preview');
        const typeSpan = document.getElementById('intention-type');
        const confidenceSpan = document.getElementById('intention-confidence');
        
        typeSpan.textContent = this.getIntentionLabel(analysis.type);
        typeSpan.className = `intention-${analysis.type}`;
        confidenceSpan.textContent = analysis.confidence;
        
        preview.style.display = 'block';
    }
    
    getIntentionLabel(type) {
        const labels = {
            question: '❓ Pytanie',
            idea: '💡 Pomysł',
            feedback: '📝 Feedback',
            solution: '🔧 Rozwiązanie',
            problem: '⚠️ Problem',
            support: '🤝 Wsparcie',
            innovation: '🚀 Innowacja',
            connection: '🔗 Połączenie',
            inspiration: '✨ Inspiracja',
            general: '💬 Ogólne'
        };
        return labels[type] || labels.general;
    }
    
    findPotentialConnections(analysis) {
        const connections = [];
        const currentKeywords = new Set(analysis.keywords);
        
        for (const [beingId, being] of this.messageBeings) {
            const commonKeywords = being.keywords.filter(k => currentKeywords.has(k));
            const keywordMatch = commonKeywords.length / Math.max(currentKeywords.size, being.keywords.length);
            
            const intentionMatch = analysis.type === being.intention.type ? 0.3 : 0;
            const sentimentMatch = analysis.sentiment === being.sentiment ? 0.2 : 0;
            
            const totalScore = (keywordMatch * 0.5) + intentionMatch + sentimentMatch;
            
            if (totalScore > 0.3) {
                connections.push({
                    beingId,
                    being,
                    score: totalScore,
                    commonKeywords,
                    reason: this.getConnectionReason(analysis, being)
                });
            }
        }
        
        return connections.sort((a, b) => b.score - a.score).slice(0, 3);
    }
    
    getConnectionReason(analysis1, analysis2) {
        if (analysis1.type === analysis2.intention.type) {
            return `Podobna intencja: ${this.getIntentionLabel(analysis1.type)}`;
        }
        
        // Komplementarne intencje
        const complementary = {
            'question': ['solution', 'support'],
            'problem': ['solution', 'support'],
            'idea': ['feedback', 'innovation'],
            'support': ['problem', 'question']
        };
        
        if (complementary[analysis1.type]?.includes(analysis2.intention.type)) {
            return `Komplementarne intencje: ${this.getIntentionLabel(analysis1.type)} ↔ ${this.getIntentionLabel(analysis2.intention.type)}`;
        }
        
        return 'Podobne słowa kluczowe';
    }
    
    showPotentialConnections(connections) {
        const connectionsList = document.getElementById('connections-list');
        
        if (connections.length === 0) {
            connectionsList.innerHTML = '<em>Brak potencjalnych połączeń</em>';
            return;
        }
        
        connectionsList.innerHTML = connections.map(conn => `
            <div class="potential-connection">
                <div class="connection-score">${Math.round(conn.score * 100)}%</div>
                <div class="connection-info">
                    <div class="connection-text">${conn.being.text.substring(0, 50)}...</div>
                    <div class="connection-reason">${conn.reason}</div>
                </div>
            </div>
        `).join('');
    }
    
    async sendMessageBeing() {
        const input = document.getElementById('message-input');
        const messageText = input.value.trim();
        
        if (!messageText) return;
        
        const analysis = this.performIntentionAnalysis(messageText);
        
        // Utwórz byt-wiadomość
        const messageBeing = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            text: messageText,
            intention: analysis,
            keywords: analysis.keywords,
            sentiment: analysis.sentiment,
            timestamp: new Date(),
            author: 'user',
            connections: []
        };
        
        // Dodaj do systemu
        this.messageBeings.set(messageBeing.id, messageBeing);
        
        // Znajdź i utwórz połączenia
        const connections = this.findPotentialConnections(analysis);
        await this.createConnections(messageBeing, connections);
        
        // Wyślij do serwera
        if (this.graphManager?.socket) {
            this.graphManager.socket.emit('message_being_created', {
                being: messageBeing,
                connections: connections
            });
        }
        
        // Aktualizuj UI
        this.updateMessagesDisplay();
        this.updateConnectionSuggestions();
        this.updateStats();
        
        // Wyczyść input
        input.value = '';
        document.getElementById('intention-preview').style.display = 'none';
        
        // Pokaż sukces
        this.showNotification(`✅ Utworzono byt-wiadomość z ${connections.length} połączeniami!`);
    }
    
    async createConnections(messageBeing, potentialConnections) {
        for (const conn of potentialConnections) {
            const connectionId = `conn_${messageBeing.id}_${conn.beingId}`;
            
            // Dodaj połączenie do obu bytów
            messageBeing.connections.push({
                id: connectionId,
                targetId: conn.beingId,
                type: 'semantic',
                strength: conn.score,
                reason: conn.reason,
                keywords: conn.commonKeywords
            });
            
            conn.being.connections.push({
                id: connectionId,
                targetId: messageBeing.id,
                type: 'semantic', 
                strength: conn.score,
                reason: conn.reason,
                keywords: conn.commonKeywords
            });
            
            this.activeConnections.set(connectionId, {
                sourceId: messageBeing.id,
                targetId: conn.beingId,
                strength: conn.score,
                reason: conn.reason
            });
        }
    }
    
    updateMessagesDisplay() {
        const messagesList = document.getElementById('messages-list');
        const recentMessages = Array.from(this.messageBeings.values())
            .sort((a, b) => b.timestamp - a.timestamp)
            .slice(0, 10);
        
        messagesList.innerHTML = recentMessages.map(msg => `
            <div class="message-being" data-id="${msg.id}">
                <div class="message-header">
                    <span class="intention-badge intention-${msg.intention.type}">
                        ${this.getIntentionLabel(msg.intention.type)}
                    </span>
                    <span class="message-time">${this.formatTime(msg.timestamp)}</span>
                </div>
                <div class="message-text">${msg.text}</div>
                <div class="message-stats">
                    <span class="connections-count">${msg.connections.length} połączeń</span>
                    <span class="keywords">${msg.keywords.join(', ')}</span>
                </div>
            </div>
        `).join('');
    }
    
    updateConnectionSuggestions() {
        const suggestionsList = document.getElementById('suggestions-list');
        const suggestions = this.generateConnectionSuggestions();
        
        suggestionsList.innerHTML = suggestions.map(sugg => `
            <div class="connection-suggestion">
                <div class="suggestion-strength">${Math.round(sugg.strength * 100)}%</div>
                <div class="suggestion-content">
                    <div class="suggestion-pair">
                        "${sugg.message1.text.substring(0, 30)}..." 
                        ↔ 
                        "${sugg.message2.text.substring(0, 30)}..."
                    </div>
                    <div class="suggestion-reason">${sugg.reason}</div>
                </div>
                <button class="accept-suggestion" onclick="intentionSystem.acceptSuggestion('${sugg.id}')">
                    ✅ Połącz
                </button>
            </div>
        `).join('');
    }
    
    generateConnectionSuggestions() {
        const suggestions = [];
        const messages = Array.from(this.messageBeings.values());
        
        for (let i = 0; i < messages.length; i++) {
            for (let j = i + 1; j < messages.length; j++) {
                const msg1 = messages[i];
                const msg2 = messages[j];
                
                // Sprawdź czy już są połączone
                if (msg1.connections.some(c => c.targetId === msg2.id)) continue;
                
                const analysis1 = { type: msg1.intention.type, keywords: msg1.keywords, sentiment: msg1.sentiment };
                const analysis2 = { type: msg2.intention.type, keywords: msg2.keywords, sentiment: msg2.sentiment };
                
                const connections = this.findPotentialConnections(analysis1);
                const relevant = connections.find(c => c.beingId === msg2.id);
                
                if (relevant && relevant.score > 0.4) {
                    suggestions.push({
                        id: `sugg_${msg1.id}_${msg2.id}`,
                        message1: msg1,
                        message2: msg2,
                        strength: relevant.score,
                        reason: relevant.reason
                    });
                }
            }
        }
        
        return suggestions.sort((a, b) => b.strength - a.strength).slice(0, 5);
    }
    
    updateStats() {
        document.getElementById('message-beings-count').textContent = 
            `${this.messageBeings.size} bytów-wiadomości`;
        document.getElementById('connections-found').textContent = 
            `${this.activeConnections.size} połączeń`;
    }
    
    formatTime(timestamp) {
        return timestamp.toLocaleTimeString('pl-PL', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'intention-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }
    
    setupSocketHandlers() {
        if (this.graphManager?.socket) {
            this.graphManager.socket.on('message_being_response', (data) => {
                console.log('Server processed message being:', data);
            });
            
            this.graphManager.socket.on('new_connection_discovered', (data) => {
                console.log('Server discovered new connection:', data);
                this.showNotification(`🔗 Nowe połączenie: ${data.reason}`);
            });
        }
    }
    
    acceptSuggestion(suggestionId) {
        const [, sourceId, targetId] = suggestionId.split('_');
        const source = this.messageBeings.get(sourceId);
        const target = this.messageBeings.get(targetId);
        
        if (source && target) {
            this.createConnections(source, [{
                beingId: targetId,
                being: target,
                score: 0.8,
                reason: 'Zaakceptowane przez użytkownika'
            }]);
            
            this.updateConnectionSuggestions();
            this.updateStats();
            this.showNotification('✅ Połączenie utworzone!');
        }
    }
}

// Style CSS
const intentionStyles = `
<style>
.intention-system-container {
    position: fixed;
    right: 20px;
    top: 80px;
    width: 400px;
    max-height: 80vh;
    overflow-y: auto;
    background: rgba(0, 0, 0, 0.9);
    border: 1px solid #333;
    border-radius: 10px;
    color: white;
    font-family: 'Courier New', monospace;
    z-index: 1000;
    padding: 15px;
}

.intention-header {
    border-bottom: 1px solid #333;
    padding-bottom: 10px;
    margin-bottom: 15px;
}

.intention-header h3 {
    margin: 0 0 10px 0;
    color: #00ff88;
}

.intention-stats {
    display: flex;
    gap: 15px;
    font-size: 12px;
    color: #999;
}

.message-input-section {
    margin-bottom: 20px;
}

.input-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

#message-input {
    background: #111;
    border: 1px solid #333;
    border-radius: 5px;
    padding: 10px;
    color: white;
    resize: vertical;
    font-family: inherit;
}

#send-message-btn {
    background: #00ff88;
    color: black;
    border: none;
    padding: 10px;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
}

#send-message-btn:hover {
    background: #00cc66;
}

.intention-preview {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 5px;
    padding: 10px;
    margin-top: 10px;
}

.detected-intention {
    margin-bottom: 10px;
}

.intention-badge {
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: bold;
}

.intention-question { background: #ff6b6b; }
.intention-idea { background: #ffd93d; color: black; }
.intention-feedback { background: #6bcf7f; color: black; }
.intention-solution { background: #4ecdc4; color: black; }
.intention-problem { background: #ff6b6b; }
.intention-support { background: #a8e6cf; color: black; }
.intention-innovation { background: #ff8b94; }
.intention-connection { background: #88d8c0; color: black; }
.intention-inspiration { background: #ffd93d; color: black; }
.intention-general { background: #666; }

.potential-connection {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px;
    border: 1px solid #333;
    border-radius: 3px;
    margin: 5px 0;
}

.connection-score {
    background: #00ff88;
    color: black;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: bold;
}

.message-being {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 5px;
    padding: 10px;
    margin: 5px 0;
}

.message-header {
    display: flex;
    justify-content: between;
    align-items: center;
    margin-bottom: 5px;
}

.message-text {
    margin: 5px 0;
    line-height: 1.4;
}

.message-stats {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #999;
    margin-top: 5px;
}

.connection-suggestion {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px;
    border: 1px solid #333;
    border-radius: 5px;
    margin: 5px 0;
}

.accept-suggestion {
    background: #00ff88;
    color: black;
    border: none;
    padding: 4px 8px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 10px;
}

.intention-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #00ff88;
    color: black;
    padding: 10px 15px;
    border-radius: 5px;
    font-weight: bold;
    z-index: 2000;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}
</style>
`;

// Dodaj style do dokumentu
document.head.insertAdjacentHTML('beforeend', intentionStyles);

// Globalna instancja
window.IntentionAnalysisSystem = IntentionAnalysisSystem;

console.log('✅ System Analizy Intencji loaded');
