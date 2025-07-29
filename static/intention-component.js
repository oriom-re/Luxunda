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

    async sendIntention() {
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
                    task_analysis: this.analyzeTaskComplexity(message),
                    context: {
                        selected_nodes: this.graphManager.selectedNodes || [],
                        timestamp: new Date().toISOString(),
                        user_agent: navigator.userAgent,
                        session_id: this.graphManager.socket.id,
                        frontend_capabilities: this.getFrontendCapabilities()
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

    analyzeTaskComplexity(intention) {
        const heavyTaskKeywords = [
            'analizuj', 'przetwórz', 'oblicz', 'generuj', 'zapisz', 'czytaj plik',
            'uruchom test', 'wykonaj kod', 'kompiluj', 'deploy', 'baza danych',
            'długoterminowy', 'cykliczny', 'harmonogram', 'monitor'
        ];

        const frontendTaskKeywords = [
            'pokaż', 'wyświetl', 'ukryj', 'animuj', 'zoom', 'przewiń',
            'filtruj', 'sortuj', 'kolor', 'wizualizuj', 'interfejs'
        ];

        const complexity = {
            is_heavy_task: heavyTaskKeywords.some(keyword =>
                intention.toLowerCase().includes(keyword)
            ),
            is_frontend_task: frontendTaskKeywords.some(keyword =>
                intention.toLowerCase().includes(keyword)
            ),
            requires_file_operations: intention.includes('plik') || intention.includes('kod'),
            requires_database: intention.includes('baza') || intention.includes('zapisz'),
            is_long_term: intention.includes('długo') || intention.includes('cykl') ||
                intention.includes('monitor'),
            delegation_recommendation: 'auto' // auto, frontend, backend
        };

        // Recommend delegation strategy
        if (complexity.is_heavy_task || complexity.requires_file_operations ||
            complexity.requires_database || complexity.is_long_term) {
            complexity.delegation_recommendation = 'backend';
        } else if (complexity.is_frontend_task) {
            complexity.delegation_recommendation = 'frontend';
        }

        return complexity;
    }

    getFrontendCapabilities() {
        return {
            d3_visualization: true,
            real_time_animation: true,
            user_interaction: true,
            local_storage: true,
            client_side_filtering: true,
            webgl_rendering: !!window.WebGLRenderingContext,
            available_memory: navigator.deviceMemory || 'unknown',
            cpu_cores: navigator.hardwareConcurrency || 'unknown'
        };
    }


    handleIntentionResponse(response) {
        console.log('Intention response received:', response);

        // Resetuj przycisk
        this.resetSendButton();

        if (response.message) {
            this.showFeedback(response.message, 'success');
        }

        // Handle delegation information
        if (response.delegation_info) {
            this.handleDelegationInstructions(response.delegation_info, response);
        }

        // Handle frontend instructions from hybrid tasks
        if (response.frontend_instructions && response.frontend_instructions.length > 0) {
            this.executeFrontendInstructions(response.frontend_instructions);
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

    handleDelegationInstructions(delegationInfo, response) {
        console.log('🔄 Delegation info:', delegationInfo);

        // Show delegation status
        const delegationStatus = document.createElement('div');
        delegationStatus.className = 'delegation-status';
        delegationStatus.style.cssText = `
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid #00ff88;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-size: 12px;
            color: #00ff88;
        `;

        let statusText = '';
        switch(delegationInfo.execute_on) {
            case 'backend':
                statusText = `🖥️ Zadanie wykonywane na backendzie: ${delegationInfo.reason}`;
                break;
            case 'frontend':
                statusText = `💻 Zadanie przekazane do frontendu: ${delegationInfo.reason}`;
                break;
            case 'hybrid':
                statusText = `🔄 Zadanie hybrydowe: ${delegationInfo.reason}`;
                break;
        }

        delegationStatus.textContent = statusText;
        // Assuming you have a container element with id 'responseDiv' in your HTML
        if (document.getElementById('responseDiv')) {
            document.getElementById('responseDiv').appendChild(delegationStatus);
        } else {
            console.warn('Element with id "responseDiv" not found, cannot display delegation status.');
            document.body.appendChild(delegationStatus); //Fallback append to body if responseDiv not found
        }

    }


    executeFrontendInstructions(instructions) {
        console.log('🎨 Executing frontend instructions:', instructions);

        instructions.forEach(instruction => {
            switch(instruction.action) {
                case 'update_visualization':
                    this.updateVisualization(instruction.data);
                    break;
                case 'create_visualization':
                    this.createVisualization(instruction);
                    break;
                case 'animate_elements':
                    this.animateElements(instruction);
                    break;
                default:
                    console.warn('Unknown frontend instruction:', instruction.action);
            }
        });
    }

    updateVisualization(data) {
        if (this.graphManager && data) {
            console.log('📊 Updating visualization with backend data');
            // Delegate to graph manager for visualization updates
            if (data.beings_summary) {
                this.graphManager.highlightBeings(data.beings_summary);
            }
        }
    }

    createVisualization(instruction) {
        if (this.graphManager) {
            console.log('🎨 Creating visualization:', instruction.type);

            if (instruction.type === 'graph_update' && instruction.animate) {
                // Trigger smooth graph animation
                this.graphManager.svg.transition()
                    .duration(1000)
                    .style('filter', 'brightness(1.2)')
                    .transition()
                    .duration(1000)
                    .style('filter', 'brightness(1)');
            }
        }
    }

    animateElements(instruction) {
        console.log('✨ Animating elements:', instruction);
        // Add custom animations based on instruction parameters
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
class IntentionComponent {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.initializeComponent();
        console.log('🧠 Intention Component initialized');
    }

    initializeComponent() {
        this.input = document.getElementById('intentionInput');
        this.button = document.getElementById('sendIntention');
        this.counter = document.getElementById('charCounter');

        this.setupEventListeners();
        this.updateCounter();
    }

    setupEventListeners() {
        // Character counter
        this.input.addEventListener('input', () => {
            this.updateCounter();
        });

        // Send on button click
        this.button.addEventListener('click', () => {
            this.sendIntention();
        });

        // Send on Ctrl+Enter
        this.input.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.sendIntention();
            }
        });

        // Auto-resize textarea
        this.input.addEventListener('input', () => {
            this.autoResize();
        });
    }

    updateCounter() {
        const length = this.input.value.length;
        this.counter.textContent = length;
        
        if (length > 450) {
            this.counter.style.color = '#ff4444';
        } else if (length > 350) {
            this.counter.style.color = '#ffaa00';
        } else {
            this.counter.style.color = '#888';
        }
    }

    autoResize() {
        this.input.style.height = 'auto';
        this.input.style.height = Math.min(this.input.scrollHeight, 200) + 'px';
    }

    sendIntention() {
        const intention = this.input.value.trim();
        
        if (!intention) {
            this.showFeedback('Wprowadź swoją intencję', 'error');
            return;
        }

        if (intention.length > 500) {
            this.showFeedback('Intencja zbyt długa (max 500 znaków)', 'error');
            return;
        }

        // Disable button during processing
        this.button.disabled = true;
        this.button.textContent = '🌀 Przetwarzanie...';

        // Send to backend via WebSocket
        const intentionData = {
            type: 'send_intention',
            intention: intention,
            timestamp: new Date().toISOString(),
            selected_nodes: Array.from(this.graphManager.selectedNodes || [])
        };

        console.log('🧠 Wysyłanie intencji:', intentionData);
        
        if (this.graphManager.socket && this.graphManager.socket.connected) {
            this.graphManager.socket.emit('send_intention', intentionData);
            this.showFeedback('Intencja wysłana do LuxDB', 'success');
            
            // Clear input after successful send
            setTimeout(() => {
                this.input.value = '';
                this.updateCounter();
                this.autoResize();
            }, 500);
        } else {
            this.showFeedback('Brak połączenia z serwerem', 'error');
        }

        // Re-enable button
        setTimeout(() => {
            this.button.disabled = false;
            this.button.textContent = '🌀 Manifestuj w LuxDB';
        }, 1000);
    }

    showFeedback(message, type = 'info') {
        // Create or get feedback element
        let feedback = document.querySelector('.feedback-message');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'feedback-message';
            document.body.appendChild(feedback);
        }

        feedback.textContent = message;
        feedback.className = `feedback-message ${type}`;
        feedback.classList.add('show');

        // Auto-hide after 3 seconds
        setTimeout(() => {
            feedback.classList.remove('show');
        }, 3000);
    }

    // Method to handle responses from the graph manager
    handleIntentionResponse(response) {
        console.log('🎯 Odpowiedź na intencję:', response);
        
        if (response.analysis) {
            const analysis = response.analysis;
            let message = `Rozpoznano: ${analysis.luxdb_type}`;
            
            if (analysis.suggested_action) {
                message += ` → ${analysis.suggested_action}`;
            }
            
            this.showFeedback(message, 'success');
            
            // Handle specific intention types
            switch (analysis.luxdb_type) {
                case 'being_manifestation':
                    this.handleBeingManifestation(analysis);
                    break;
                case 'soul_query':
                    this.handleSoulQuery(analysis);
                    break;
                case 'relationship_creation':
                    this.handleRelationshipCreation(analysis);
                    break;
            }
        }
    }

    handleBeingManifestation(analysis) {
        if (analysis.parameters && analysis.parameters.suggested_soul) {
            const manifestData = {
                type: 'manifest_being',
                soul_type: analysis.parameters.suggested_soul,
                alias: `being_${Date.now()}`,
                attributes: {}
            };
            
            console.log('✨ Manifestuję byt:', manifestData);
            this.graphManager.socket.emit('manifest_being', manifestData);
        }
    }

    handleSoulQuery(analysis) {
        console.log('🧬 Zapytanie o dusze - wyświetlam dostępne genotypy');
        // Could trigger display of available souls in UI
    }

    handleRelationshipCreation(analysis) {
        const selectedNodes = Array.from(this.graphManager.selectedNodes || []);
        if (selectedNodes.length >= 2) {
            console.log('🔗 Tworzę relację między wybranymi węzłami:', selectedNodes);
            // Logic to create relationships between selected nodes
        } else {
            this.showFeedback('Wybierz co najmniej 2 węzły aby utworzyć relację', 'error');
        }
    }

    // Utility method to suggest intentions based on current graph state
    suggestIntentions() {
        const suggestions = [
            "Stwórz nowy agent AI",
            "Dodaj dane semantyczne o projekcie",
            "Połącz wybrane byty relacją",
            "Pokaż dostępne genotypy",
            "Manifestuj byt z duszy semantic_data_soul"
        ];
        
        return suggestions;
    }
}

// Make available globally
window.IntentionComponent = IntentionComponent;
