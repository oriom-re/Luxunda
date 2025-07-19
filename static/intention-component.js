
class IntentionComponent {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.intentionInput = document.getElementById('intentionInput');
        this.intentionCounter = document.getElementById('charCounter');
        this.sendButton = document.getElementById('sendIntention');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initCharacterCounter();
        this.enableEmoticonSupport();
        this.setupKeyboardShortcuts();
    }

    setupEventListeners() {
        // Obsługa licznika znaków w intencji
        this.intentionInput.addEventListener('input', () => {
            this.updateCharacterCounter();
            this.autoResizeTextarea();
            this.processEmoticons();
        });

        // Obsługa przycisków
        this.sendButton.addEventListener('click', () => {
            this.sendIntention();
        });

        // Auto-resize textarea
        this.intentionInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });
    }

    setupKeyboardShortcuts() {
        // Obsługa Enter w textarea
        this.intentionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendIntention();
            }
            
            // Ctrl+Enter również wysyła intencję
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.sendIntention();
            }
        });
    }

    initCharacterCounter() {
        this.updateCharacterCounter();
    }

    updateCharacterCounter() {
        const length = this.intentionInput.value.length;
        const maxLength = 500;
        
        this.intentionCounter.textContent = length;

        // Zmiana kolorów w zależności od długości
        if (length > 450) {
            this.intentionCounter.style.color = '#ff4444';
        } else if (length > 350) {
            this.intentionCounter.style.color = '#ffff44';
        } else {
            this.intentionCounter.style.color = '#888';
        }

        // Wyłączanie przycisku gdy za długo lub puste
        this.sendButton.disabled = length === 0 || length > maxLength;
    }

    autoResizeTextarea() {
        this.intentionInput.style.height = 'auto';
        const newHeight = Math.min(Math.max(this.intentionInput.scrollHeight, 40), 200);
        this.intentionInput.style.height = newHeight + 'px';
    }

    enableEmoticonSupport() {
        this.emoticonMap = {
            ':D': '😃',
            ':)': '😊',
            ':(': '😞',
            ':P': '😛',
            ';)': '😉',
            ':o': '😮',
            ':O': '😲',
            ':|': '😐',
            ':/': '😕',
            '<3': '❤️',
            '</3': '💔',
            ':*': '😘',
            '^^': '😊',
            '>:(': '😠',
            ':@': '😡'
        };
    }

    processEmoticons() {
        const cursorPos = this.intentionInput.selectionStart;
        let text = this.intentionInput.value;
        let replaced = false;

        for (const [emoticon, emoji] of Object.entries(this.emoticonMap)) {
            if (text.includes(emoticon)) {
                text = text.replaceAll(emoticon, emoji);
                replaced = true;
            }
        }

        if (replaced) {
            this.intentionInput.value = text;
            this.intentionInput.setSelectionRange(cursorPos, cursorPos);
        }
    }

    sendIntention() {
        const intention = this.intentionInput.value.trim();
        
        if (!intention) {
            this.showValidationError('Wprowadź treść intencji');
            return;
        }

        if (intention.length > 500) {
            this.showValidationError('Intencja jest za długa (max 500 znaków)');
            return;
        }

        // Wyślij intencję przez graph manager
        this.graphManager.processIntention(intention);
        
        // Wyczyść formularz
        this.clearForm();
        
        // Pokaż feedback
        this.showSuccessFeedback('Intencja wysłana! 🚀');
    }

    clearForm() {
        this.intentionInput.value = '';
        this.intentionInput.style.height = '40px';
        this.intentionCounter.textContent = '0';
        this.intentionCounter.style.color = '#888';
        this.sendButton.disabled = true;
    }

    showValidationError(message) {
        this.showFeedback(message, 'error');
    }

    showSuccessFeedback(message) {
        this.showFeedback(message, 'success');
    }

    showFeedback(message, type = 'success') {
        // Usuń poprzednie powiadomienie
        const existing = document.querySelector('.intention-feedback');
        if (existing) {
            existing.remove();
        }

        // Utwórz nowe powiadomienie
        const feedback = document.createElement('div');
        feedback.className = `intention-feedback ${type}`;
        feedback.textContent = message;
        
        // Style dla powiadomienia
        feedback.style.position = 'fixed';
        feedback.style.top = '80px';
        feedback.style.right = '20px';
        feedback.style.padding = '12px 18px';
        feedback.style.borderRadius = '8px';
        feedback.style.zIndex = '1001';
        feedback.style.fontSize = '14px';
        feedback.style.fontWeight = 'bold';
        feedback.style.transform = 'translateX(100%)';
        feedback.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
        feedback.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
        
        if (type === 'error') {
            feedback.style.background = '#ff4444';
            feedback.style.color = 'white';
        } else {
            feedback.style.background = '#00ff88';
            feedback.style.color = '#1a1a1a';
        }

        document.body.appendChild(feedback);

        // Animacja pojawienia się
        setTimeout(() => {
            feedback.style.transform = 'translateX(0)';
        }, 10);

        // Automatyczne usunięcie po 3 sekundach
        setTimeout(() => {
            feedback.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.remove();
                }
            }, 300);
        }, 3000);
    }

    // Publiczne metody dla zewnętrznych komponentów
    focusInput() {
        this.intentionInput.focus();
    }

    setIntention(text) {
        this.intentionInput.value = text;
        this.updateCharacterCounter();
        this.autoResizeTextarea();
    }

    getIntention() {
        return this.intentionInput.value;
    }

    isEnabled() {
        return !this.sendButton.disabled;
    }
}
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
