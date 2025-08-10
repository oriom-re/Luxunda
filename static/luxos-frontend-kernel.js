/**
 * LuxOS Frontend Kernel - Samowystarczalny system z obsługą scenariuszy
 */

class FrontendKernel {
    constructor() {
        this.beings = new Map();
        this.souls = new Map();
        this.scenarios = new Map();
        this.lux = null;
        this.scenarioManager = null;
        this.dbConnection = null;
        this.biosScenario = null;
        this.initialized = false;
        this.bootstrapState = 'init';
    }

    async initialize() {
        console.log('🚀 LuxOS Frontend Kernel - Inicjalizacja...');

        try {
            // 1. Połączenie z bazą danych
            await this.connectToDatabase();

            // 2. Ładowanie BIOS scenariusza
            await this.loadBiosScenario();

            // 3. Wykonanie sekwencji bootstrap
            await this.executeBootstrapSequence();

            // 4. Inicjalizacja podstawowych bytów
            await this.initializeCoreBeing();

            // 5. Uruchomienie event listenerów
            this.startEventListeners();

            this.initialized = true;
            this.bootstrapState = 'ready';

            console.log('✅ LuxOS Frontend Kernel zainicjalizowany');
            this.emit('kernel:ready', this);

            return this;

        } catch (error) {
            console.error('❌ Błąd inicjalizacji kernela:', error);
            this.bootstrapState = 'error';
            throw error;
        }
    }

    async connectToDatabase() {
        console.log('📡 Łączenie z bazą danych...');

        this.dbConnection = {
            async query(endpoint, options = {}) {
                const response = await fetch(`/api/${endpoint}`, {
                    method: options.method || 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    body: options.body ? JSON.stringify(options.body) : undefined
                });

                if (!response.ok) {
                    throw new Error(`API Error: ${response.status}`);
                }

                return await response.json();
            },

            async getScenario(name) {
                return await this.query(`scenarios/${name}`);
            },

            async saveScenario(name, data) {
                return await this.query(`scenarios/${name}`, {
                    method: 'POST',
                    body: data
                });
            },

            async getMinimalBeings() {
                return await this.query('beings/minimal');
            },

            async getBeing(ulid) {
                return await this.query(`beings/${ulid}`);
            },

            async createBeing(beingData) {
                return await this.query('beings', {
                    method: 'POST',
                    body: { being_data: beingData }
                });
            },

            async getSoul(soulHash) {
                return await this.query(`souls/${soulHash}`);
            },

            async getSystemStatus() {
                return await this.query('system/status');
            }
        };

        // Test połączenia
        const status = await this.dbConnection.getSystemStatus();
        console.log('📊 Status systemu:', status);
    }

    async loadBiosScenario() {
        console.log('🔧 Ładowanie BIOS scenariusza...');
        this.bootstrapState = 'loading_bios';

        try {
            const biosResponse = await this.dbConnection.query('bios');
            this.biosScenario = biosResponse.data;

            console.log('✅ BIOS załadowany:', this.biosScenario.name);
            this.scenarios.set('bios', this.biosScenario);

        } catch (error) {
            console.error('❌ Błąd ładowania BIOS:', error);
            // Fallback do lokalnego BIOS
            this.biosScenario = this.createFallbackBios();
        }
    }

    createFallbackBios() {
        return {
            name: "LuxOS BIOS Fallback",
            version: "1.0.0",
            description: "Lokalny scenariusz rozruchowy",
            bootstrap_sequence: [
                "init_kernel",
                "load_communication",
                "setup_ui",
                "ready_state"
            ],
            required_beings: [
                {
                    alias: "lux_assistant",
                    type: "ai_assistant",
                    priority: 100
                }
            ]
        };
    }

