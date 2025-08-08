
// ===== LUX GRAPH REACTIVE - SELECTIVE GRAPH RENDERING =====

class LuxGraphReactive {
    constructor() {
        this.reactive = window.luxReactive;
        this.components = window.luxComponents;
        this.svg = null;
        this.simulation = null;
        
        // Initialize state
        this.reactive.createState('graphNodes', []);
        this.reactive.createState('graphLinks', []);
        this.reactive.createState('selectedNodes', []);
        this.reactive.createState('graphViewport', { x: 0, y: 0, scale: 1 });
        
        console.log('📊 LuxGraphReactive initialized');
    }

    initialize(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`❌ Container ${containerId} not found`);
            return;
        }

        // Create SVG
        this.svg = d3.select(`#${containerId}`)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%');

        this.setupZoom();
        this.setupReactiveRendering();
        
        console.log('✅ Graph reactive system ready');
    }

    setupZoom() {
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                const { x, y, k } = event.transform;
                this.reactive.setState('graphViewport', { x, y, scale: k });
            });

        this.svg.call(zoom);
    }

    setupReactiveRendering() {
        // Subscribe to node changes - render only changed nodes
        this.reactive.subscribe(['graphNodes'], () => {
            this.renderNodes();
        });

        // Subscribe to link changes - render only changed links
        this.reactive.subscribe(['graphLinks'], () => {
            this.renderLinks();
        });

        // Subscribe to selection changes - update styles only
        this.reactive.subscribe(['selectedNodes'], () => {
            this.updateSelectionStyles();
        });

        // Subscribe to viewport changes - update transform only
        this.reactive.subscribe(['graphViewport'], () => {
            this.updateViewport();
        });
    }

    renderNodes() {
        const nodes = this.reactive.getState('graphNodes') || [];
        
        // Data join with key function for efficient updates
        const nodeSelection = this.svg.selectAll('.graph-node')
            .data(nodes, d => d.id);

        // Remove old nodes
        nodeSelection.exit()
            .transition()
            .duration(300)
            .style('opacity', 0)
            .remove();

        // Add new nodes
        const nodeEnter = nodeSelection.enter()
            .append('g')
            .attr('class', 'graph-node')
            .style('opacity', 0);

        nodeEnter.append('circle')
            .attr('r', 20)
            .attr('fill', d => this.components.getNodeColor(d.type));

        nodeEnter.append('text')
            .attr('dy', 5)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', 'white')
            .text(d => d.name ? d.name.substring(0, 8) : d.id.substring(0, 8));

        // Update existing nodes
        const nodeUpdate = nodeEnter.merge(nodeSelection);

        nodeUpdate
            .transition()
            .duration(300)
            .style('opacity', 1)
            .attr('transform', d => `translate(${d.x || 0}, ${d.y || 0})`);

        // Update circle colors for type changes
        nodeUpdate.select('circle')
            .transition()
            .duration(300)
            .attr('fill', d => this.components.getNodeColor(d.type));

        // Update text
        nodeUpdate.select('text')
            .text(d => d.name ? d.name.substring(0, 8) : d.id.substring(0, 8));

        console.log(`🔄 Rendered ${nodes.length} nodes`);
    }

    renderLinks() {
        const links = this.reactive.getState('graphLinks') || [];
        
        const linkSelection = this.svg.selectAll('.graph-link')
            .data(links, d => `${d.source}-${d.target}`);

        // Remove old links
        linkSelection.exit()
            .transition()
            .duration(300)
            .style('opacity', 0)
            .remove();

        // Add new links
        const linkEnter = linkSelection.enter()
            .append('line')
            .attr('class', 'graph-link')
            .style('stroke', '#666')
            .style('stroke-width', 2)
            .style('opacity', 0);

        // Update existing links
        const linkUpdate = linkEnter.merge(linkSelection);

        linkUpdate
            .transition()
            .duration(300)
            .style('opacity', 0.6)
            .attr('x1', d => d.source.x || 0)
            .attr('y1', d => d.source.y || 0)
            .attr('x2', d => d.target.x || 0)
            .attr('y2', d => d.target.y || 0);

        console.log(`🔗 Rendered ${links.length} links`);
    }

    updateSelectionStyles() {
        const selectedNodes = this.reactive.getState('selectedNodes') || [];
        
        this.svg.selectAll('.graph-node')
            .classed('selected', d => selectedNodes.includes(d.id))
            .select('circle')
            .transition()
            .duration(200)
            .attr('stroke', d => selectedNodes.includes(d.id) ? '#00ff88' : 'none')
            .attr('stroke-width', d => selectedNodes.includes(d.id) ? 3 : 0);

        console.log(`🎯 Updated selection for ${selectedNodes.length} nodes`);
    }

    updateViewport() {
        const viewport = this.reactive.getState('graphViewport');
        if (!viewport) return;

        this.svg.select('.main-group')
            .transition()
            .duration(200)
            .attr('transform', `translate(${viewport.x}, ${viewport.y}) scale(${viewport.scale})`);
    }

    // Update graph data efficiently
    updateGraphData(newData) {
        if (newData.beings) {
            // Convert beings to nodes
            const nodes = newData.beings.map((being, i) => ({
                id: being.id || being.ulid,
                name: being.name || 'Unknown',
                type: being._soul?.genesis?.type || 'entity',
                x: being.x || Math.random() * 800,
                y: being.y || Math.random() * 600,
                data: being
            }));

            this.components.updateNodes(nodes);
            this.reactive.setState('graphNodes', nodes);
        }

        if (newData.relationships) {
            // Convert relationships to links
            const links = newData.relationships.map(rel => ({
                source: rel.source_uid || rel.source,
                target: rel.target_uid || rel.target,
                type: rel.relation_type || rel.type,
                data: rel
            }));

            this.reactive.setState('graphLinks', links);
        }
    }

    // Add single node (for real-time updates)
    addNode(node) {
        const currentNodes = this.reactive.getState('graphNodes') || [];
        const newNodes = [...currentNodes, node];
        this.reactive.setState('graphNodes', newNodes);
    }

    // Remove single node
    removeNode(nodeId) {
        const currentNodes = this.reactive.getState('graphNodes') || [];
        const newNodes = currentNodes.filter(n => n.id !== nodeId);
        this.reactive.setState('graphNodes', newNodes);
    }

    // Update single node
    updateNode(nodeId, updates) {
        const currentNodes = this.reactive.getState('graphNodes') || [];
        const newNodes = currentNodes.map(node => 
            node.id === nodeId ? { ...node, ...updates } : node
        );
        this.reactive.setState('graphNodes', newNodes);
    }
}

// Global instance
window.luxGraphReactive = new LuxGraphReactive();

console.log('✅ LuxGraphReactive loaded globally');
