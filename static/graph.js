// ===== LUX OS GRAPH - KOMPLETNY RESET =====
// Zero błędów składni, czysta implementacja

class LuxOSGraph {
    constructor() {
        this.socket = null;
        this.beings = [];
        this.relationships = [];
        this.selectedNodes = [];
        this.isConnected = false;

        console.log('🌀 LuxDB Graph initialized');
        this.initializeConnection();
    }

    initializeConnection() {
        try {
            this.socket = io();

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
            this.socket.emit('get_graph_data');
        }
    }

    updateGraphData(data) {
        try {
            this.beings = data.beings || [];
            this.relationships = data.relationships || [];
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
        
        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height);
            
        // Add gradient definitions for beautiful nodes
        const defs = svg.append('defs');
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
            type: rel.genesis?.type || 'connection'
        }));
        
        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width/2, height/2))
            .force('collision', d3.forceCollide().radius(40));
            
        // Draw links
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'link')
            .style('stroke', '#555')
            .style('stroke-width', 2)
            .style('opacity', 0.6);
            
        // Draw nodes
        const node = svg.append('g')
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
                })
                .on('drag', (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on('end', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }))
            .on('click', (event, d) => {
                console.log('🎯 Kliknięto węzeł:', d.name);
                // Add selection logic here
            });
            
        // Add node labels
        const labels = svg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('class', 'node-label')
            .style('fill', '#ffffff')
            .style('font-size', '12px')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'none')
            .text(d => d.name);
            
        // Add beautiful pulsing animation
        node.append('animate')
            .attr('attributeName', 'r')
            .attr('values', '25;30;25')
            .attr('dur', '2s')
            .attr('repeatCount', 'indefinite');
            
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
        console.log('🔍 Zoom in');
    }

    zoomOut() {
        console.log('🔍 Zoom out');
    }

    resetZoom() {
        console.log('🔍 Reset zoom');
    }

    resizeGraph() {
        console.log('📏 Resize graph');
        const width = window.innerWidth;
        const height = window.innerHeight - 200;
        
        d3.select('#graph svg')
            .attr('width', width)
            .attr('height', height);
            
        // Re-render the universe with new dimensions
        this.renderUniverse();
    }
}

console.log('✅ LuxOSGraph class defined and available globally');
window.LuxOSGraph = LuxOSGraph;