    async executeBootstrapSequence() {
        console.log('⚙️ Wykonywanie sekwencji bootstrap z BIOS bytu...');
        this.bootstrapState = 'bootstrap';

        const sequence = this.biosScenario.bootstrap_sequence || [
            'init_kernel',
            'load_communication',
            'setup_ui',
            'ready_state'
        ];

        const fallbackProcedure = this.biosScenario.fallback_procedure || {
            max_retries: 3,
            retry_delay: 5000,
            emergency_mode: true
        };

        console.log('📋 BIOS instrukcje:', {
            sequence,
            fallback: fallbackProcedure,
            required_beings: this.biosScenario.required_beings?.length || 0
        });

        let retries = 0;
        while (retries < fallbackProcedure.max_retries) {
            try {
                for (const step of sequence) {
                    console.log(`🔄 Bootstrap krok ${retries + 1}/${fallbackProcedure.max_retries}: ${step}`);
                    await this.executeBootstrapStep(step);
                }

                // Jeśli udało się wykonać całą sekwencję, przerwij pętlę
                break;

            } catch (error) {
                retries++;
                console.error(`❌ Błąd w bootstrap (próba ${retries}):`, error);

                if (retries < fallbackProcedure.max_retries) {
                    console.log(`⏳ Czekam ${fallbackProcedure.retry_delay}ms przed ponowną próbą...`);
                    await new Promise(resolve => setTimeout(resolve, fallbackProcedure.retry_delay));
                } else if (fallbackProcedure.emergency_mode) {
                    console.log('🚨 Tryb awaryjny - minimalna inicjalizacja...');
                    await this.executeEmergencyBootstrap();
                }
            }
        }

        this.bootstrapState = 'complete';
        this.emit('kernel:bootstrap_complete');
    }

    async executeBootstrapStep(step) {
        switch (step) {
            case 'init_kernel':
                await this.initKernel();
                break;
            case 'load_communication':
                await this.loadCommunication();
                break;
            case 'setup_ui':
                await this.setupUI();
                break;
            case 'ready_state':
                await this.enterReadyState();
                break;
            default:
                console.warn(`⚠️ Nieznany krok bootstrap: ${step}`);
        }
    }

    async initKernel() {
        // Inicjalizacja podstawowych struktur
        this.beings.clear();
        this.souls.clear();

        // Utwórz scenario manager
        this.scenarioManager = new ScenarioManager(this);
    }

    async loadCommunication() {
        // Przygotowanie systemu komunikacji
        this.eventHub = new EventTarget();
    }

    async setupUI() {
        // Przygotowanie interfejsu
        this.emit('ui:setup_required');
    }

    async enterReadyState() {
        // System gotowy do pracy
        this.emit('kernel:bootstrap_complete');
    }

    async initializeCoreBeing() {
        console.log('🤖 Inicjalizacja podstawowych bytów...');

        const requiredBeings = this.biosScenario.required_beings || [];

        for (const beingConfig of requiredBeings) {
            switch (beingConfig.type) {
                case 'ai_assistant':
                    await this.createLuxAssistant(beingConfig);
                    break;
                case 'system_manager':
                    await this.createSystemManager(beingConfig);
                    break;
                default:
                    console.log(`📦 Tworzenie bytu: ${beingConfig.alias}`);
                    await this.createGenericBeing(beingConfig);
            }
        }
    }

    async createLuxAssistant(config) {
        const luxSoul = {
            soul_hash: 'lux_frontend_soul_001',
            genotype: {
                genesis: {
                    name: 'lux_assistant_frontend',
                    type: 'ai_assistant',
                    version: '2.0.0',
                    environment: 'browser'
                },
                attributes: {
                    conversation_history: { py_type: 'list' },
                    scenario_awareness: { py_type: 'dict' },
                    kernel_access: { py_type: 'bool', default: true }
                },
                capabilities: {
                    process_message: 'lux.processMessage',
                    manage_scenarios: 'lux.manageScenarios',
                    create_beings: 'lux.createBeings'
                }
            }
        };

        this.lux = new LuxAssistant(luxSoul, this);
        this.beings.set('lux_assistant', this.lux);

        console.log('🌟 Lux Assistant zainicjalizowany');
    }

