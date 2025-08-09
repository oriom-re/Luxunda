
/**
 * Frontend Communication Client - Event-driven communication with backend
 */

class CommunicationClient {
    constructor() {
        this.sessionData = null;
        this.connectionUlid = null;
        this.userUlid = null;
        this.isAuthenticated = false;
        this.eventHandlers = new Map();
        this.pollingInterval = null;
        this.lastEventId = null;
        this.connectionStatus = 'disconnected';
        this.heartbeatInterval = null;
        this.ttlChunks = new Map(); // TTL cache dla danych
        
        this.setupEventHandlers();
        console.log('📡 Communication Client initialized');
    }
    
    setupEventHandlers() {
        // Handlery dla różnych typów eventów
        this.on('connection_established', (data) => this.handleConnectionEstablished(data));
        this.on('connection_closed', (data) => this.handleConnectionClosed(data));
        this.on('lux_response', (data) => this.handleLuxResponse(data));
        this.on('notification', (data) => this.handleNotification(data));
        this.on('stream_data', (data) => this.handleStreamData(data));
        this.on('being_update', (data) => this.handleBeingUpdate(data));
    }
    
    async authenticate(username, password, fingerprint) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    fingerprint: fingerprint
                })
            });
            
            if (!response.ok) {
                throw new Error('Authentication failed');
            }
            
            const authData = await response.json();
            
            if (authData.success) {
                this.sessionData = authData.session;
                this.connectionUlid = authData.session.connection_ulid;
                this.userUlid = authData.session.user_ulid;
                this.isAuthenticated = true;
                
                // Rozpocznij polling eventów
                this.startEventPolling();
                this.startHeartbeat();
                
                console.log('🔓 Authentication successful:', username);
                this.emit('authenticated', authData);
                
                return true;
            }
            
            return false;
            
        } catch (error) {
            console.error('❌ Authentication error:', error);
            this.emit('auth_error', error);
            return false;
        }
    }
    
    async logout() {
        if (!this.isAuthenticated) return;
        
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.sessionData.session_token}`
                }
            });
            
            this.cleanup();
            console.log('🔒 Logged out successfully');
            
        } catch (error) {
            console.error('❌ Logout error:', error);
            this.cleanup();
        }
    }
    
    cleanup() {
        this.isAuthenticated = false;
        this.connectionStatus = 'disconnected';
        this.sessionData = null;
        this.connectionUlid = null;
        this.userUlid = null;
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        this.ttlChunks.clear();
        this.emit('disconnected');
    }
    
    startEventPolling() {
        if (this.pollingInterval) return;
        
        this.pollingInterval = setInterval(async () => {
            await this.pollEvents();
        }, 1000); // Poll co sekundę
        
        console.log('🔄 Event polling started');
    }
    
    async pollEvents() {
        if (!this.isAuthenticated || !this.connectionUlid) return;
        
        try {
            const response = await fetch('/api/events/poll', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.sessionData.session_token}`
                },
                body: JSON.stringify({
                    connection_ulid: this.connectionUlid,
                    last_event_id: this.lastEventId
                })
            });
            
            if (!response.ok) {
                throw new Error('Event polling failed');
            }
            
            const eventData = await response.json();
            
            if (eventData.events && eventData.events.length > 0) {
                for (const event of eventData.events) {
                    await this.processEvent(event);
                    this.lastEventId = event.id;
                }
            }
            
            // Aktualizuj status połączenia
            if (this.connectionStatus !== 'connected') {
                this.connectionStatus = 'connected';
                this.emit('connection_status', 'connected');
            }
            
        } catch (error) {
            console.error('❌ Event polling error:', error);
            this.connectionStatus = 'error';
            this.emit('connection_status', 'error');
        }
    }
    
    async processEvent(event) {
        const eventType = event.message_data?.type || event.event_type;
        const eventData = event.message_data || event.payload;
        
        // Sprawdź TTL dla chunków danych
        this.cleanupTTLChunks();
        
        // Zapisz event w TTL cache jeśli ma chunk_id
        if (eventData.chunk_id) {
            const ttl = Date.now() + (eventData.ttl || 300000); // Domyślnie 5 minut
            this.ttlChunks.set(eventData.chunk_id, {
                data: eventData,
                expires: ttl
            });
        }
        
        // Emituj event do handlera
        this.emit(eventType, eventData);
        
        console.log('📨 Event processed:', eventType);
    }
    
    cleanupTTLChunks() {
        const now = Date.now();
        for (const [chunkId, chunk] of this.ttlChunks.entries()) {
            if (now > chunk.expires) {
                this.ttlChunks.delete(chunkId);
            }
        }
    }
    
    startHeartbeat() {
        if (this.heartbeatInterval) return;
        
        this.heartbeatInterval = setInterval(async () => {
            await this.sendHeartbeat();
        }, 30000); // Heartbeat co 30 sekund
    }
    
    async sendHeartbeat() {
        if (!this.isAuthenticated) return;
        
        try {
            await fetch('/api/connection/heartbeat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.sessionData.session_token}`
                },
                body: JSON.stringify({
                    connection_ulid: this.connectionUlid
                })
            });
            
        } catch (error) {
            console.error('❌ Heartbeat error:', error);
        }
    }
    
    // Event handling
    on(eventType, handler) {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, []);
        }
        this.eventHandlers.get(eventType).push(handler);
    }
    
    off(eventType, handler) {
        if (this.eventHandlers.has(eventType)) {
            const handlers = this.eventHandlers.get(eventType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    emit(eventType, data) {
        if (this.eventHandlers.has(eventType)) {
            this.eventHandlers.get(eventType).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`❌ Event handler error for ${eventType}:`, error);
                }
            });
        }
    }
    
    // Specific event handlers
    handleConnectionEstablished(data) {
        console.log('🔗 Connection established:', data);
        this.connectionStatus = 'connected';
        this.emit('connection_status', 'connected');
    }
    
    handleConnectionClosed(data) {
        console.log('🔌 Connection closed:', data);
        this.cleanup();
    }
    
    handleLuxResponse(data) {
        console.log('🤖 Lux response:', data.message);
        this.emit('chat_message', {
            role: 'assistant',
            content: data.message,
            timestamp: data.timestamp
        });
    }
    
    handleNotification(data) {
        console.log('🔔 Notification:', data);
        
        // Pokaż notyfikację w UI
        this.showNotification(data.notification_type, data.message, data.priority);
    }
    
    handleStreamData(data) {
        console.log('🌊 Stream data:', data.stream_type);
        
        // Przetwórz streaming danych
        this.emit('data_stream', data);
    }
    
    handleBeingUpdate(data) {
        console.log('🧬 Being update:', data.being_ulid);
        
        // Aktualizuj UI dla tego bytu
        this.emit('being_changed', data);
    }
    
    // API Methods
    async sendLuxMessage(message) {
        if (!this.isAuthenticated) return false;
        
        try {
            await fetch('/api/events/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.sessionData.session_token}`
                },
                body: JSON.stringify({
                    event_type: 'lux_message',
                    user_ulid: this.userUlid,
                    payload: {
                        message: message
                    }
                })
            });
            
            // Dodaj wiadomość użytkownika do UI
            this.emit('chat_message', {
                role: 'user',
                content: message,
                timestamp: new Date().toISOString()
            });
            
            return true;
            
        } catch (error) {
            console.error('❌ Send message error:', error);
            return false;
        }
    }
    
    async requestDataStream(streamType, config = {}) {
        if (!this.isAuthenticated) return false;
        
        try {
            await fetch('/api/events/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.sessionData.session_token}`
                },
                body: JSON.stringify({
                    event_type: 'stream_request',
                    user_ulid: this.userUlid,
                    payload: {
                        stream_type: streamType,
                        config: config
                    }
                })
            });
            
            return true;
            
        } catch (error) {
            console.error('❌ Stream request error:', error);
            return false;
        }
    }
    
    showNotification(type, message, priority = 'normal') {
        // Implementuj pokazywanie notyfikacji w UI
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification notification-${priority}`;
        notificationElement.innerHTML = `
            <div class="notification-content">
                <strong>${type}</strong>
                <p>${message}</p>
            </div>
        `;
        
        document.body.appendChild(notificationElement);
        
        // Auto-remove po 5 sekundach
        setTimeout(() => {
            if (notificationElement.parentNode) {
                notificationElement.parentNode.removeChild(notificationElement);
            }
        }, 5000);
    }
    
    getConnectionStatus() {
        return {
            status: this.connectionStatus,
            authenticated: this.isAuthenticated,
            userUlid: this.userUlid,
            connectionUlid: this.connectionUlid,
            sessionData: this.sessionData
        };
    }
    
    getTTLData(chunkId) {
        const chunk = this.ttlChunks.get(chunkId);
        if (chunk && Date.now() <= chunk.expires) {
            return chunk.data;
        }
        return null;
    }
}

// Globalna instancja
window.commClient = new CommunicationClient();
