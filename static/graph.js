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

            // Setup socket listeners
            this.socket.on('graph_data', (data) => {
                console.log('📊 Otrzymano dane grafu:', data);
                console.log('📊 Beings count:', data.beings ? data.beings.length : 'no beings');
                console.log('📊 Relationships count:', data.relationships ? data.relationships.length : 'no relationships');

                if (data && data.beings && Array.isArray(data.beings)) {
                    this.renderUniverse(data.beings);
                } else {
                    console.log('❌ Invalid beings data received:', data.beings);
                }

                if (data && data.relationships && Array.isArray(data.relationships)) {
                    this.updateRelationships(data.relationships);
                } else {
                    console.log('❌ Invalid relationships data received:', data.relationships);
                }
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

    updateRelationships(relationships) {
        console.log('🔗 Otrzymano tradycyjne relacje:', relationships);
        this.relationships = relationships.map(rel => ({
            source_uid: rel.source_uid || rel.source_soul,
            target_uid: rel.target_uid || rel.target_soul,
            relation_type: rel.relation_type || rel.type || 'connection',
            strength: rel.strength || rel.metadata?.strength || 0.5,
            metadata: rel.metadata || {}
        }));
        // Refresh the graph with updated relationships
        this.renderUniverse(this.beings);
    }


    updateGraphData(data) {
        try {
            console.log("📊 Otrzymano dane grafu:", data);

            if (data.beings) {
                const relationships = data.relationships || [];
                console.log("🔗 Relationships data:", relationships);

                // Map relationships to D3.js format
                const mappedRelationships = relationships.map(rel => ({
                    source: rel.source_uid || rel.source_soul,
                    target: rel.target_uid || rel.target_soul,
                    strength: rel.strength || rel.metadata?.strength || 0.5,
                    type: rel.relation_type || rel.type || 'connection'
                }));

                console.log("🔗 Mapped relationships:", mappedRelationships);
                this.renderUniverse(data.beings, mappedRelationships);
            }
        } catch (error) {
            console.error("❌ Błąd aktualizacji danych:", error);
            console.error("Error details:", error.message, error.stack);
        }
    }

    renderUniverse(beings) {
        console.log(`🌌 Renderuję wszechświat z ${beings ? beings.length : 0} bytami`);
        console.log(`📊 Raw beings data:`, beings);
        
        // Debug being types
        if (beings && beings.length > 0) {
            const types = beings.map(b => b._soul?.genesis?.type || 'unknown');
            console.log(`📋 Being types:`, types);
            console.log(`📊 Type counts:`, types.reduce((acc, type) => {
                acc[type] = (acc[type] || 0) + 1;
                return acc;
            }, {}));
        }

        // Clear existing nodes and links
        this.nodes = [];
        this.links = [];

        // Ensure beings is an array
        if (!beings || !Array.isArray(beings)) {
            console.log(`❌ Beings data is not valid array:`, beings);
            return;
        }

        // Process beings into nodes
        beings.forEach((being, index) => {
            console.log(`🔍 Processing being ${index}:`, being);
        });


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

        // Zoom behavior - MUST be before adding elements
        this.zoomBehavior = d3.zoom()
            .scaleExtent([0.1, 5])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        // Apply zoom to SVG - CRITICAL: must be here
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

        // Filter beings - separate relation beings for links, but keep them in nodes for potential interaction
        const actualBeings = beings.filter(being =>
            being.ulid // Just ensure it has a ULID - show all beings including relations
        );

        const relationBeings = beings.filter(being =>
            being._soul?.genesis?.type === 'relation' && being.ulid // Keep relation beings for creating links
        );

        // Create nodes data with beautiful positions
        const nodes = actualBeings.map((being, i) => ({
            id: being.ulid,  // Use ulid as node ID
            name: being._soul?.genesis?.name || `Being ${i}`,
            type: being._soul?.genesis?.type || 'unknown',
            x: width/2 + Math.cos(i * 2 * Math.PI / actualBeings.length) * 200,
            y: height/2 + Math.sin(i * 2 * Math.PI / actualBeings.length) * 200,
            being: being
        }));

        // Store the processed nodes for later use (e.g., updating relationships)
        this.nodes = nodes;

        // Create links data from both relation beings and relationships
        const links = [];

        console.log(`🔗 Przetwarzam ${relationBeings.length} bytów relacji i ${this.relationships.length} tradycyjnych relacji`);

        // Add links from relation beings
        relationBeings.forEach(relationBeing => {
            const attrs = relationBeing.attributes || {};
            const sourceUid = attrs.source_uid;
            const targetUid = attrs.target_uid;

            if (sourceUid && targetUid) {
                const sourceExists = nodes.find(n => n.id === sourceUid);
                const targetExists = nodes.find(n => n.id === targetUid);

                if (sourceExists && targetExists) {
                    links.push({
                        source: sourceUid,
                        target: targetUid,
                        type: 'relation_being',
                        relation_type: attrs.relation_type || 'connection',
                        strength: parseFloat(attrs.strength) || 0.5,
                        metadata: attrs.metadata || {},
                        being: relationBeing // Keep the relation being itself for context
                    });
                    console.log(`✅ Dodano link z bytu relacji: ${sourceUid} -> ${targetUid}`);
                } else {
                    console.log(`⚠️ Nie znaleziono węzłów dla relacji z bytu: ${sourceUid} -> ${targetUid}`);
                }
            }
        });

        // Add links from traditional relationships
        this.relationships.forEach(rel => {
            const sourceExists = nodes.find(n => n.id === rel.source_uid);
            const targetExists = nodes.find(n => n.id === rel.target_uid);

            if (sourceExists && targetExists) {
                links.push({
                    source: rel.source_uid,
                    target: rel.target_uid,
                    type: rel.genesis?.type || 'connection', // Use genesis type if available, fallback to 'connection'
                    relation_type: rel.relation_type || 'unknown',
                    strength: parseFloat(rel.strength) || 0.5,
                    metadata: rel.metadata || {}
                });
                console.log(`✅ Dodano link z relationships: ${rel.source_uid} -> ${rel.target_uid}`);
            } else {
                 console.log(`⚠️ Nie znaleziono węzłów dla relacji z relationships: ${rel.source_uid} -> ${rel.target_uid}`);
            }
        });

        // Store the processed links for later use
        this.links = links;

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
                if (d.type === 'relation_being') return '#00ccff'; // Blue for relation beings
                return '#555';
            })
            .style('stroke-width', d => {
                // Line thickness dependent on relationship strength
                return Math.max(2, d.strength * 5);
            })
            .style('opacity', d => {
                // Opacity dependent on relationship strength
                return Math.max(0.4, d.strength);
            })
            .style('stroke-dasharray', d => {
                // Different line styles for different relationship types
                if (d.relation_type === 'similar_content') return '5,5';
                if (d.type === 'relation_being') return '3,3';
                return 'none';
            })
            .on('mouseover', function(event, d) {
                // Highlight line on hover
                d3.select(this).style('stroke-width', Math.max(4, d.strength * 6));
            })
            .on('mouseout', function(event, d) {
                // Restore normal thickness
                d3.select(this).style('stroke-width', Math.max(2, d.strength * 5));
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

        // Add relationship labels for all relations
        const relationLabels = g.append('g')
            .selectAll('text')
            .data(links)
            .enter().append('text')
            .attr('class', 'relation-label')
            .style('fill', d => {
                if (d.type === 'relation_being') return '#00ccff';
                if (d.relation_type === 'similar_content') return '#00ff88';
                return '#fff';
            })
            .style('font-size', '9px')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'none')
            .text(d => {
                if (d.type === 'relation_being') {
                    return `${d.relation_type} (${Math.round(d.strength * 100)}%)`;
                }
                return `${Math.round(d.strength * 100)}%`;
            });

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
        console.log(`🔗 Znaleziono ${relationBeings.length} bytów relacji i ${this.relationships.length} tradycyjnych relacji`);
        console.log('📋 Szczegóły linków:', links.map(l => `${l.source} -> ${l.target} (${l.relation_type})`));
        console.log('📋 Dostępne węzły:', nodes.map(n => `${n.id} (${n.name})`));
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
        this.renderUniverse(this.beings); // Pass this.beings to re-render
    }
}

console.log('✅ LuxOSGraph class defined and available globally');
window.LuxOSGraph = LuxOSGraph;