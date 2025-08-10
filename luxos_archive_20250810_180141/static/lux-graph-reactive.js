
// ===== LUX REACTIVE GRAPH SYSTEM =====

class LuxGraphReactive {
    constructor() {
        this.socket = null;
        this.graphData = { beings: [], relationships: [] };
        this.selectedNodes = new Set();
        this.subscribers = new Map();
        this.isInitialized = false;
        this.updateQueue = [];
        this.isProcessingQueue = false;
        
        console.log('📊 LuxGraphReactive initialized');
    }

    init(socket, luxComponents) {
        this.socket = socket;
        this.luxComponents = luxComponents;
        this.setupReactiveSubscriptions();
        this.setupSocketListeners();
        this.isInitialized = true;
        console.log('📊 LuxGraphReactive connected');
    }

    setupReactiveSubscriptions() {
        if (!this.luxComponents) return;

        // Subscribe to graph data updates
        this.luxComponents.subscribe('graph_data', (data) => {
            this.handleGraphDataUpdate(data);
        });

        this.luxComponents.subscribe('being_created', (data) => {
            this.handleBeingCreated(data);
        });

        this.luxComponents.subscribe('node_selected', (data) => {
            this.handleNodeSelection(data.nodeId);
        });
    }

    setupSocketListeners() {
        if (!this.socket) return;

        this.socket.on('graph_data', (data) => {
            console.log('📊 Graph data received in reactive system:', data);
            this.queueUpdate('graph_data', data);
        });

        this.socket.on('being_created', (data) => {
            console.log('🆕 Being created in reactive system:', data);
            this.queueUpdate('being_created', data);
        });
    }

    queueUpdate(type, data) {
        this.updateQueue.push({ type, data, timestamp: Date.now() });
        this.processQueue();
    }

    async processQueue() {
        if (this.isProcessingQueue || this.updateQueue.length === 0) {
            return;
        }

        this.isProcessingQueue = true;

        while (this.updateQueue.length > 0) {
            const update = this.updateQueue.shift();
            
            try {
                await this.processUpdate(update);
            } catch (error) {
                console.error('❌ Error processing update:', error);
            }

            // Small delay to prevent overwhelming the UI
            await new Promise(resolve => setTimeout(resolve, 10));
        }

        this.isProcessingQueue = false;
    }

    async processUpdate(update) {
        switch (update.type) {
            case 'graph_data':
                await this.updateGraphData(update.data);
                break;
            case 'being_created':
                await this.addBeing(update.data.being);
                break;
        }
    }

    async updateGraphData(data) {
        if (!data || !data.beings) return;

        const oldCount = this.graphData.beings.length;
        this.graphData = {
            beings: data.beings || [],
            relationships: data.relationships || []
        };

        const newCount = this.graphData.beings.length;

        console.log(`📊 Graph updated: ${oldCount} → ${newCount} beings`);

        // Notify subscribers
        this.notifySubscribers('graph_updated', {
            beings: this.graphData.beings,
            relationships: this.graphData.relationships,
            counts: { old: oldCount, new: newCount }
        });

        // Update global graph if available
        if (window.luxGraph && typeof window.luxGraph.updateGraph === 'function') {
            window.luxGraph.updateGraph(this.graphData);
        }

        // Animate count changes
        this.animateCountChange(oldCount, newCount);
    }

    async addBeing(being) {
        if (!being) return;

        // Check if being already exists
        const exists = this.graphData.beings.find(b => b.id === being.id);
        if (exists) return;

        this.graphData.beings.push(being);
        
        console.log('🆕 Being added to reactive graph:', being.name || being.id);

        // Notify subscribers
        this.notifySubscribers('being_added', being);

        // Update global graph
        if (window.luxGraph && typeof window.luxGraph.updateGraph === 'function') {
            window.luxGraph.updateGraph(this.graphData);
        }

        // Animate the addition
        this.animateBeingAddition(being);
    }

    handleNodeSelection(nodeId) {
        if (this.selectedNodes.has(nodeId)) {
            this.selectedNodes.delete(nodeId);
        } else {
            this.selectedNodes.add(nodeId);
        }

        this.notifySubscribers('selection_changed', {
            selectedNodes: Array.from(this.selectedNodes),
            nodeId
        });

        // Update visual selection
        this.updateNodeSelection(nodeId);
    }

    updateNodeSelection(nodeId) {
        // Find and highlight the node
        const nodes = document.querySelectorAll('.node');
        nodes.forEach(node => {
            const isSelected = node.dataset.nodeId === nodeId && this.selectedNodes.has(nodeId);
            node.classList.toggle('selected', isSelected);
        });
    }

    animateCountChange(oldCount, newCount) {
        const countElements = document.querySelectorAll('#nodesCount, .stat-value');
        countElements.forEach(element => {
            if (element.textContent == oldCount.toString()) {
                this.animateValue(element, oldCount, newCount);
            }
        });
    }

    animateBeingAddition(being) {
        // Create a temporary notification
        this.showNotification(`🆕 New being: ${being.name || being.id}`, 'success');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 6px;
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            font-weight: 500;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Auto remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    animateValue(element, start, end, duration = 500) {
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

    // Subscription system
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
                    console.error('❌ Reactive graph subscriber error:', error);
                }
            });
        }
    }

    // Public API methods
    requestGraphData() {
        if (this.socket) {
            this.socket.emit('request_graph_data');
        }
    }

    createBeing(name, type = 'entity') {
        if (this.socket) {
            this.socket.emit('create_being', { name, type });
        }
    }

    selectNode(nodeId) {
        this.handleNodeSelection(nodeId);
    }

    clearSelection() {
        this.selectedNodes.clear();
        this.notifySubscribers('selection_cleared', {});
        
        // Update visuals
        document.querySelectorAll('.node.selected').forEach(node => {
            node.classList.remove('selected');
        });
    }

    exportData() {
        console.log('💾 Exporting data');
        const data = {
            graphData: this.graphData,
            selectedNodes: Array.from(this.selectedNodes),
            timestamp: new Date().toISOString()
        };

        // Create download link
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `luxdb-graph-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);

        this.showNotification('📁 Graph data exported', 'success');
    }

    // Statistics
    getStats() {
        return {
            beings: this.graphData.beings.length,
            relationships: this.graphData.relationships.length,
            selectedNodes: this.selectedNodes.size,
            lastUpdate: this.lastUpdateTime || null
        };
    }
}

// Global instance
window.luxGraphReactive = new LuxGraphReactive();
console.log('✅ LuxGraphReactive loaded globally');
