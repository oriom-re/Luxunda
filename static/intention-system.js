
// 🔥 REWOLUCYJNY SYSTEM INTENCJI LuxOS
class RevolutionaryIntentionSystem {
    constructor() {
        this.socket = io();
        this.intentions = new Map();
        this.connections = new Map();
        this.inspirations = [];
        
        this.setupUI();
        this.setupSocketListeners();
    }

    setupUI() {
        const container = document.getElementById('intention-container');
        container.innerHTML = `
            <div class="revolutionary-header">
                <h1>🧬 LuxOS: System Żywych Intencji</h1>
                <p>Gdzie myśli stają się rzeczywistością</p>
            </div>
            
            <div class="intention-input-zone">
                <textarea id="user-intention" 
                         placeholder="Opisz swoją intencję... (np. 'Chcę system który automatycznie łączy podobne projekty')"
                         rows="3"></textarea>
                <button id="submit-intention" class="quantum-btn">
                    🚀 Aktywuj Intencję
                </button>
            </div>
            
            <div class="live-system-state">
                <div class="intention-stream" id="intention-stream">
                    <h3>🌊 Strumień Świadomości</h3>
                </div>
                <div class="connection-web" id="connection-web">
                    <h3>🕸️ Sieć Połączeń</h3>
                </div>
                <div class="inspiration-feed" id="inspiration-feed">
                    <h3>💡 Żywe Inspiracje</h3>
                </div>
            </div>
        `;

        // Event listeners
        document.getElementById('submit-intention').addEventListener('click', () => {
            this.processUserIntention();
        });

        document.getElementById('user-intention').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.processUserIntention();
            }
        });
    }

    processUserIntention() {
        const textarea = document.getElementById('user-intention');
        const intentionText = textarea.value.trim();
        
        if (!intentionText) return;

        const intention = {
            id: this.generateId(),
            text: intentionText,
            timestamp: new Date(),
            type: this.classifyIntention(intentionText),
            energy: Math.random() * 100,
            connections: []
        };

        this.intentions.set(intention.id, intention);
        
        // Wyślij do systemu AI
        this.socket.emit('process_intention', {
            intention: intention,
            context: Array.from(this.intentions.values())
        });

        this.visualizeIntention(intention);
        this.findConnections(intention);
        
        textarea.value = '';
        this.animateSubmission();
    }

    classifyIntention(text) {
        const lower = text.toLowerCase();
        
        if (lower.includes('połącz') || lower.includes('łączy') || lower.includes('relacja')) {
            return 'connection';
        } else if (lower.includes('stwórz') || lower.includes('zbuduj') || lower.includes('utwórz')) {
            return 'creation';
        } else if (lower.includes('analizuj') || lower.includes('sprawdź') || lower.includes('znajdź')) {
            return 'analysis';
        } else if (lower.includes('automatycznie') || lower.includes('auto') || lower.includes('samo')) {
            return 'automation';
        } else if (lower.includes('pomysł') || lower.includes('inspiracja') || lower.includes('idea')) {
            return 'inspiration';
        } else {
            return 'exploration';
        }
    }

    visualizeIntention(intention) {
        const stream = document.getElementById('intention-stream');
        const intentionElement = document.createElement('div');
        intentionElement.className = `intention-item ${intention.type}`;
        
        intentionElement.innerHTML = `
            <div class="intention-header">
                <span class="intention-type">${this.getTypeIcon(intention.type)} ${intention.type}</span>
                <span class="intention-energy">⚡ ${Math.round(intention.energy)}%</span>
            </div>
            <div class="intention-text">${intention.text}</div>
            <div class="intention-status">🔄 Analizowanie wzorców...</div>
            <div class="intention-timestamp">${intention.timestamp.toLocaleTimeString()}</div>
        `;

        stream.insertBefore(intentionElement, stream.firstChild.nextSibling);
        
        // Animacja pojawiania się
        setTimeout(() => {
            intentionElement.classList.add('intention-appear');
        }, 100);
    }

    findConnections(newIntention) {
        const connections = [];
        
        for (const [id, intention] of this.intentions) {
            if (id === newIntention.id) continue;
            
            const similarity = this.calculateSimilarity(newIntention.text, intention.text);
            if (similarity > 0.3) {
                connections.push({
                    target: intention,
                    strength: similarity,
                    type: this.getConnectionType(newIntention.type, intention.type)
                });
            }
        }

        newIntention.connections = connections;
        this.visualizeConnections(newIntention, connections);
        
        if (connections.length > 0) {
            this.generateInspiration(newIntention, connections);
        }
    }

    calculateSimilarity(text1, text2) {
        const words1 = text1.toLowerCase().split(/\s+/);
        const words2 = text2.toLowerCase().split(/\s+/);
        
        const intersection = words1.filter(word => words2.includes(word));
        const union = [...new Set([...words1, ...words2])];
        
        return intersection.length / union.length;
    }

    visualizeConnections(intention, connections) {
        const web = document.getElementById('connection-web');
        
        connections.forEach(connection => {
            const connectionElement = document.createElement('div');
            connectionElement.className = 'connection-item';
            
            connectionElement.innerHTML = `
                <div class="connection-strength">
                    💫 Siła połączenia: ${Math.round(connection.strength * 100)}%
                </div>
                <div class="connection-description">
                    "${intention.text}" ↔️ "${connection.target.text}"
                </div>
                <div class="connection-type">
                    🔗 Typ: ${connection.type}
                </div>
            `;
            
            web.appendChild(connectionElement);
        });
    }

    generateInspiration(intention, connections) {
        const inspiration = {
            id: this.generateId(),
            source: intention,
            connections: connections,
            text: this.createInspirationText(intention, connections),
            timestamp: new Date()
        };

        this.inspirations.push(inspiration);
        this.visualizeInspiration(inspiration);
    }

    createInspirationText(intention, connections) {
        const templates = [
            `Co jeśli połączymy "${intention.text}" z istniejącymi wzorcami? Możemy stworzyć system który...`,
            `Analizując relacje widzę potencjał: ${intention.text} może ewoluować w...`,
            `System odkrył wzorzec! Twoja intencja rezonuje z ${connections.length} innymi myślami...`,
            `🧬 Mutacja genetyczna: Łącząc "${intention.text}" z podobnymi intencjami powstaje nowy organizm...`
        ];

        return templates[Math.floor(Math.random() * templates.length)];
    }

    visualizeInspiration(inspiration) {
        const feed = document.getElementById('inspiration-feed');
        const inspirationElement = document.createElement('div');
        inspirationElement.className = 'inspiration-item';
        
        inspirationElement.innerHTML = `
            <div class="inspiration-header">
                💡 System Generuje Inspirację
            </div>
            <div class="inspiration-text">${inspiration.text}</div>
            <div class="inspiration-connections">
                🔗 Oparte na ${inspiration.connections.length} połączeniach
            </div>
            <div class="inspiration-timestamp">${inspiration.timestamp.toLocaleTimeString()}</div>
        `;

        feed.insertBefore(inspirationElement, feed.firstChild.nextSibling);
        
        // Efekt DNA double helix
        inspirationElement.classList.add('dna-spiral');
    }

    getTypeIcon(type) {
        const icons = {
            'connection': '🔗',
            'creation': '🧬',
            'analysis': '🔍',
            'automation': '🤖',
            'inspiration': '💡',
            'exploration': '🌌'
        };
        return icons[type] || '🧬';
    }

    getConnectionType(type1, type2) {
        if (type1 === type2) return 'Synergia';
        if ((type1 === 'creation' && type2 === 'inspiration') || 
            (type1 === 'inspiration' && type2 === 'creation')) return 'Twórcza Fuzja';
        if ((type1 === 'analysis' && type2 === 'automation') || 
            (type1 === 'automation' && type2 === 'analysis')) return 'Inteligentna Automatyzacja';
        return 'Krzyżowa Ewolucja';
    }

    setupSocketListeners() {
        this.socket.on('intention_processed', (data) => {
            // AI odpowiedziało - zaktualizuj status
            const intention = this.intentions.get(data.intention_id);
            if (intention) {
                this.updateIntentionStatus(intention, data.ai_response);
            }
        });

        this.socket.on('system_evolution', (data) => {
            // System ewoluował na podstawie intencji
            this.showSystemEvolution(data);
        });
    }

    updateIntentionStatus(intention, aiResponse) {
        // Znajdź element w DOM i zaktualizuj status
        const elements = document.querySelectorAll('.intention-item');
        elements.forEach(element => {
            if (element.textContent.includes(intention.text)) {
                const statusElement = element.querySelector('.intention-status');
                statusElement.innerHTML = `✅ ${aiResponse.action || 'Zintegrowano z systemem'}`;
                statusElement.classList.add('status-complete');
            }
        });
    }

    animateSubmission() {
        const button = document.getElementById('submit-intention');
        button.classList.add('quantum-pulse');
        setTimeout(() => {
            button.classList.remove('quantum-pulse');
        }, 1000);
    }

    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