    async createSystemManager(config) {
        // Placeholder dla system managera
        const manager = new SystemManager(config, this);
        this.beings.set(config.alias, manager);
    }

    async createGenericBeing(config) {
        const being = new GenericBeing(config, this);
        this.beings.set(config.alias, being);
    }

    startEventListeners() {
        // DOM event listeners
        document.addEventListener('luxos:message', (e) => {
            this.handleMessage(e.detail);
        });

        document.addEventListener('luxos:load_scenario', (e) => {
            this.loadScenario(e.detail.name);
        });

        document.addEventListener('luxos:create_being', (e) => {
            this.createBeing(e.detail);
        });

        console.log('🔧 Event listeners uruchomione');
    }

    async handleMessage(message) {
        console.log('💬 Kernel otrzymał wiadomość:', message);

        if (this.lux) {
            const response = await this.lux.processMessage(message);
            this.emit('lux:response', response);
        } else {
            this.emit('lux:response', 'System jeszcze się inicjalizuje...');
        }
    }

    async loadScenario(scenarioName) {
        console.log(`📋 Ładowanie scenariusza: ${scenarioName}`);

        try {
            const scenarioData = await this.dbConnection.getScenario(scenarioName);
            this.scenarios.set(scenarioName, scenarioData.data);

            this.emit('scenario:loaded', {
                name: scenarioName,
                data: scenarioData.data
            });

            return scenarioData.data;

        } catch (error) {
            console.error(`❌ Błąd ładowania scenariusza ${scenarioName}:`, error);
            throw error;
        }
    }

    async createBeing(beingData) {
        console.log('🆕 Tworzenie nowego bytu:', beingData);

        try {
            const result = await this.dbConnection.createBeing(beingData);

            // Utwórz lokalną instancję
            const being = new FrontendBeing(beingData, this);
            this.beings.set(result.ulid, being);

            this.emit('being:created', being);
            return being;

        } catch (error) {
            console.error('❌ Błąd tworzenia bytu:', error);
            throw error;
        }
    }

    emit(eventName, data) {
        const event = new CustomEvent(`luxos:${eventName}`, { detail: data });
        document.dispatchEvent(event);
    }

    // API publiczne
    getBeing(ulid) {
        return this.beings.get(ulid);
    }

    getAllBeings() {
        return Array.from(this.beings.values());
    }

    getScenario(name) {
        return this.scenarios.get(name);
    }

    getBootstrapState() {
        return this.bootstrapState;
    }

    async saveBeing(being) {
        try {
            await this.dbConnection.createBeing(being.toJSON());
            console.log(`💾 Zapisano byt: ${being.alias}`);
        } catch (error) {
            console.error('❌ Błąd zapisywania bytu:', error);
        }
    }

    async executeEmergencyBootstrap() {
        console.log('🚨 Wykonywanie awaryjnej sekwencji bootstrap...');

        // Minimalna sekwencja w trybie awaryjnym
        const emergencySequence = ['init_kernel', 'ready_state'];

        for (const step of emergencySequence) {
            try {
                console.log(`🚨 Awaryjny krok: ${step}`);
                await this.executeBootstrapStep(step);
            } catch (error) {
                console.error(`💥 Krytyczny błąd w kroku ${step}:`, error);
                // W trybie awaryjnym kontynuuj mimo błędów
            }
        }
    }
}

class LuxAssistant {
    constructor(soul, kernel) {
        this.soul = soul;
        this.kernel = kernel;
        this.conversationHistory = [];
        this.scenarioAwareness = {};
    }

