
// ===== LUX OS GRAPH - NAPRAWIONY ZOOM D3.js v7 =====

class LuxOSGraph {
    constructor() {
        this.socket = null;
        this.beings = [];
        this.relationships = [];
        this.selectedNodes = [];
        this.isConnected = false;
        this.zoomBehavior = null;
        this.svg = null;

        console.log('🌀 LuxDB Graph initialized');
        this.initializeConnection();
    }

    initializeConnection() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true
            });

            this.socket.on('connect', () => {
                this.isConnected = true;
                console.log('✅ Połączono z wszechświatem LuxOS');
                this.requestGraphData();
            });

            this.socket.on('disconnect', (reason) => {
                this.isConnected = false;
                console.log('Rozłączono ze wszechświatem:', reason);
                this.attemptReconnect();
            });

            this.socket.on('graph_data', (data) => {
                console.log('📊 Otrzymano dane grafu:', data);
                this.updateGraphData(data);
            });

        } catch (error) {
            console.error('❌ Błąd inicjalizacji połączenia:', error);
        }
    }

    requestGraphData() {
        if (this.socket && this.isConnected) {
            console.log('📡 Żądanie danych grafu...');
            this.socket.emit('request_graph_data');
        }
    }

    updateGraphData(data) {
        try {
            this.beings = data.beings || [];
            this.relationships = data.relationships || [];
            console.log(`🔗 Otrzymano ${this.relationships.length} relacji:`, this.relationships);
            this.renderUniverse();
        } catch (error) {
            console.error('❌ Błąd aktualizacji danych:', error);
        }
    }

    renderUniverse() {
        console.log(`🌌 Renderuję wszechświat z ${this.beings.length} bytami`);
        
        // Clear previous graph
        d3.select('#graph').selectAll('*').remove();
        
        const width = window.innerWidth;
        const height = window.innerHeight - 200;
        
        // Create SVG
        this.svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Create main group for all graph elements
        const g = this.svg.append('g').attr('class', 'main-group');

        // Zoom behavior - MUSI być przed dodaniem elementów
        this.zoomBehavior = d3.zoom()
            .scaleExtent([0.1, 5])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        // Apply zoom to SVG - KRYTYCZNE: musi być tutaj
        this.svg.call(this.zoomBehavior);
        
        // Store reference to main group
        this.mainGroup = g;
            
        // Add gradient definitions for beautiful nodes
        const defs = this.svg.append('defs');
        const gradient = defs.append('radialGradient')
            .attr('id', 'nodeGradient')
            .attr('cx', '30%')
            .attr('cy', '30%');
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#00ff88')
            .attr('stop-opacity', 1);
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#00cc66')
            .attr('stop-opacity', 0.8);
            
        // Create nodes data with beautiful positions
        const nodes = this.beings.map((being, i) => ({
            id: being.soul_uid || `node_${i}`,
            name: being._soul?.genesis?.name || `Being ${i}`,
            type: being._soul?.genesis?.type || 'unknown',
            x: width/2 + Math.cos(i * 2 * Math.PI / this.beings.length) * 200,
            y: height/2 + Math.sin(i * 2 * Math.PI / this.beings.length) * 200,
            being: being
        }));
        
        // Create links data
        const links = this.relationships.map(rel => ({
            source: rel.source_soul,
            target: rel.target_soul,
            type: rel.genesis?.type || 'connection',
            relation_type: rel.relation_type || 'unknown',
            strength: rel.strength || 0.5,
            metadata: rel.metadata || {}
        }));
        
        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width/2, height/2))
            .force('collision', d3.forceCollide().radius(40));
            
        // Draw links with different styles based on relationship type
        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'link')
            .style('stroke', d => {
                if (d.relation_type === 'similar_content') return '#00ff88';
                if (d.relation_type === 'communication') return '#ff8800';
                return '#555';
            })
            .style('stroke-width', d => {
                // Grubość linii zależna od siły relacji
                return Math.max(1, d.strength * 4);
            })
            .style('opacity', d => {
                // Przezroczystość zależna od siły relacji
                return Math.max(0.3, d.strength);
            })
            .style('stroke-dasharray', d => {
                // Różne style linii dla różnych typów relacji
                if (d.relation_type === 'similar_content') return '5,5';
                return 'none';
            });
            
        // Draw nodes with simple drag
        const node = g.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('class', 'node')
            .attr('r', 25)
            .style('fill', 'url(#nodeGradient)')
            .style('stroke', '#00ff88')
            .style('stroke-width', 2)
            .style('cursor', 'pointer')
            .call(d3.drag()
                .on('start', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                    event.sourceEvent?.stopPropagation();
                })
                .on('drag', (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on('end', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }));
            
        // Add relationship labels for similarity relations
        const relationLabels = g.append('g')
            .selectAll('text')
            .data(links.filter(d => d.relation_type === 'similar_content'))
            .enter().append('text')
            .attr('class', 'relation-label')
            .style('fill', '#00ff88')
            .style('font-size', '10px')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'none')
            .text(d => `${Math.round(d.strength * 100)}%`);

        // Add node labels
        const labels = g.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('class', 'node-label')
            .style('fill', '#ffffff')
            .style('font-size', '12px')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'none')
            .text(d => d.name);
            
        // Update positions on simulation tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
                
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
                
            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y + 5);
                
            relationLabels
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2 - 5);
        });
        
        console.log(`✨ Graf renderowany z ${nodes.length} węzłami i ${links.length} połączeniami!`);
    }

    attemptReconnect() {
        let attempts = 0;
        const maxAttempts = 5;

        const reconnect = () => {
            attempts++;
            if (attempts <= maxAttempts) {
                console.log(`Próba reconnect ${attempts}/${maxAttempts} za ${1000 * attempts}ms`);
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.socket.connect();
                    }
                }, 1000 * attempts);
            }
        };

        reconnect();
    }

    zoomIn() {
        console.log('🔍 Zoom In called');
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().duration(300).call(this.zoomBehavior.scaleBy, 1.5);
            console.log('✅ Zoom In executed');
        } else {
            console.error('❌ Zoom In failed - missing svg or zoomBehavior');
        }
    }

    zoomOut() {
        console.log('🔍 Zoom Out called');
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().duration(300).call(this.zoomBehavior.scaleBy, 0.67);
            console.log('✅ Zoom Out executed');
        } else {
            console.error('❌ Zoom Out failed - missing svg or zoomBehavior');
        }
    }

    resetZoom() {
        console.log('🔍 Reset Zoom called');
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().duration(500).call(
                this.zoomBehavior.transform,
                d3.zoomIdentity
            );
            console.log('✅ Reset Zoom executed');
        } else {
            console.error('❌ Reset Zoom failed - missing svg or zoomBehavior');
        }
    }

    resizeGraph() {
        console.log('📏 Resize graph');
        const width = window.innerWidth;
        const height = window.innerHeight - 200;
        
        if (this.svg) {
            this.svg
                .attr('width', width)
                .attr('height', height);
        }
        
        // Re-render the universe with new dimensions
        this.renderUniverse();
    }
}

console.log('✅ LuxOSGraph class defined and available globally');
window.LuxOSGraph = LuxOSGraph;
