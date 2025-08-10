
// ===== LUX REACTIVE COMPONENTS SYSTEM =====

class LuxComponents {
    constructor() {
        this.components = new Map();
        this.subscribers = new Map();
        this.state = {
            connections: 0,
            beings: 0,
            stats: {},
            graphData: { beings: [], relationships: [] },
            uiState: { zoom: 1.0, pan: { x: 0, y: 0 } }
        };
        this.socket = null;
        this.isInitialized = false;
        
        console.log('🧩 LuxComponents initialized');
    }

    init(socket) {
        this.socket = socket;
        this.setupSocketListeners();
        this.isInitialized = true;
        console.log('🔌 LuxComponents connected to socket');
    }

    setupSocketListeners() {
        if (!this.socket) return;

        this.socket.on('initial_state', (data) => {
            console.log('📦 Received initial state:', data);
            this.updateState(data.stats || {});
            this.updateGraphData(data.page_state?.graph_data || { beings: [], relationships: [] });
            this.notifySubscribers('initial_state', data);
        });

        this.socket.on('being_created', (data) => {
            console.log('🆕 Being created:', data);
            if (data.being) {
                this.state.graphData.beings.push(data.being);
            }
            this.updateState(data.stats || {});
            this.notifySubscribers('being_created', data);
            this.updateComponent('graphNodes', this.state.graphData.beings);
        });

        this.socket.on('user_count_update', (data) => {
            console.log('👥 User count update:', data);
            this.updateState({ connections: data.connections });
            this.updateComponent('connectionStatus', {
                connected: true,
                users: data.active_users,
                connections: data.connections
            });
        });

        this.socket.on('component_update', (data) => {
            console.log('🔄 Component update:', data);
            this.updateComponent(data.component_id, data.data);
        });

        this.socket.on('graph_data', (data) => {
            console.log('📊 Graph data received:', data);
            this.updateGraphData(data);
            this.notifySubscribers('graph_data', data);
        });

        this.socket.on('ui_state_update', (data) => {
            console.log('🎨 UI state update:', data);
            this.state.uiState = { ...this.state.uiState, ...data.ui_state };
            this.notifySubscribers('ui_state_update', data);
        });
    }

    updateState(newState) {
        this.state = { ...this.state, ...newState };
        this.updateComponent('statsContainer', this.state);
    }

    updateGraphData(graphData) {
        this.state.graphData = graphData;
        this.updateComponent('graphNodes', graphData.beings || []);
        this.notifySubscribers('graph_data_update', graphData);
    }

    subscribe(event, callback) {
        if (!this.subscribers.has(event)) {
            this.subscribers.set(event, new Set());
        }
        this.subscribers.get(event).add(callback);
        
        return () => {
            this.subscribers.get(event)?.delete(callback);
        };
    }

    notifySubscribers(event, data) {
        const callbacks = this.subscribers.get(event);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('❌ Subscriber callback error:', error);
                }
            });
        }
    }

    createComponent(containerId, componentType, renderFunction) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`⚠️ Container ${containerId} not found`);
            return;
        }

        const component = {
            id: containerId,
            type: componentType,
            container,
            render: renderFunction,
            data: null
        };

        this.components.set(containerId, component);
        console.log(`✅ Component ${containerId} created`);
    }

    updateComponent(componentId, data) {
        const component = this.components.get(componentId);
        if (component && component.render) {
            try {
                component.data = data;
                component.render(data);
            } catch (error) {
                console.error(`❌ Error updating component ${componentId}:`, error);
            }
        }
    }

    // Predefined component creators
    createConnectionComponent(containerId) {
        this.createComponent(containerId, 'connection', (data) => {
            const container = document.getElementById(containerId);
            if (container) {
                const status = data?.connected ? 'connected' : 'disconnected';
                const users = data?.users || 0;
                const connections = data?.connections || 0;
                
                container.innerHTML = `
                    <span class="user-info">👤 ${users} użytkowników</span>
                    <span class="connection-status ${status}">
                        ${status} (${connections} połączeń)
                    </span>
                `;
            }
        });
    }

    createStatsComponent(containerId) {
        this.createComponent(containerId, 'stats', (data) => {
            const container = document.getElementById(containerId);
            if (container) {
                const beings = data?.beings || 0;
                const connections = data?.connections || 0;
                
                container.innerHTML = `
                    <div class="stat-item">
                        <div class="stat-value">${beings}</div>
                        <div class="stat-label">Byty</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${connections}</div>
                        <div class="stat-label">Połączenia</div>
                    </div>
                `;
            }
        });
    }

    createListComponent(containerId, listType, itemRenderer) {
        this.createComponent(containerId, 'list', (data) => {
            const container = document.getElementById(containerId);
            if (container && Array.isArray(data)) {
                container.innerHTML = data.map(itemRenderer).join('');
            }
        });
    }

    createGraphComponent(containerId) {
        this.createComponent(containerId, 'graph', (data) => {
            // This will be handled by the graph system
            this.notifySubscribers('graph_update', data);
        });
    }

    // Utility methods
    emit(event, data) {
        if (this.socket) {
            this.socket.emit(event, data);
        } else {
            console.warn('⚠️ Socket not connected, cannot emit:', event);
        }
    }

    createBeing(name, type = 'entity') {
        this.emit('create_being', { name, type });
    }

    requestGraphData() {
        this.emit('request_graph_data');
    }

    updateUIState(uiState) {
        this.emit('update_ui_state', { ui_state: uiState });
    }

    selectNode(nodeId) {
        this.notifySubscribers('node_selected', { nodeId });
    }

    // Animation utilities
    animateValue(element, start, end, duration = 300) {
        const startTime = performance.now();
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const value = start + (end - start) * this.easeInOutQuad(progress);
            
            element.textContent = Math.floor(value);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    }

    easeInOutQuad(t) {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    // Responsive utilities
    onResize(callback) {
        window.addEventListener('resize', callback);
        return () => window.removeEventListener('resize', callback);
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Global instance
window.luxComponents = new LuxComponents();
console.log('✅ LuxComponents loaded globally');