// Style CSS w duchu rewolucji
const style = document.createElement('style');
style.textContent = `
.revolutionary-header {
    text-align: center;
    background: linear-gradient(45deg, #ff00cc, #0099ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 30px;
}

.revolutionary-header h1 {
    font-size: 2.5rem;
    margin: 0;
    text-shadow: 0 0 30px rgba(255, 0, 204, 0.5);
}

.intention-input-zone {
    background: rgba(0, 255, 136, 0.1);
    border: 2px solid rgba(0, 255, 136, 0.3);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 30px;
}

#user-intention {
    width: 100%;
    background: rgba(0, 0, 0, 0.7);
    border: 1px solid rgba(0, 255, 136, 0.5);
    border-radius: 10px;
    padding: 15px;
    color: #00ff88;
    font-size: 16px;
    resize: vertical;
}

.quantum-btn {
    background: linear-gradient(45deg, #00ff88, #0099ff);
    border: none;
    border-radius: 25px;
    padding: 15px 30px;
    color: #000;
    font-weight: bold;
    font-size: 16px;
    cursor: pointer;
    margin-top: 10px;
    transition: all 0.3s ease;
}

.quantum-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(0, 255, 136, 0.6);
}

.quantum-pulse {
    animation: quantum-pulse 1s ease-in-out;
}

@keyframes quantum-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); box-shadow: 0 0 30px rgba(0, 255, 136, 0.8); }
}

.live-system-state {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    margin-top: 30px;
}

.intention-stream, .connection-web, .inspiration-feed {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    max-height: 500px;
    overflow-y: auto;
}

.intention-item {
    background: rgba(0, 255, 136, 0.1);
    border-left: 4px solid #00ff88;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    opacity: 0;
    transform: translateX(-20px);
    transition: all 0.3s ease;
}

.intention-appear {
    opacity: 1;
    transform: translateX(0);
}

.intention-item.creation { border-left-color: #ff00cc; }
.intention-item.analysis { border-left-color: #0099ff; }
.intention-item.automation { border-left-color: #ffaa00; }

.intention-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-size: 14px;
}

.intention-energy {
    color: #ffaa00;
    font-weight: bold;
}

.intention-text {
    color: #ffffff;
    margin-bottom: 10px;
    font-weight: 500;
}

.intention-status {
    color: #00ff88;
    font-size: 12px;
    margin-bottom: 5px;
}

.status-complete {
    color: #00ff88;
    font-weight: bold;
}

.connection-item {
    background: rgba(0, 153, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
    border-left: 3px solid #0099ff;
}

.inspiration-item {
    background: rgba(255, 0, 204, 0.1);
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border-left: 4px solid #ff00cc;
    position: relative;
    overflow: hidden;
}

.dna-spiral::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 0, 204, 0.3), transparent);
    animation: dna-flow 2s linear infinite;
}

@keyframes dna-flow {
    0% { left: -100%; }
    100% { left: 100%; }
}
`;
document.head.appendChild(style);

// Inicjalizacja systemu
document.addEventListener('DOMContentLoaded', () => {
    new RevolutionaryIntentionSystem();
});
