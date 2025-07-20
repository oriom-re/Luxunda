
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
            
            // Pobierz kontekst wizualny
            const visualContext = this.getVisualContext();
            
            // Pokaż feedback z kontekstem
            if (visualContext.focused_beings.length > 0) {
                this.showFeedback(`Lux analizuje w kontekście: ${visualContext.focused_beings.join(', ')}...`, 'info');
            } else {
                this.showFeedback('Lux analizuje twoją myśl...', 'info');
            }
            
            // Zablokuj przycisk na czas przetwarzania
            this.sendButton.disabled = true;
            this.sendButton.textContent = '🧠 Lux analizuje...';

            // Wyślij przez nowy kanał komunikacyjny z Lux z rozszerzonym kontekstem
            if (this.graphManager && this.graphManager.socket) {
                this.graphManager.socket.emit('lux_communication', {
                    message: message,
                    context: {
                        selected_nodes: visualContext.selected_nodes,
                        focused_beings: visualContext.focused_beings,
                        viewport_center: visualContext.viewport_center,
                        nearby_beings: visualContext.nearby_beings,
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

    getVisualContext() {
        """Pobiera kontekst wizualny - na co użytkownik patrzy"""
        const context = {
            selected_nodes: [],
            focused_beings: [],
            viewport_center: { x: 0, y: 0 },
            nearby_beings: []
        };

        if (!this.graphManager) return context;

        // Pobierz zaznaczone węzły
        context.selected_nodes = this.graphManager.selectedNodes || [];
        
        // Pobierz nazwy bytów dla lepszego feedbacku
        context.focused_beings = context.selected_nodes.map(nodeId => {
            const being = this.graphManager.beings.find(b => b.soul === nodeId);
            return being ? being.genesis.name || 'Unknown' : 'Unknown';
        });

        // Pobierz centrum widoku
        if (this.graphManager.svg) {
            const transform = this.graphManager.svg.node().transform;
            if (transform) {
                context.viewport_center = {
                    x: transform.baseVal.length > 0 ? transform.baseVal[0].matrix.e : 0,
                    y: transform.baseVal.length > 0 ? transform.baseVal[0].matrix.f : 0
                };
            }
        }

        // Znajdź pobliskie byty (w widoku)
        if (this.graphManager.beings) {
            const viewportRadius = 300; // Promień "bliskości"
            const center = context.viewport_center;
            
            context.nearby_beings = this.graphManager.beings
                .filter(being => {
                    if (!being.x || !being.y) return false;
                    const distance = Math.sqrt(
                        Math.pow(being.x - center.x, 2) + 
                        Math.pow(being.y - center.y, 2)
                    );
                    return distance <= viewportRadius;
                })
                .map(being => being.soul)
                .slice(0, 5); // Maksymalnie 5 najbliższych
        }

        return context;
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

        // Pokaż akcję jaką podjął Lux
        if (response.action_taken) {
            this.showActionTaken(response.action_taken, response.result);
        }

        // Pokaż analizę kontekstu
        if (response.context_analysis) {
            this.showContextAnalysis(response.context_analysis);
        }

        // Zaktualizuj graf jeśli coś zostało utworzone
        if (response.result && (response.result.created_being || response.result.created_parent)) {
            setTimeout(() => {
                if (this.graphManager && this.graphManager.socket) {
                    this.graphManager.socket.emit('get_graph_data');
                }
            }, 500);
        }

        // Wyczyść input po pomyślnej analizie
        this.clearInput();
    }

    showActionTaken(action, result) {
        const actionMessages = {
            'create_new': `🌟 Utworzono nowy byt: ${result.created_being || 'Unknown'}`,
            'attach_to_focused': `🔗 Dodano do kontekstu: ${result.attached_to || 'Unknown'}`,
            'continue_thread': `➡️ Kontynuacja wątku`,
            'create_parent_concept': `🏗️ Utworzono nadrzędny koncept: ${result.created_parent || 'Unknown'}`
        };

        const message = actionMessages[action] || `⚡ Akcja: ${action}`;
        this.showFeedback(message, 'success');

        // Dodatkowe informacje dla grupowania
        if (action === 'create_parent_concept' && result.grouped_beings) {
            this.showFeedback(`📦 Pogrupowano ${result.grouped_beings.length} bytów`, 'info');
        }
    }

    showContextAnalysis(analysis) {
        let contextInfo = '';
        
        if (analysis.relates_to_focused && analysis.relates_to_focused.length > 0) {
            const focusedNames = analysis.relates_to_focused.map(rel => rel.being_name).join(', ');
            contextInfo += `👀 Związane z: ${focusedNames}. `;
        }

        if (analysis.relates_to_history && analysis.relates_to_history.length > 0) {
            contextInfo += `📚 Nawiązuje do wcześniejszej rozmowy. `;
        }

        if (analysis.new_concept) {
            contextInfo += `💡 Nowy koncept. `;
        }

        if (contextInfo) {
            this.showFeedback(`🧠 Analiza: ${contextInfo}(Pewność: ${Math.round(analysis.confidence * 100)}%)`, 'info');
        }
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
