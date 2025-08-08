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
        this.lastData = null; // Store last data for resize operations
        this.connectionStatus = 'disconnected';
        this.reconnectAttempts = 0;
        this.heartbeatInterval = null;
        this.width = window.innerWidth; // Initialize width
        this.height = window.innerHeight - 200; // Initialize height

        // Session management
        this.sessionId = null;
        this.userName = 'Guest';
        this.isAdmin = false;

        console.log('🌀 LuxDB Graph initialized');
        this.loadSessionFromCookie();
        this.initializeConnection();
    }

    loadSessionFromCookie() {
        // Pobierz session_id z cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'session_id') {
                this.sessionId = value;
                console.log('🍪 Znaleziono session_id w cookie:', this.sessionId.substring(0, 8) + '...');
                break;
            }
        }
    }

    updateSessionUI() {
        // Zaktualizuj UI z informacją o sesji
        const sessionInfo = document.getElementById('sessionInfo');
        if (sessionInfo) {
            sessionInfo.innerHTML = `
                <span class="user-info">👤 ${this.userName} ${this.isAdmin ? '(Admin)' : ''}</span>
                <span class="connection-status ${this.connectionStatus}">${this.connectionStatus}</span>
            `;
        }
    }

    initializeConnection() {
        try {
            // Przygotuj auth object z session_id
            const auth = this.sessionId ? { session_id: this.sessionId } : {};

            // Initialize Socket.IO with robust reconnection and session support
            this.socket = io({
                auth: auth,
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                maxReconnectionAttempts: 10,
                timeout: 20000,
                pingTimeout: 60000,
                pingInterval: 25000
            });

            this.socket.on('connect', () => {
                console.log('✅ Połączono z LuxDB Gaming Server');
                this.connectionStatus = 'connected';
                this.reconnectAttempts = 0;
                this.requestGraphData();
                this.startHeartbeat();
                this.updateSessionUI();
            });

            // Session events
            this.socket.on('session_established', (data) => {
                console.log('🔐 Sesja nawiązana:', data);
                this.sessionId = data.session_id;
                this.userName = data.user_name;
                this.isAdmin = data.is_admin;

                // Zapisz session_id do cookie jeśli jest nowe
                if (data.session_id !== this.getCookieValue('session_id')) {
                    document.cookie = `session_id=${data.session_id}; max-age=${30*24*60*60}; path=/; samesite=lax`;
                }

                this.updateSessionUI();
                this.showNotification(`Zalogowano jako ${this.userName}`, 'success');
            });

            this.socket.on('disconnect', (reason) => {
                console.log('💔 Rozłączono z LuxDB Gaming Server:', reason);
                this.connectionStatus = 'disconnected';
                this.stopHeartbeat();
            });

            this.socket.on('connect_error', (error) => {
                console.log('❌ Błąd połączenia:', error);
                this.connectionStatus = 'error';
            });

            this.socket.on('reconnect', (attemptNumber) => {
                console.log(`🔄 Ponownie połączono po ${attemptNumber} próbach`);
                this.connectionStatus = 'connected';
                this.requestGraphData();
            });

            this.socket.on('reconnect_attempt', (attemptNumber) => {
                console.log(`🔄 Próba ponownego połączenia: ${attemptNumber}`);
                this.reconnectAttempts = attemptNumber;
            });

            this.socket.on('reconnect_error', (error) => {
                console.log('❌ Błąd ponownego połączenia:', error);
            });

            this.socket.on('reconnect_failed', () => {
                console.log('❌ Nie udało się ponownie połączyć');
                this.connectionStatus = 'failed';
            });

            // Handle pong responses
            this.socket.on('pong', (data) => {
                // Silent ping-pong handling
            });

            // Setup socket listeners
            this.socket.on('graph_data', (data) => {
                console.log('📊 Otrzymano dane grafu:', data);

                // Sprawdź czy mamy jakiekolwiek dane
                if (!data || typeof data !== 'object') {
                    console.log('❌ Nieprawidłowe dane:', data);
                    return;
                }

                const beings = data.beings || [];
                const relationships = data.relationships || [];
                const relations = data.relations || [];
                const nodes = data.nodes || [];
                const links = data.links || [];

                console.log('📊 Beings count:', beings.length);
                console.log('📊 Relationships count:', relationships.length);
                console.log('📊 Relations count:', relations.length);
                console.log('📊 Nodes count:', nodes.length);
                console.log('📊 Links count:', links.length);

                // Store last data for resize
                this.lastData = data;

                // Jeśli mamy bezpośrednio nodes i links, użyj ich
                if (nodes.length > 0) {
                    console.log('✅ Używam gotowych nodes i links');
                    this.updateGraphData({ beings: nodes, relationships: links });
                    return;
                }

                // Jeśli mamy beings/relationships, skonwertuj je
                if (beings.length > 0 || relationships.length > 0) {
                    console.log('✅ Konwertuję beings i relationships');
                    this.updateGraphData(data);
                    return;
                }

                console.log('❌ Brak danych do wyświetlenia');
            });

        } catch (error) {
            console.error('❌ Błąd inicjalizacji połączenia:', error);
        }
    }

    getCookieValue(name) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [cookieName, cookieValue] = cookie.trim().split('=');
            if (cookieName === name) {
                return cookieValue;
            }
        }
        return null;
    }

    showNotification(message, type = 'info') {
        // Prosty system notyfikacji
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 4px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    requestGraphData() {
        console.log('📡 Żądanie danych grafu...');
        this.socket.emit('request_graph_data');
    }

    startHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }

        this.heartbeatInterval = setInterval(() => {
            if (this.socket.connected) {
                this.socket.emit('ping');
            }
        }, 30000); // Ping every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
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

    getTestData() {
        // Dummy data for testing purposes if no data is received
        console.log("🧪 Używam danych testowych.");
        return {
            beings: [
                { id: 'test-being-1', ulid: 'test-ulid-1', name: 'Test Being 1', _soul: { alias: 'sample_entity', genesis: { type: 'test' } } },
                { id: 'test-being-2', ulid: 'test-ulid-2', name: 'Test Being 2', _soul: { alias: 'sample_entity', genesis: { type: 'test' } } }
            ],
            relationships: [
                { source_uid: 'test-ulid-1', target_uid: 'test-ulid-2', relation_type: 'connected', strength: 0.8 }
            ]
        };
    }

    renderUniverse(beings) {
        console.log("🌌 Renderuję wszechświat z", beings?.length || 0, "beings");

        // Use stored data for souls and relations
        const souls = this.lastData?.souls || [];
        const relations = this.lastData?.relations || [];

        // Ensure beings is an array
        beings = beings || [];

        console.log("📊 Raw data:", { souls: souls.length, beings: beings.length, relations: relations.length });
        console.log("🔍 First being structure:", beings[0] || null);
        console.log("🔍 First soul structure:", souls[0] || null);

        // Check what types we have
        console.log("🔍 Being types found:", beings.map(b => b._soul?.genesis?.type || 'unknown').filter((v, i, a) => a.indexOf(v) === i));

        // Filter beings - show all beings with ULID
        const actualBeings = beings.filter(being => {
            const hasUlid = being.ulid;
            if (hasUlid) {
                console.log(`🔍 Being ${being.ulid}: type=${being._soul?.genesis?.type || 'unknown'}`);
            }
            return hasUlid; // Just ensure it has a ULID
        });

        const relationBeings = beings.filter(being =>
            being._soul?.genesis?.type === 'relation' && being.ulid // Keep relation beings for creating links
        );

        console.log(`📊 Filtered: ${actualBeings.length} actualBeings, ${relationBeings.length} relationBeings`);

        // Clear existing nodes and links
        this.nodes = [];
        this.links = [];

        // Ensure beings is an array
        if (!beings || !Array.isArray(beings)) {
            console.log(`❌ Beings data is not valid array:`, beings);
            return;
        }

        // Clear previous graph
        d3.select('#graph').selectAll('*').remove();

        // Use initialized width and height
        const width = this.width;
        const height = this.height;

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

        // Add glow filter for nodes
        const filter = defs.append('filter')
            .attr('id', 'glow');
        filter.append('feGaussianBlur')
            .attr('stdDeviation', 3)
            .attr('result', 'coloredBlur');
        filter.append('feMerge');
        filter.append('feMergeNode')
            .attr('in', 'coloredBlur');
        filter.append('feMergeNode')
            .attr('in', 'SourceGraphic');

        // Debug entities structure (simplified)
        console.log('🔍 First entity structure:', beings[0]);
        console.log('🔍 Entity types found:', beings.map(e => e.type || 'unknown').filter((v, i, a) => a.indexOf(v) === i));

        // Create nodes from simplified entities
        const entityNodes = beings.map((entity, i) => {
            const hasAlias = entity._soul?.alias;
            const genesisType = entity._soul?.genesis?.type;
            const hasAttributes = entity.attributes && Object.keys(entity.attributes).length > 0;

            const isSoulTemplate = hasAlias && !hasAttributes &&
                                  ['user_profile', 'ai_agent', 'basic_relation', 'sample_entity'].includes(entity._soul?.alias);

            console.log(`🔍 Node analysis: ${entity.ulid}:`, {
                alias: hasAlias ? entity._soul.alias : 'NO_ALIAS',
                genesisType: genesisType || 'UNDEFINED',
                hasAttributes,
                isSoulTemplate,
                attributesCount: entity.attributes ? Object.keys(entity.attributes).length : 0,
            });

            return {
                id: entity.id,
                x: width/2 + Math.cos(i * 2 * Math.PI / beings.length) * 150,
                y: height/2 + Math.sin(i * 2 * Math.PI / beings.length) * 150,
                entity: entity,
                vx: 0,
                vy: 0,
                type: entity.type || 'entity',
                label: entity.name || 'Unnamed'
            };
        });

        const beingNodes = actualBeings.map((being, i) => {
            const hasAlias = being._soul?.alias;
            const genesisType = being._soul?.genesis?.type;
            const hasAttributes = being.attributes && Object.keys(being.attributes).length > 0;

            const isSoul = hasAlias && !hasAttributes &&
                          ['user_profile', 'ai_agent', 'basic_relation', 'sample_entity'].includes(being._soul?.alias);

            const isRelation = genesisType === 'relation' ||
                              (hasAttributes && (being.attributes.source_uid || being.attributes.relation_type));

            console.log(`🔍 Node analysis: ${being.ulid}:`, {
                alias: hasAlias ? being._soul.alias : 'NO_ALIAS',
                genesisType: genesisType || 'UNDEFINED',
                hasAttributes,
                isSoul,
                isRelation,
                attributesCount: being.attributes ? Object.keys(being.attributes).length : 0,
                hasRelationAttrs: hasAttributes && (being.attributes.source_uid || being.attributes.relation_type)
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

        const relationNodes = relationBeings.map((relation, i) => ({
            id: relation.ulid,
            x: width/2 + Math.cos(i * 2 * Math.PI / relationBeings.length) * 200,
            y: height/2 + Math.sin(i * 2 * Math.PI / relationBeings.length) * 200,
            being: relation,
            vx: 0,
            vy: 0,
            type: 'relation',
            isSoul: false,
            isRelation: true
        }));

        // Process relationships and relations for links
        console.log("🔗 Przetwarzam", relationBeings.length, "bytów relacji i", this.relationships.length, "tradycyjnych relacji");

        // Create a map of node IDs for easier lookup
        const nodeMap = new Map();
        [...entityNodes, ...beingNodes, ...relationNodes].forEach(node => nodeMap.set(node.id, node));

        const links = [];

        // Add links from relation beings
        relationBeings.forEach(relationBeing => {
            const attrs = relationBeing.attributes || {};
            const sourceUid = attrs.source_uid;
            const targetUid = attrs.target_uid;

            if (sourceUid && targetUid) {
                const sourceExists = nodeMap.get(sourceUid);
                const targetExists = nodeMap.get(targetUid);

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

        // Add links from traditional relationships (now supports mixed ID types)
        this.relationships.forEach(rel => {
            // Handle both new and legacy relationship formats
            const sourceId = rel.source_uid || rel.source_ulid;
            const targetId = rel.target_uid || rel.target_ulid;
            const sourceType = rel.source_type || 'being';
            const targetType = rel.target_type || 'being';

            const sourceExists = nodeMap.get(sourceId);
            const targetExists = nodeMap.get(targetId);

            if (sourceExists && targetExists) {
                links.push({
                    source: sourceId,
                    target: targetId,
                    type: sourceType === 'soul' || targetType === 'soul' ? 'soul_relation' : 'connection',
                    relation_type: rel.relation_type || 'unknown',
                    strength: parseFloat(rel.strength) || 0.5,
                    metadata: rel.metadata || {},
                    source_type: sourceType,
                    target_type: targetType
                });
                console.log(`✅ Dodano link z relationships: ${sourceType}(${sourceId.substring(0,8)}...) -> ${targetType}(${targetId.substring(0,8)}...)`);
            } else {
                 console.log(`⚠️ Nie znaleziono węzłów dla relacji: ${sourceType}(${sourceId?.substring(0,8)}...) -> ${targetType}(${targetId?.substring(0,8)}...)`);
            }
        });

        // Store the processed links for later use
        this.links = links;

        // POŁĄCZ wszystkie typy węzłów
        const allNodes = [...entityNodes, ...beingNodes, ...relationNodes];
        console.log(`📊 Total nodes: ${allNodes.length} (${entityNodes.length} entities + ${beingNodes.length} beings + ${relationNodes.length} relations)`);

        // Create force simulation
        const simulation = d3.forceSimulation(allNodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-500))
            .force('center', d3.forceCenter(width/2, height/2))
            .force('collision', d3.forceCollide().radius(50));

        // Draw links with different styles based on relationship type
        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'link')
            .style('stroke', d => {
                if (d.type === 'soul_relation') return '#ffd700'; // Gold for soul-being relationships
                if (d.relation_type === 'instantiates') return '#ffaa00'; // Orange for instantiation
                if (d.relation_type === 'similar_content') return '#00ff88';
                if (d.relation_type === 'communication') return '#ff8800';
                if (d.type === 'relation_being') return '#00ccff'; // Blue for relation beings
                if (d.relation_type === 'similarity') return '#aa88ff'; // Purple for similarity
                return '#555';
            })
            .style('stroke-width', d => {
                // Thicker lines for soul relationships
                const baseWidth = d.type === 'soul_relation' ? 3 : 2;
                return Math.max(baseWidth, d.strength * 5);
            })
            .style('opacity', d => {
                // Higher opacity for soul relationships
                const baseOpacity = d.type === 'soul_relation' ? 0.8 : 0.4;
                return Math.max(baseOpacity, d.strength);
            })
            .style('stroke-dasharray', d => {
                // Different line styles for different relationship types
                if (d.relation_type === 'instantiates') return '8,3'; // Dash-dot for instantiation
                if (d.relation_type === 'similar_content') return '5,5';
                if (d.type === 'relation_being') return '3,3';
                if (d.relation_type === 'similarity') return '2,2';
                return 'none';
            })
            .on('mouseover', function(event, d) {
                // Highlight line on hover
                const baseWidth = d.type === 'soul_relation' ? 3 : 2;
                d3.select(this).style('stroke-width', Math.max(baseWidth + 2, d.strength * 6));

                // Show tooltip with relationship info
                const tooltip = d3.select('body').append('div')
                    .attr('class', 'tooltip')
                    .style('position', 'absolute')
                    .style('background', 'rgba(0,0,0,0.8)')
                    .style('color', 'white')
                    .style('padding', '5px')
                    .style('border-radius', '3px')
                    .style('font-size', '12px')
                    .style('pointer-events', 'none')
                    .style('z-index', '1000')
                    .html(`
                        <strong>${d.relation_type}</strong><br/>
                        ${d.source_type || 'being'} → ${d.target_type || 'being'}<br/>
                        Strength: ${d.strength}
                    `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px');
            })
            .on('mouseout', function(event, d) {
                // Restore normal thickness
                const baseWidth = d.type === 'soul_relation' ? 3 : 2;
                d3.select(this).style('stroke-width', Math.max(baseWidth, d.strength * 5));

                // Remove tooltip
                d3.select('.tooltip').remove();
            });

        // Create nodes with type-specific styling
        const node = g.append('g')
            .selectAll('.node')
            .data(allNodes)
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

            if (d.type === 'soul') {
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

            } else if (d.type === 'relation') {
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
        const labels = node.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 35)
            .style('font-size', '11px')
            .style('fill', d => d.type === 'soul' ? '#b8860b' : (d.type === 'relation' ? '#5b21b6' : '#2c5282'))
            .style('font-weight', 'bold')
            .text(d => {
                const being = d.being;
                let prefix = '';
                let label = '';

                if (d.type === 'soul') {
                    prefix = '♦ SOUL: ';
                    // For souls, prioritize alias
                    label = being._soul?.alias || 'Unknown Soul';
                } else if (d.type === 'relation') {
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
        const relationLabels = node.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 48)
            .style('font-size', '9px')
            .style('fill', '#666')
            .style('font-style', 'italic')
            .text(d => {
                if (d.type === 'soul') return 'Soul';
                if (d.type === 'relation') return 'Relation';
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
        });

        // Add title
        const svg = this.svg; // Ensure svg is accessible here
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
                const hexagon = "M0,-8 L6.93,-4 L6.93,4 L0,20 L-6.93,4 L-6.93,-4 Z";
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

        console.log(`✨ Graf renderowany z ${allNodes.length} węzłami i ${links.length} połączeniami!`);
        console.log(`🔗 Znaleziono ${relationBeings.length} bytów relacji i ${this.relationships.length} tradycyjnych relacji`);
        console.log('📋 Szczegóły linków:', links.map(l => `${l.source?.id || l.source} -> ${l.target?.id || l.target} (${l.relation_type})`));
        console.log("📋 Dostępne węzły:", allNodes.map(n => `${n.label} (${n.id.substring(0, 8)}...) [${n.type}]`));
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
        // Update width and height based on current window dimensions
        this.width = window.innerWidth;
        this.height = window.innerHeight - 200;

        if (this.svg) {
            this.svg
                .attr('width', this.width)
                .attr('height', this.height);
        }

        // Re-render the universe with new dimensions using stored data
        if (this.lastData && this.lastData.beings) {
            this.renderUniverse(this.lastData.beings);
        } else {
            console.warn("Resize called but no beings data available to re-render.");
            d3.select('#graph').selectAll('*').remove();
        }
    }

    clear() {
        console.log('🗑️ Czyszczenie grafu...');
        d3.select('#graph').selectAll('*').remove();
        this.beings = [];
        this.relationships = [];
    }
}

// Global functions
console.log('✅ LuxOSGraph class defined and available globally');
window.LuxOSGraph = LuxOSGraph;

function clearGraph() {
    console.log('🗑️ Czyszczenie grafu...');
    if (window.graph) {
        window.graph.clear();
    }
}

function testData() {
    console.log('🧪 Ładowanie danych testowych...');
    fetch('/test-data')
        .then(response => response.json())
        .then(data => {
            console.log('✅ Otrzymano dane testowe:', data);
        })
        .catch(error => {
            console.error('❌ Błąd podczas ładowania danych testowych:', error);
        });
}

// Export for global use
window.clearGraph = clearGraph;
window.testData = testData;