class IntentionComponent {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.intentionInput = document.getElementById('intentionInput');
        this.sendButton = document.getElementById('sendIntention');
        this.charCounter = document.getElementById('charCounter');

        this.setupEventListeners();
        this.updateCharacterCounter();
    }

    setupEventListeners() {
        this.intentionInput.addEventListener('input', () => {
            this.updateCharacterCounter();
            this.autoResizeTextarea();
            this.processEmoticons();
        });

        this.intentionInput.addEventListener('paste', () => {
            this.autoResizeTextarea();
        });

        this.intentionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendIntention();
            }

            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.sendIntention();
            }
        });

        this.sendButton.addEventListener('click', () => {
            this.sendIntention();
        });
    }

    updateCharacterCounter() {
        const currentLength = this.intentionInput.value.length;
        this.charCounter.textContent = currentLength;

        if (currentLength > 400) {
            this.charCounter.style.color = '#ff4444';
        } else if (currentLength > 300) {
            this.charCounter.style.color = '#ffaa00';
        } else {
            this.charCounter.style.color = '#888';
        }

        this.sendButton.disabled = currentLength === 0 || currentLength > 500;
    }

    autoResizeTextarea() {
        this.intentionInput.style.height = 'auto';
        this.intentionInput.style.height = Math.min(this.intentionInput.scrollHeight, 200) + 'px';
    }

    processEmoticons() {
        const value = this.intentionInput.value;
        const emojiMap = {
            ':rocket:': '🚀',
            ':target:': '🎯',
            ':bulb:': '💡',
            ':gear:': '⚙️',
            ':fire:': '🔥',
            ':star:': '⭐',
            ':heart:': '❤️',
            ':check:': '✅'
        };

        let newValue = value;
        for (const [text, emoji] of Object.entries(emojiMap)) {
            newValue = newValue.replace(new RegExp(text, 'g'), emoji);
        }

        if (newValue !== value) {
            const cursorPos = this.intentionInput.selectionStart;
            this.intentionInput.value = newValue;
            this.intentionInput.setSelectionRange(cursorPos, cursorPos);
        }
    }

    sendIntention() {
        const intention = this.intentionInput.value.trim();

        if (!intention) {
            this.showValidationError('Wprowadź treść intencji');
            return;
        }

        this.sendButton.disabled = true;
        this.sendButton.textContent = '⏳ Przetwarzanie...';

        try {
            this.graphManager.processIntention(intention);
            this.intentionInput.value = '';
            this.updateCharacterCounter();
            this.autoResizeTextarea();
        } catch (error) {
            console.error('Error sending intention:', error);
            this.showValidationError('Błąd podczas wysyłania intencji');
        }

        setTimeout(() => {
            this.sendButton.disabled = false;
            this.sendButton.textContent = '🎯 Przetwórz Intencję';
        }, 2000);
    }

    showValidationError(message) {
        this.intentionInput.style.borderColor = '#ff4444';
        this.intentionInput.style.boxShadow = '0 0 10px rgba(255, 68, 68, 0.3)';

        setTimeout(() => {
            this.intentionInput.style.borderColor = '#555';
            this.intentionInput.style.boxShadow = 'none';
        }, 2000);

        const feedback = document.createElement('div');
        feedback.textContent = message;
        feedback.style.position = 'absolute';
        feedback.style.bottom = '130px';
        feedback.style.left = '20px';
        feedback.style.background = '#ff4444';
        feedback.style.color = 'white';
        feedback.style.padding = '8px 12px';
        feedback.style.borderRadius = '4px';
        feedback.style.fontSize = '12px';
        feedback.style.zIndex = '1002';

        document.body.appendChild(feedback);

        setTimeout(() => {
            feedback.remove();
        }, 3000);
    }

    focusInput() {
        this.intentionInput.focus();
    }

    clearInput() {
        this.intentionInput.value = '';
        this.updateCharacterCounter();
        this.autoResizeTextarea();
    }

    setPlaceholder(text) {
        this.intentionInput.placeholder = text;
    }

    insertText(text) {
        const cursorPos = this.intentionInput.selectionStart;
        const currentValue = this.intentionInput.value;
        const newValue = currentValue.slice(0, cursorPos) + text + currentValue.slice(cursorPos);

        this.intentionInput.value = newValue;
        this.intentionInput.setSelectionRange(cursorPos + text.length, cursorPos + text.length);
        this.updateCharacterCounter();
        this.autoResizeTextarea();
        this.intentionInput.focus();
    }
}