    async processMessage(message) {
        console.log('🤖 Lux przetwarza:', message);

        this.conversationHistory.push({
            timestamp: new Date(),
            message: message,
            type: 'user'
        });

        const intent = this.analyzeIntent(message);
        let response;

        switch (intent.type) {
            case 'create_being':
                response = await this.handleCreateBeing(intent);
                break;
            case 'load_scenario':
                response = await this.handleLoadScenario(intent);
                break;
            case 'system_status':
                response = await this.handleSystemStatus(intent);
                break;
            case 'general_chat':
                response = await this.handleGeneralChat(intent);
                break;
            default:
                response = "Nie rozumiem tej komendy. Spróbuj: 'stwórz byt', 'załaduj scenariusz', 'status systemu'";
        }

        this.conversationHistory.push({
            timestamp: new Date(),
            message: response,
            type: 'assistant'
        });

        return response;
    }

    analyzeIntent(message) {
        const lowerMessage = message.toLowerCase();

        if (lowerMessage.includes('stwórz') || lowerMessage.includes('utwórz')) {
            return { type: 'create_being', message };
        }

        if (lowerMessage.includes('scenariusz') || lowerMessage.includes('załaduj')) {
            return { type: 'load_scenario', message };
        }

        if (lowerMessage.includes('status') || lowerMessage.includes('stan')) {
            return { type: 'system_status', message };
        }

        return { type: 'general_chat', message };
    }

    async handleCreateBeing(intent) {
        try {
            const beingData = {
                alias: `being_${Date.now()}`,
                data: {
                    created_by: 'lux_assistant',
                    creation_intent: intent.message,
                    created_at: new Date().toISOString(),
                    type: 'user_created'
                }
            };

            const being = await this.kernel.createBeing(beingData);
            return `✨ Utworzyłem nowy byt: ${being.alias}`;
        } catch (error) {
            return `❌ Nie udało się utworzyć bytu: ${error.message}`;
        }
    }

    async handleLoadScenario(intent) {
        try {
            // Wyciągnij nazwę scenariusza z wiadomości
            const match = intent.message.match(/scenariusz\s+(\w+)/i);
            const scenarioName = match ? match[1] : 'default';

            const scenario = await this.kernel.loadScenario(scenarioName);
            return `📋 Załadowałem scenariusz: ${scenario.name || scenarioName}`;
        } catch (error) {
            return `❌ Nie udało się załadować scenariusza: ${error.message}`;
        }
    }

    async handleSystemStatus(intent) {
        const beings = this.kernel.getAllBeings();
        const scenarios = Array.from(this.kernel.scenarios.keys());
        const bootstrapState = this.kernel.getBootstrapState();

        return `📊 Status systemu LuxOS:
• Bootstrap: ${bootstrapState}
• Bytów w pamięci: ${beings.length}
• Scenariuszy: ${scenarios.length} (${scenarios.join(', ')})
• Tryb: Frontend-only
• Baza: Połączona`;
    }

    async handleGeneralChat(intent) {
        // Najpierw spróbuj komunikacji z serwerem
        try {
            const response = await fetch('/api/lux/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: intent.message
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                return data.response;
            } else {
                throw new Error(data.response || 'Server error');
            }
        } catch (error) {
            console.warn('Fallback to local chat:', error);
            // Fallback do lokalnej odpowiedzi
            return `🤖 Jestem Lux, asystentem LuxOS działającym w przeglądarce.
Mogę zarządzać bytami i scenariuszami.
System status: ${this.kernel.getBootstrapState()}
⚠️ Komunikacja z serwerem niedostępna - tryb lokalny`;
        }
    }
}

class ScenarioManager {
    constructor(kernel) {
        this.kernel = kernel;
        this.loadedScenarios = new Map();
    }

    async loadScenario(name) {
        return await this.kernel.loadScenario(name);
    }

    async createScenario(name, data) {
        await this.kernel.dbConnection.saveScenario(name, data);
        this.loadedScenarios.set(name, data);
    }
}

