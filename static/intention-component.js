// ===== INTENTION COMPONENT - CZYSTA IMPLEMENTACJA =====

class IntentionComponent {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.isVisible = true;
        this.currentIntention = '';

        this.initializeComponent();
        console.log('💫 Intention Component initialized');
    }

    initializeComponent() {
        this.intentionInput = document.getElementById('intentionInput');
        this.sendButton = document.getElementById('sendIntention');
        this.charCounter = document.getElementById('charCounter');

        if (!this.intentionInput || !this.sendButton) {
            console.error('Intention component elements not found');
            return;
        }

        this.setupEventListeners();
        this.setupResponseHandler();
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => {
            this.sendIntention();
        });

        this.intentionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendIntention();
            }
        });

        this.intentionInput.addEventListener('input', () => {
            this.updateCharCounter();
            this.autoResize();
        });
    }

    sendIntention() {
        const intention = this.intentionInput.value.trim();
        if (!intention) return;

        console.log('Wysyłanie intencji:', intention);

        if (this.graphManager && this.graphManager.socket) {
            this.graphManager.socket.emit('send_intention', {
                intention: intention,
                timestamp: new Date().toISOString()
            });
        }

        this.intentionInput.value = '';
        this.updateCharCounter();
        this.autoResize();
        this.showFeedback('Intencja wysłana do uniwersum...');
    }

    updateCharCounter() {
        const currentLength = this.intentionInput.value.length;
        if (this.charCounter) {
            this.charCounter.textContent = currentLength;
        }
    }

    autoResize() {
        this.intentionInput.style.height = 'auto';
        const scrollHeight = this.intentionInput.scrollHeight;
        const minHeight = 40;
        const maxHeight = 200;
        const newHeight = Math.max(minHeight, Math.min(maxHeight, scrollHeight));
        this.intentionInput.style.height = newHeight + 'px';
    }

    showFeedback(message, isSuccess = true) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-message';
        feedbackDiv.textContent = message;
        feedbackDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${isSuccess ? '#00ff88' : '#ff6b6b'};
            color: #1a1a1a;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 2000;
            max-width: 300px;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;

        document.body.appendChild(feedbackDiv);

        setTimeout(() => {
            if (feedbackDiv.parentNode) {
                feedbackDiv.parentNode.removeChild(feedbackDiv);
            }
        }, 4000);
    }

    setupResponseHandler() {
        if (this.graphManager && this.graphManager.socket) {
            this.graphManager.socket.on('intention_response', (response) => {
                console.log('📥 Intention response received:', response);
                
                if (response.status === 'processed') {
                    const analysis = response.analysis;
                    let message = `🎯 Intent: ${analysis.intent}`;
                    if (analysis.new_being_created) {
                        message += `\n✨ Created: ${analysis.being_name}`;
                    }
                    this.showFeedback(message, true);
                } else if (response.status === 'error') {
                    this.showFeedback(`❌ Error: ${response.error}`, false);
                } else {
                    this.showFeedback('📤 Intention sent!', true);
                }
            });
        }
    }
}

console.log('✅ IntentionComponent loaded');
window.IntentionComponent = IntentionComponent;
// Intention Component for LuxDB
class IntentionComponent {
    constructor() {
        this.initialized = false;
        console.log('🎯 Intention Component initialized');
    }

    init() {
        this.initialized = true;
        console.log('✅ Intention Component ready');
    }

    showIntention(message) {
        console.log('💭 Intention:', message);
    }
}

// Global instance
window.intentionComponent = new IntentionComponent();
