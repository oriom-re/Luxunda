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
                    console.log('✅ Validating beings data:', data.beings.slice(0, 3)); // Show first 3 for debug

                    // Store relationships first
                    if (data.relationships && Array.isArray(data.relationships)) {
                        this.relationships = data.relationships.map(rel => ({
                            source_uid: rel.source_uid || rel.source_soul,
                            target_uid: rel.target_uid || rel.target_soul,
                            relation_type: rel.relation_type || rel.type || 'connection',
                            strength: rel.strength || rel.metadata?.strength || 0.5,
                            metadata: rel.metadata || {}
                        }));
                        console.log('🔗 Processed relationships:', this.relationships);
                    } else {
                        this.relationships = [];
                    }

                    // Store beings and render immediately
                    this.beings = data.beings;
                    console.log(`🚀 Calling renderUniverse with ${data.beings.length} beings`);
                    this.renderUniverse(data.beings);
                } else {
                    console.log('❌ Invalid beings data received:', data.beings);
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
                // Store relationships for later use
                this.relationships = data.relationships || [];
                console.log("🔗 Relationships data:", this.relationships);

                // Render universe with beings
                this.renderUniverse(data.beings);
            }
        } catch (error) {
            console.error("❌ Błąd aktualizacji danych:", error);
            console.error("Error details:", error.message, error.stack);
        }
    }

    renderUniverse(beings) {
        console.log(`🌌 Renderuję wszechświat z ${beings ? beings.length : 0} bytami`);
        console.log(`📊 Raw beings data:`, beings);

        // Store beings for later use
        this.beings = beings || [];

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

        // Debug beings structure
        console.log('🔍 First being structure:', beings[0]);
        console.log('🔍 Being types found:', beings.map(b => b._soul?.genesis?.type).filter((v, i, a) => a.indexOf(v) === i));

        // Filter beings - separate relation beings for links, but keep them in nodes for potential interaction
        const actualBeings = beings.filter(being => {
            const hasUlid = being.ulid;
            console.log(`🔍 Being ${being.ulid}: hasUlid=${hasUlid}, type=${being._soul?.genesis?.type}`);
            return hasUlid; // Just ensure it has a ULID - show all beings including relations
        });

        const relationBeings = beings.filter(being =>
            being._soul?.genesis?.type === 'relation' && being.ulid // Keep relation beings for creating links
        );

        console.log(`📊 Filtered: ${actualBeings.length} actualBeings, ${relationBeings.length} relationBeings`);

        // Create nodes data with beautiful positions and type distinction
        const nodes = actualBeings.map((being, i) => {
            // Detect Soul vs Being vs Relation
            const hasAlias = being._soul?.alias;
            const genesisType = being._soul?.genesis?.type;
            const hasAttributes = being.attributes && Object.keys(being.attributes).length > 0;
            
            // Soul detection: has alias AND (no genesis type OR genesis type is undefined) AND not a relation
            const isSoul = hasAlias && (!genesisType || genesisType === undefined) && genesisType !== 'relation';
            
            // Relation detection: explicit relation type
            const isRelation = genesisType === 'relation';
            
            console.log(`🔍 Node analysis: ${being.ulid}:`, {
                alias: hasAlias ? being._soul.alias : 'NO_ALIAS',
                genesisType: genesisType || 'UNDEFINED',
                hasAttributes,
                isSoul,
                isRelation,
                attributesCount: being.attributes ? Object.keys(being.attributes).length : 0
            });

            return {
                id: being.ulid,
                x: width/2 + Math.cos(i * 2 * Math.PI / actualBeings.length) * 200,
                y: height/2 + Math.sin(i * 2 * Math.PI / actualBeings.length) * 200,
                being: being,
                vx: 0,
                vy: 0,
                type: isSoul ? 'soul' : (isRelation ? 'relation' : 'being'),
                isSoul: isSoul,
                isRelation: isRelation
            };
        });

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

        // Create nodes with type-specific styling
        const node = g.append('g')
            .selectAll('.node')
            .data(nodes)
            .enter().append('g')
            .attr('class', d => `node ${d.type}`)
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
                })
            );

        // Add shapes based on node type
        node.each(function(d) {
            const nodeElement = d3.select(this);

            if (d.isSoul) {
                // Souls - Diamond shape, gold color
                nodeElement.append('rect')
                    .attr('width', 30)
                    .attr('height', 30)
                    .attr('x', -15)
                    .attr('y', -15)
                    .attr('transform', 'rotate(45)')
                    .style('fill', '#ffd700')
                    .style('stroke', '#b8860b')
                    .style('stroke-width', 3)
                    .style('filter', 'url(#glow)');

                // Soul icon
                nodeElement.append('text')
                    .attr('text-anchor', 'middle')
                    .attr('dy', '0.35em')
                    .style('font-size', '16px')
                    .style('fill', '#b8860b')
                    .style('font-weight', 'bold')
                    .text('♦');

            } else if (d.isRelation) {
                // Relations - Hexagon, purple color
                const hexagon = "M0,-20 L17.32,-10 L17.32,10 L0,20 L-17.32,10 L-17.32,-10 Z";
                nodeElement.append('path')
                    .attr('d', hexagon)
                    .style('fill', '#8b5cf6')
                    .style('stroke', '#5b21b6')
                    .style('stroke-width', 2)
                    .style('filter', 'url(#glow)');

                // Relation icon
                nodeElement.append('text')
                    .attr('text-anchor', 'middle')
                    .attr('dy', '0.35em')
                    .style('font-size', '14px')
                    .style('fill', 'white')
                    .style('font-weight', 'bold')
                    .text('⟷');

            } else {
                // Beings - Circle, blue color
                nodeElement.append('circle')
                    .attr('r', 22)
                    .style('fill', '#4a90e2')
                    .style('stroke', '#2c5282')
                    .style('stroke-width', 2)
                    .style('filter', 'url(#glow)');

                // Being icon
                nodeElement.append('text')
                    .attr('text-anchor', 'middle')
                    .attr('dy', '0.35em')
                    .style('font-size', '16px')
                    .style('fill', 'white')
                    .style('font-weight', 'bold')
                    .text('●');
            }
        });

        // Add labels to nodes with type indicators
        node.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 35)
            .style('font-size', '11px')
            .style('fill', d => d.isSoul ? '#b8860b' : (d.isRelation ? '#5b21b6' : '#2c5282'))
            .style('font-weight', 'bold')
            .text(d => {
                const being = d.being;
                let prefix = '';
                let label = '';

                if (d.isSoul) {
                    prefix = '♦ SOUL: ';
                    // For souls, prioritize alias
                    label = being._soul?.alias || 'Unknown Soul';
                } else if (d.isRelation) {
                    prefix = '⟷ REL: ';
                    // For relations, show relation type if available
                    label = being.attributes?.relation_type || 'Relation';
                } else {
                    prefix = '● BEING: ';
                    // For beings, show name or alias
                    label = being.attributes?.name || being._soul?.alias || (being.ulid ? being.ulid.substring(0, 8) + '...' : 'Unknown');
                }

                return prefix + label;
            });

        // Add type label below main label
        node.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 48)
            .style('font-size', '9px')
            .style('fill', '#666')
            .style('font-style', 'italic')
            .text(d => {
                if (d.isSoul) return 'Soul';
                if (d.isRelation) return 'Relation';
                return 'Being';
            });

        // Update positions on simulation tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('transform', d => `translate(${d.x}, ${d.y})`);

            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y + 5);

            relationLabels
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2 - 5);
        });

        // Add title
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', 30)
            .attr('text-anchor', 'middle')
            .style('font-size', '24px')
            .style('font-weight', 'bold')
            .style('fill', '#333')
            .text('🌌 Universe Graph');

        // Add legend
        const legend = svg.append('g')
            .attr('class', 'legend')
            .attr('transform', 'translate(20, 60)');

        const legendData = [
            { type: 'soul', label: 'Soul (Genotype/Template)', color: '#ffd700', shape: 'diamond', icon: '♦' },
            { type: 'being', label: 'Being (Data Instance)', color: '#4a90e2', shape: 'circle', icon: '●' },
            { type: 'relation', label: 'Relation (Connection)', color: '#8b5cf6', shape: 'hexagon', icon: '⟷' }
        ];

        const legendItems = legend.selectAll('.legend-item')
            .data(legendData)
            .enter().append('g')
            .attr('class', 'legend-item')
            .attr('transform', (d, i) => `translate(0, ${i * 25})`);

        legendItems.each(function(d) {
            const item = d3.select(this);

            if (d.shape === 'diamond') {
                item.append('rect')
                    .attr('width', 12)
                    .attr('height', 12)
                    .attr('x', -6)
                    .attr('y', -6)
                    .attr('transform', 'rotate(45)')
                    .style('fill', d.color)
                    .style('stroke', '#666')
                    .style('stroke-width', 1);
            } else if (d.shape === 'hexagon') {
                const hexagon = "M0,-8 L6.93,-4 L6.93,4 L0,8 L-6.93,4 L-6.93,-4 Z";
                item.append('path')
                    .attr('d', hexagon)
                    .style('fill', d.color)
                    .style('stroke', '#666')
                    .style('stroke-width', 1);
            } else {
                item.append('circle')
                    .attr('r', 8)
                    .style('fill', d.color)
                    .style('stroke', '#666')
                    .style('stroke-width', 1);
            }

            item.append('text')
                .attr('x', 20)
                .attr('y', 0)
                .attr('dy', '0.35em')
                .style('font-size', '12px')
                .style('fill', '#333')
                .text(`${d.icon} ${d.label}`);
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