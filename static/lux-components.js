
// ===== LUX COMPONENTS - REACTIVE UI COMPONENTS =====

class LuxComponents {
    constructor(reactiveSystem) {
        this.reactive = reactiveSystem;
        this.components = new Map();
        
        console.log('🧩 LuxComponents initialized');
    }

    // Node Component - dla węzłów grafu
    createNodeComponent(nodeId, containerId) {
        const component = this.reactive.createRegionalComponent(
            containerId,
            ['nodes', 'selectedNodes'],
            (data) => {
                const [nodes, selectedNodes] = data;
                const node = nodes?.find(n => n.id === nodeId);
                
                if (!node) return '<div class="node-missing">Node not found</div>';
                
                const isSelected = selectedNodes?.includes(nodeId);
                
                return `
                    <div class="lux-node ${isSelected ? 'selected' : ''}" data-node-id="${nodeId}">
                        <div class="node-header">
                            <span class="node-type">${node.type || 'unknown'}</span>
                            <span class="node-id">${nodeId.substring(0, 8)}...</span>
                        </div>
                        <div class="node-content">
                            <h4>${node.name || 'Unnamed'}</h4>
                            ${node.data ? `<pre>${JSON.stringify(node.data, null, 2)}</pre>` : ''}
                        </div>
                        <div class="node-actions">
                            <button onclick="luxComponents.selectNode('${nodeId}')">Select</button>
                            <button onclick="luxComponents.editNode('${nodeId}')">Edit</button>
                        </div>
                    </div>
                `;
            },
            [nodeId] // dependencies
        );

        this.components.set(`node_${nodeId}`, component);
        return component;
    }

    // Stats Component - dla statystyk
    createStatsComponent(containerId) {
        return this.reactive.createRegionalComponent(
            containerId,
            ['stats', 'beings', 'relationships'],
            (data) => {
                const [stats, beings, relationships] = data;
                
                const beingsCount = beings?.length || 0;
                const relationshipsCount = relationships?.length || 0;
                
                return `
                    <div class="lux-stats">
                        <div class="stat-item">
                            <span class="stat-value">${beingsCount}</span>
                            <span class="stat-label">Beings</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${relationshipsCount}</span>
                            <span class="stat-label">Relationships</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${stats?.active_users || 0}</span>
                            <span class="stat-label">Active Users</span>
                        </div>
                    </div>
                `;
            }
        );
    }

    // List Component - dla list węzłów
    createListComponent(containerId, stateKey, itemRenderer) {
        return this.reactive.createRegionalComponent(
            containerId,
            [stateKey],
            (data) => {
                const [items] = data;
                
                if (!items || items.length === 0) {
                    return '<div class="empty-list">No items found</div>';
                }

                const itemsHtml = items.map(item => itemRenderer(item)).join('');
                
                return `
                    <div class="lux-list">
                        ${itemsHtml}
                    </div>
                `;
            }
        );
    }

    // Connection Status Component
    createConnectionComponent(containerId) {
        return this.reactive.createRegionalComponent(
            containerId,
            ['connectionStatus', 'sessionInfo'],
            (data) => {
                const [status, session] = data;
                
                const statusClass = status === 'connected' ? 'connected' : 'disconnected';
                const statusText = status === 'connected' ? 'Connected' : 'Disconnected';
                
                return `
                    <div class="connection-status ${statusClass}">
                        <div class="status-dot"></div>
                        <span class="status-text">${statusText}</span>
                        ${session ? `<span class="session-info">${session.user_name}</span>` : ''}
                    </div>
                `;
            }
        );
    }

    // Fragment dla pojedynczych węzłów w grafie
    createGraphNodeFragment(parentId, node) {
        const fragmentId = `node-fragment-${node.id}`;
        
        return this.reactive.createFragment(
            parentId,
            fragmentId,
            ['graphNodes'],
            (data) => {
                const [graphNodes] = data;
                const currentNode = graphNodes?.find(n => n.id === node.id);
                
                if (!currentNode) return ''; // Węzeł usunięty
                
                return `
                    <div class="graph-node" style="transform: translate(${currentNode.x}px, ${currentNode.y}px)">
                        <circle r="20" fill="${this.getNodeColor(currentNode.type)}"></circle>
                        <text dy="5" text-anchor="middle">${currentNode.name.substring(0, 8)}</text>
                    </div>
                `;
            }
        );
    }

    // Actions
    selectNode(nodeId) {
        const selectedNodes = this.reactive.getState('selectedNodes') || [];
        
        if (selectedNodes.includes(nodeId)) {
            // Deselect
            this.reactive.setState('selectedNodes', selectedNodes.filter(id => id !== nodeId));
        } else {
            // Select
            this.reactive.setState('selectedNodes', [...selectedNodes, nodeId]);
        }
    }

    editNode(nodeId) {
        console.log('🖊️ Editing node:', nodeId);
        // Implementacja edycji
    }

    // Utilities
    getNodeColor(type) {
        const colors = {
            'soul': '#ffd700',
            'being': '#4a90e2',
            'relation': '#8b5cf6',
            'entity': '#10b981'
        };
        return colors[type] || '#6b7280';
    }

    // Batch update - dla wielu zmian naraz
    batchUpdate(updates) {
        updates.forEach(update => {
            this.reactive.setState(update.key, update.value, true);
        });
    }

    // Update nodes efficiently - tylko zmienione węzły
    updateNodes(newNodes) {
        const oldNodes = this.reactive.getState('nodes') || [];
        const oldNodesMap = new Map(oldNodes.map(n => [n.id, n]));
        
        // Znajdź zmiany
        const added = [];
        const modified = [];
        const removed = [];

        newNodes.forEach(newNode => {
            const oldNode = oldNodesMap.get(newNode.id);
            if (!oldNode) {
                added.push(newNode);
            } else if (!this.reactive.deepEqual(oldNode, newNode)) {
                modified.push(newNode);
            }
        });

        const newNodesMap = new Map(newNodes.map(n => [n.id, n]));
        oldNodes.forEach(oldNode => {
            if (!newNodesMap.has(oldNode.id)) {
                removed.push(oldNode);
            }
        });

        console.log(`🔄 Nodes update: +${added.length} ~${modified.length} -${removed.length}`);

        // Ustaw nowy stan
        this.reactive.setState('nodes', newNodes);
        
        // Wyślij szczegółowe eventy dla efektów ubocznych
        if (added.length > 0) this.reactive.setState('nodesAdded', added);
        if (modified.length > 0) this.reactive.setState('nodesModified', modified);
        if (removed.length > 0) this.reactive.setState('nodesRemoved', removed);
    }
}

// Global instance
window.luxComponents = new LuxComponents(window.luxReactive);

console.log('✅ LuxComponents loaded globally');