class SystemManager {
    constructor(config, kernel) {
        this.config = config;
        this.kernel = kernel;
        this.alias = config.alias;
    }
}

class GenericBeing {
    constructor(config, kernel) {
        this.config = config;
        this.kernel = kernel;
        this.alias = config.alias;
        this.type = config.type;
    }
}

class FrontendBeing {
    constructor(data, kernel) {
        this.ulid = data.ulid || this.generateULID();
        this.soul_hash = data.soul_hash;
        this.alias = data.alias;
        this.data = data.data || {};
        this.kernel = kernel;
        this.created_at = data.created_at;
        this.updated_at = data.updated_at;
    }

    generateULID() {
        // Prosta implementacja ULID-like
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    async save() {
        await this.kernel.saveBeing(this);
    }

    toJSON() {
        return {
            ulid: this.ulid,
            soul_hash: this.soul_hash,
            alias: this.alias,
            data: this.data,
            created_at: this.created_at,
            updated_at: new Date().toISOString()
        };
    }
}

// Globalna instancja
window.LuxOSKernel = null;

// Auto-inicjalizacja po załadowaniu DOM
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('🌟 LuxOS Frontend System - Uruchamianie...');

        window.LuxOSKernel = new FrontendKernel();
        await window.LuxOSKernel.initialize();

        // Emit ready event
        document.dispatchEvent(new CustomEvent('luxos:ready', {
            detail: window.LuxOSKernel
        }));

    } catch (error) {
        console.error('❌ Błąd inicjalizacji LuxOS:', error);

        // Emit error event
        document.dispatchEvent(new CustomEvent('luxos:error', {
            detail: { error: error.message }
        }));
    }
});
/**
 * LuxOS Frontend Kernel - System komunikacji z asystentem Lux
 */
class LuxOSKernel {
    constructor() {
        this.isInitialized = false;
        this.assistantReady = false;
        this.conversationHistory = [];
        this.specialistBeings = new Map();
        this.chainProcessing = false;
    }

    async initialize() {
        try {
            console.log('🚀 Initializing LuxOS Kernel...');
            
            // Initialize communication with backend
            await this.setupCommunication();
            
            // Initialize specialist beings registry
            await this.loadSpecialistBeings();
            
            // Setup conversation interface
            this.setupConversationInterface();
            
            this.isInitialized = true;
            this.assistantReady = true;
            
            console.log('✅ LuxOS Kernel initialized successfully');
            this.displayWelcomeMessage();
            
        } catch (error) {
            console.error('❌ Błąd inicjalizacji:', error);
            this.displayErrorMessage('Initialization failed: ' + error.message);
        }
    }

    async setupCommunication() {
        // Setup WebSocket or fetch-based communication
        this.apiBase = window.location.origin;
        
        // Test connection
        const response = await fetch(`${this.apiBase}/api/status`);
        if (!response.ok) {
            throw new Error('Failed to connect to backend');
        }
        
        const status = await response.json();
        console.log('📡 Backend connection established:', status);
    }

    async loadSpecialistBeings() {
        try {
            const response = await fetch(`${this.apiBase}/api/beings/specialists`);
            if (response.ok) {
                const specialists = await response.json();
                specialists.forEach(being => {
                    this.specialistBeings.set(being.alias, being);
                });
                console.log(`🧬 Loaded ${specialists.length} specialist beings`);
            }
        } catch (error) {
            console.warn('⚠️ Could not load specialist beings:', error);
        }
    }

    setupConversationInterface() {
        // Create conversation container if it doesn't exist
        let chatContainer = document.getElementById('lux-chat');
        if (!chatContainer) {
            chatContainer = document.createElement('div');
            chatContainer.id = 'lux-chat';
            chatContainer.innerHTML = `
                <div id="lux-messages" class="messages-container"></div>
                <div class="input-container">
                    <input type="text" id="lux-input" placeholder="Napisz wiadomość do Lux..." />
                    <button id="lux-send" onclick="luxKernel.sendMessage()">Wyślij</button>
                </div>
            `;
            document.body.appendChild(chatContainer);
        }

        // Setup input handler
        const input = document.getElementById('lux-input');
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }

