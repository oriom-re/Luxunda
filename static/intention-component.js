
class IntentionComponent {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.intentionInput = document.getElementById('intentionInput');
        this.sendButton = document.getElementById('sendIntention');
        this.charCounter = document.getElementById('charCounter');

        if (!this.intentionInput || !this.sendButton || !this.charCounter) {
            console.error('Intention component elements not found');
            return;
        }

        this.setupEventListeners();
        this.updateCharacterCounter();
        this.autoResizeTextarea();

        console.log('IntentionComponent initialized');
    }

    setupEventListeners() {
        // Input event dla licznika znaków i resize
        this.intentionInput.addEventListener('input', () => {
            this.updateCharacterCounter();
            this.autoResizeTextarea();
            this.processEmoticons();
        });

        // Dodatkowy listener dla paste
        this.intentionInput.addEventListener('paste', () => {
            setTimeout(() => {
                this.updateCharacterCounter();
                this.autoResizeTextarea();
            }, 10);
        });

        // Keydown dla Enter
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

        // Click na przycisk
        this.sendButton.addEventListener('click', () => {
            this.sendIntention();
        });

        // Socket.IO listeners
        if (this.graphManager && this.graphManager.socket) {
            this.graphManager.socket.on('lux_analysis_response', (response) => {
                this.handleLuxAnalysisResponse(response);
            });

            this.graphManager.socket.on('intention_response', (response) => {
                this.handleIntentionResponse(response);
            });

            this.graphManager.socket.on('error', (error) => {
                this.showError('Błąd serwera: ' + error.message);
            });
        }
    }

    updateCharacterCounter() {
        const length = this.intentionInput.value.length;
        const maxLength = 500;
        
        this.charCounter.textContent = length;
        
        // Zmień kolor licznika gdy zbliżamy się do limitu
        if (length > maxLength * 0.9) {
            this.charCounter.style.color = '#ff6b6b';
        } else if (length > maxLength * 0.7) {
            this.charCounter.style.color = '#ffd93d';
        } else {
            this.charCounter.style.color = '#888';
        }

        // Zablokuj przycisk jeśli za długo
        this.sendButton.disabled = length === 0 || length > maxLength;
    }

    autoResizeTextarea() {
        // Reset wysokości żeby zmierzyć scrollHeight
        this.intentionInput.style.height = 'auto';
        
        // Ustaw nową wysokość na podstawie contentu
        const scrollHeight = this.intentionInput.scrollHeight;
        const minHeight = 40;
        const maxHeight = 200;
        
        const newHeight = Math.max(minHeight, Math.min(maxHeight, scrollHeight));
        this.intentionInput.style.height = newHeight + 'px';
    }

    processEmoticons() {
        const text = this.intentionInput.value;
        const emoticons = {
            ':)': '😊',
            ':D': '😃',
            ':(': '😢',
            ':P': '😛',
            ';)': '😉',
            '<3': '❤️',
            ':star:': '⭐',
            ':rocket:': '🚀',
            ':fire:': '🔥',
            ':brain:': '🧠'
        };

        let newText = text;
        for (const [emoticon, emoji] of Object.entries(emoticons)) {
            newText = newText.replace(new RegExp(escapeRegExp(emoticon), 'g'), emoji);
        }

        if (newText !== text) {
            const cursorPos = this.intentionInput.selectionStart;
            this.intentionInput.value = newText;
            this.intentionInput.setSelectionRange(cursorPos, cursorPos);
        }
    }

    sendIntention() {
        const message = this.intentionInput.value.trim();
        
        if (!message) {
            this.showError('Wprowadź myśl przed wysłaniem');
            return;
        }

        if (message.length > 500) {
            this.showError('Wiadomość jest za długa (maksymalnie 500 znaków)');
            return;
        }

        try {
            console.log('Sending thought to Lux:', message);
            
            // Pokaż feedback
            this.showFeedback('Lux analizuje twoją myśl...', 'info');
            
            // Zablokuj przycisk na czas przetwarzania
            this.sendButton.disabled = true;
            this.sendButton.textContent = '🧠 Lux analizuje...';

            // Wyślij przez nowy kanał komunikacyjny z Lux
            if (this.graphManager && this.graphManager.socket) {
                this.graphManager.socket.emit('lux_communication', {
                    message: message,
                    context: {
                        selected_nodes: this.graphManager.selectedNodes || [],
                        timestamp: new Date().toISOString()
                    }
                });
            } else {
                throw new Error('Połączenie z Lux niedostępne');
            }

        } catch (error) {
            console.error('Error sending to Lux:', error);
            this.showError('Błąd komunikacji z Lux: ' + error.message);
            this.resetSendButton();
        }
    }

    handleIntentionResponse(response) {
        console.log('Intention response received:', response);

        // Resetuj przycisk
        this.resetSendButton();

        if (response.message) {
            this.showFeedback(response.message, 'success');
        }

        // Wykonaj akcje jeśli są
        if (response.actions && response.actions.length > 0) {
            response.actions.forEach(action => {
                this.executeAction(action);
            });
        }

        // Wyczyść input po pomyślnym przetworzeniu
        if (response.actions && response.actions.length > 0) {
            this.clearInput();
        }
    }

    executeAction(action) {
        console.log('Executing action:', action);

        switch (action.type) {
            case 'create_being':
                if (this.graphManager && this.graphManager.socket) {
                    this.graphManager.socket.emit('create_being', action.data);
                }
                break;

            case 'create_relationship':
                if (this.graphManager && this.graphManager.socket) {
                    this.graphManager.socket.emit('create_relationship', action.data);
                }
                break;

            case 'update_being':
                if (this.graphManager && this.graphManager.socket) {
                    this.graphManager.socket.emit('update_being', action.data);
                }
                break;

            default:
                console.warn('Unknown action type:', action.type);
        }
    }

    handleLuxAnalysisResponse(response) {
        console.log('Lux analysis response:', response);

        // Resetuj przycisk
        this.resetSendButton();

        // Pokaż odpowiedź Lux
        if (response.lux_response) {
            this.showFeedback(response.lux_response, 'success');
        }

        // Pokaż klasyfikację
        const analysis = response.analysis;
        if (analysis) {
            const classificationText = this.getClassificationText(analysis.classification);
            this.showFeedback(`Lux: ${classificationText}`, 'info');

            // Jeśli są sugerowane akcje, pokaż je
            if (analysis.suggested_actions && analysis.suggested_actions.length > 0) {
                this.showSuggestedActions(analysis.suggested_actions);
            }

            // Jeśli znaleziono podobne intencje
            if (analysis.matching_intentions && analysis.matching_intentions.length > 0) {
                this.showMatchingIntentions(analysis.matching_intentions);
            }
        }

        // Wyczyść input po pomyślnej analizie
        this.clearInput();
    }

    getClassificationText(classification) {
        const classifications = {
            'new_intention': '🌟 Nowa intencja! Umieszczę ją na orbicie.',
            'intention_extension': '🔗 Rozszerzenie istniejącej intencji.',
            'question': '❓ Pytanie - przeszukuję wiedzę...',
            'general_thought': '💭 Myśl dodana do kontekstu.',
            'error': '❌ Błąd analizy.'
        };
        return classifications[classification] || '🤔 Analizuję...';
    }

    showSuggestedActions(actions) {
        // Pokaż sugerowane akcje w interfejsie
        const actionsText = actions.map(action => `${action.icon} ${action.description}`).join('\n');
        this.showFeedback(`Sugerowane akcje:\n${actionsText}`, 'info');
    }

    showMatchingIntentions(intentions) {
        // Pokaż podobne intencje
        const intentionsText = intentions.map((intent, i) => 
            `${i+1}. ${intent.content} (${(intent.similarity * 100).toFixed(0)}% podobieństwa)`
        ).join('\n');
        this.showFeedback(`Znalezione podobne intencje:\n${intentionsText}`, 'info');
    }

    resetSendButton() {
        this.sendButton.disabled = false;
        this.sendButton.textContent = '🧠 Wyślij do Lux';
    }

    showFeedback(message, type = 'info') {
        const feedback = document.createElement('div');
        feedback.className = 'intention-feedback';
        feedback.textContent = message;

        feedback.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            z-index: 10000;
            transform: translateX(100px);
            opacity: 0;
            transition: all 0.3s ease;
        `;

        if (type === 'success') {
            feedback.style.background = '#4CAF50';
        } else if (type === 'error') {
            feedback.style.background = '#f44336';
        } else {
            feedback.style.background = '#2196F3';
        }

        document.body.appendChild(feedback);

        // Animacja wejścia
        setTimeout(() => {
            feedback.style.transform = 'translateX(0)';
            feedback.style.opacity = '1';
        }, 10);

        // Usuń po 3 sekundach
        setTimeout(() => {
            feedback.style.transform = 'translateX(100px)';
            feedback.style.opacity = '0';
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.parentNode.removeChild(feedback);
                }
            }, 300);
        }, 3000);
    }

    showError(message) {
        this.showFeedback(message, 'error');
        this.resetSendButton();
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
    }
}

// Helper function dla regex escape
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Udostępnij globalnie
window.IntentionComponent = IntentionComponent;
