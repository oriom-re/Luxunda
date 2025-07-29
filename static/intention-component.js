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

    showFeedback(message) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-message';
        feedbackDiv.textContent = message;
        feedbackDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: #00ff88;
            color: #1a1a1a;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 2000;
            max-width: 300px;
            font-weight: bold;
        `;

        document.body.appendChild(feedbackDiv);

        setTimeout(() => {
            if (feedbackDiv.parentNode) {
                feedbackDiv.parentNode.removeChild(feedbackDiv);
            }
        }, 3000);
    }
}

console.log('✅ IntentionComponent loaded');
window.IntentionComponent = IntentionComponent;