        // Add basic styling
        this.addBasicStyles();
    }

    addBasicStyles() {
        if (document.getElementById('lux-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'lux-styles';
        style.textContent = `
            #lux-chat {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 400px;
                height: 500px;
                background: white;
                border: 2px solid #0066cc;
                border-radius: 10px;
                display: flex;
                flex-direction: column;
                font-family: Arial, sans-serif;
                z-index: 1000;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }
            
            .messages-container {
                flex: 1;
                overflow-y: auto;
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            
            .input-container {
                display: flex;
                padding: 10px;
                gap: 10px;
            }
            
            #lux-input {
                flex: 1;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            #lux-send {
                padding: 8px 16px;
                background: #0066cc;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .message {
                margin: 10px 0;
                padding: 8px 12px;
                border-radius: 8px;
                max-width: 80%;
            }
            
            .message.user {
                background: #e3f2fd;
                margin-left: auto;
                text-align: right;
            }
            
            .message.assistant {
                background: #f5f5f5;
            }
            
            .message.system {
                background: #fff3cd;
                font-style: italic;
                text-align: center;
            }
            
            .processing {
                color: #666;
                font-style: italic;
            }
        `;
        document.head.appendChild(style);
    }

    displayWelcomeMessage() {
        this.addMessage('system', '🌟 Lux Assistant gotowa do rozmowy! Mam dostęp do zespołu specjalistów.');
    }

    displayErrorMessage(message) {
        this.addMessage('system', '❌ ' + message);
    }

    addMessage(type, content) {
        const messagesContainer = document.getElementById('lux-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = content;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async sendMessage() {
        const input = document.getElementById('lux-input');
        if (!input || !input.value.trim()) return;

        const message = input.value.trim();
        input.value = '';

        // Add user message to chat
        this.addMessage('user', message);
        
        // Show processing
        this.addMessage('system', '🤖 Lux przetwarza wiadomość...');

        try {
            // Send to backend for processing
            const response = await this.processMessageWithSpecialists(message);
            
            // Remove processing message
            const messages = document.querySelectorAll('#lux-messages .message.system');
            const lastMessage = messages[messages.length - 1];
            if (lastMessage && lastMessage.textContent.includes('przetwarza')) {
                lastMessage.remove();
            }
            
            // Add response
            this.addMessage('assistant', response);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('system', '❌ Błąd podczas przetwarzania wiadomości');
        }
    }

    async processMessageWithSpecialists(message) {
        try {
            // Send message to Lux Assistant with specialist chain processing
            const response = await fetch(`${this.apiBase}/api/lux/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    use_specialists: true,
                    conversation_history: this.conversationHistory.slice(-10)
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Store in conversation history
            this.conversationHistory.push({
                user: message,
                assistant: data.response,
                timestamp: new Date().toISOString(),
                specialists_used: data.specialists_used || []
            });

            return data.response || 'Brak odpowiedzi od asystenta';
            
        } catch (error) {
            console.error('Error in specialist processing:', error);
            return 'Przepraszam, wystąpił błąd podczas przetwarzania Twojej wiadomości.';
        }
    }

    // Public API methods
    isReady() {
        return this.isInitialized && this.assistantReady;
    }

    getConversationHistory() {
        return this.conversationHistory;
    }

    clearConversation() {
        this.conversationHistory = [];
        const messagesContainer = document.getElementById('lux-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        this.displayWelcomeMessage();
    }
}

// Initialize kernel when DOM is ready
const luxKernel = new LuxOSKernel();

document.addEventListener('DOMContentLoaded', () => {
    luxKernel.initialize();
});

// Export for global access
window.luxKernel = luxKernel;
