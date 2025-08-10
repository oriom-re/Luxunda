
/**
 * LuxOS Frontend Kernel - Samowystarczalny system działający w przeglądarce
 */

class FrontendKernel {
    constructor() {
        this.beings = new Map();
        this.souls = new Map();
        this.lux = null;
        this.dbConnection = null;
        this.eventListeners = new Map();
        this.initialized = false;
    }

    async initialize() {
        console.log('🚀 Inicjalizacja LuxOS Frontend Kernel...');
        
        // Połączenie z bazą danych
        await this.connectToDatabase();
        
        // Inicjalizacja Lux Assistant
        await this.initializeLux();
        
        // Ładowanie bytów z bazy
        await this.loadBeingsFromDatabase();
        
        // Start event listeners
        this.startEventListeners();
        
        this.initialized = true;
        console.log('✅ LuxOS Frontend Kernel zainicjalizowany');
        
        return this;
    }

    async connectToDatabase() {
        // Symulacja połączenia z PostgreSQL przez API
        this.dbConnection = {
            async query(sql, params = []) {
                const response = await fetch('/api/db/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sql, params })
                });
                return await response.json();
            },
            
            async save(table, data) {
                const response = await fetch(`/api/db/${table}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                return await response.json();
            }
        };
        
        console.log('📡 Połączono z bazą danych');
    }

    async initializeLux() {
        // Tworzenie Lux Assistant jako bytu
        const luxSoul = {
            soul_hash: 'lux_kernel_hash_001',
            genotype: {
                genesis: {
                    name: 'lux_assistant',
                    type: 'ai_assistant',
                    version: '1.0.0'
                },
                attributes: {
                    conversation_history: { py_type: 'list' },
                    user_context: { py_type: 'dict' },
                    active_tools: { py_type: 'list' }
                },
                genes: {
                    process_message: 'lux.processMessage',
                    save_to_database: 'lux.saveToDatabase',
                    create_being: 'lux.createBeing'
                }
            }
        };

        this.lux = new LuxAssistant(luxSoul, this);
        this.beings.set('lux_assistant', this.lux);
        
        console.log('🌟 Lux Assistant zainicjalizowany');
    }

    async loadBeingsFromDatabase() {
        try {
            // Ładowanie souls z bazy
            const souls = await this.dbConnection.query('SELECT * FROM souls');
            souls.forEach(soul => {
                this.souls.set(soul.soul_hash, soul);
            });

            // Ładowanie beings z bazy
            const beings = await this.dbConnection.query('SELECT * FROM beings');
            beings.forEach(beingData => {
                const being = new FrontendBeing(beingData, this);
                this.beings.set(being.ulid, being);
            });

            console.log(`📋 Załadowano ${souls.length} souls i ${beings.length} beings`);
        } catch (error) {
            console.error('❌ Błąd ładowania z bazy:', error);
        }
    }

    startEventListeners() {
        // WebSocket lub EventSource dla real-time updates
        this.setupDatabaseListener();
        
        // DOM event listeners
        document.addEventListener('luxos:message', (e) => {
            this.handleMessage(e.detail);
        });
        
        document.addEventListener('luxos:create_being', (e) => {
            this.createBeing(e.detail);
        });
        
        console.log('🔧 Event listeners uruchomione');
    }

    setupDatabaseListener() {
        // Symulacja listenera do zmian w bazie
        setInterval(async () => {
            try {
                const changes = await this.dbConnection.query(
                    'SELECT * FROM beings WHERE updated_at > NOW() - INTERVAL \'10 seconds\''
                );
                
                changes.forEach(change => {
                    this.handleDatabaseChange(change);
                });
            } catch (error) {
                console.error('Database listener error:', error);
            }
        }, 5000); // Check co 5 sekund
    }

    async handleMessage(message) {
        console.log('💬 Otrzymano wiadomość:', message);
        
        if (this.lux) {
            const response = await this.lux.processMessage(message);
            this.emit('lux:response', response);
        }
    }

    async createBeing(beingData) {
        console.log('🆕 Tworzenie nowego bytu:', beingData);
        
        try {
            // Zapisz do bazy
            const result = await this.dbConnection.save('beings', beingData);
            
            // Dodaj do pamięci
            const being = new FrontendBeing(result, this);
            this.beings.set(being.ulid, being);
            
            this.emit('being:created', being);
            return being;
        } catch (error) {
            console.error('❌ Błąd tworzenia bytu:', error);
            throw error;
        }
    }

    handleDatabaseChange(change) {
        // Aktualizacja bytu w pamięci na podstawie zmiany w bazie
        if (this.beings.has(change.ulid)) {
            const being = this.beings.get(change.ulid);
            being.updateFromDatabase(change);
            this.emit('being:updated', being);
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

    async saveBeing(being) {
        try {
            await this.dbConnection.save('beings', being.toJSON());
            console.log(`💾 Zapisano byt: ${being.alias}`);
        } catch (error) {
            console.error('❌ Błąd zapisywania bytu:', error);
        }
    }
}

class LuxAssistant {
    constructor(soul, kernel) {
        this.soul = soul;
        this.kernel = kernel;
        this.conversationHistory = [];
        this.userContext = {};
    }

    async processMessage(message) {
        console.log('🤖 Lux przetwarza:', message);
        
        // Dodaj do historii
        this.conversationHistory.push({
            timestamp: new Date(),
            message: message,
            type: 'user'
        });

        // Analiza intencji
        const intent = this.analyzeIntent(message);
        let response;

        switch (intent.type) {
            case 'create_being':
                response = await this.handleCreateBeing(intent);
                break;
            case 'query_beings':
                response = await this.handleQueryBeings(intent);
                break;
            case 'general_chat':
                response = await this.handleGeneralChat(intent);
                break;
            default:
                response = "Nie rozumiem tej komendy. Spróbuj ponownie.";
        }

        // Dodaj odpowiedź do historii
        this.conversationHistory.push({
            timestamp: new Date(),
            message: response,
            type: 'assistant'
        });

        // Zapisz zmiany do bazy
        await this.saveToDatabase();

        return response;
    }

    analyzeIntent(message) {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('stwórz') || lowerMessage.includes('utwórz')) {
            return { type: 'create_being', message };
        }
        
        if (lowerMessage.includes('pokaż') || lowerMessage.includes('znajdź')) {
            return { type: 'query_beings', message };
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
                    created_at: new Date().toISOString()
                }
            };

            const being = await this.kernel.createBeing(beingData);
            return `✨ Utworzyłem nowy byt: ${being.alias}`;
        } catch (error) {
            return `❌ Nie udało się utworzyć bytu: ${error.message}`;
        }
    }

    async handleQueryBeings(intent) {
        const beings = this.kernel.getAllBeings();
        const count = beings.length;
        
        return `📊 W systemie jest ${count} bytów:\n${beings.map(b => `- ${b.alias}`).join('\n')}`;
    }

    async handleGeneralChat(intent) {
        return `🤖 Jestem Lux, asystentem LuxOS. Mogę pomóc Ci zarządzać bytami i danymi. Aktualnie mamy ${this.kernel.beings.size} bytów w pamięci.`;
    }

    async saveToDatabase() {
        try {
            await this.kernel.dbConnection.save('beings', {
                ulid: 'lux_assistant',
                data: {
                    conversation_history: this.conversationHistory.slice(-50), // Ostatnie 50 wiadomości
                    user_context: this.userContext,
                    updated_at: new Date().toISOString()
                }
            });
        } catch (error) {
            console.error('❌ Błąd zapisywania Lux do bazy:', error);
        }
    }
}

class FrontendBeing {
    constructor(data, kernel) {
        this.ulid = data.ulid;
        this.soul_hash = data.soul_hash;
        this.alias = data.alias;
        this.data = data.data || {};
        this.kernel = kernel;
        this.created_at = data.created_at;
        this.updated_at = data.updated_at;
    }

    updateFromDatabase(newData) {
        this.data = { ...this.data, ...newData.data };
        this.updated_at = newData.updated_at;
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
        window.LuxOSKernel = new FrontendKernel();
        await window.LuxOSKernel.initialize();
        
        // Emit ready event
        document.dispatchEvent(new CustomEvent('luxos:ready', { 
            detail: window.LuxOSKernel 
        }));
    } catch (error) {
        console.error('❌ Błąd inicjalizacji LuxOS:', error);
    }
});
