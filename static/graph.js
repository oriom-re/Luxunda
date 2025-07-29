class LuxOSUniverse {
    constructor() {
        this.beings = [];
        this.agents = [];
        this.selectedNodes = [];
        this.universeCenter = { x: 0, y: 0 };
        this.universeRunning = false;
        this.zoomLevel = 1;
        this.viewOffset = { x: 0, y: 0 };
        this.beingsPositions = {};
        this.detailsLevel = 1;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.lastUpdateTime = 0;
        this.updateThrottle = 100;
        this.heartbeatInterval = null;

        // Inicjalizacja Socket.IO z lepszą konfiguracją
        this.socket = io({
            timeout: 20000,
            reconnection: true,
            reconnectionDelay: 2000,
            reconnectionDelayMax: 10000,
            randomizationFactor: 0.5,
            reconnectionAttempts: 10,
            maxReconnectionAttempts: 10,
            forceNew: false,
            transports: ['websocket', 'polling']
        });
        this.setupSocketListeners();

        // Inicjalizacja SVG
        this.initUniverse();

        // Requestuj dane wszechświata
        this.socket.emit('get_graph_data');

        console.log('LuxOS Universe initialized');
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('✅ Połączono z wszechświatem LuxOS');
            this.updateConnectionStatus(true);
            this.reconnectAttempts = 0;

            setTimeout(() => {
                console.log('📡 Żądanie danych grafu...');
                this.socket.emit('get_graph_data');
            }, 100);

            this.startHeartbeat();
        });

        this.socket.on('disconnect', (reason) => {
            console.log('Rozłączono ze wszechświatem:', reason);
            this.updateConnectionStatus(false);

            if (reason !== 'io client disconnect') {
                this.attemptReconnect();
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('Błąd połączenia z wszechświatem:', error);
            this.updateConnectionStatus(false);
        });

        this.socket.on('graph_data', (data) => {
            console.log('📊 Otrzymano dane wszechświata:', {
                nodes: data.nodes?.length || 0,
                relationships: data.relationships?.length || 0
            });

            if (data.nodes && Array.isArray(data.nodes)) {
                this.throttledUpdate(data);
            } else {
                console.warn('⚠️ Nieprawidłowe dane grafu:', data);
            }
        });

        this.socket.on('intention_response', (response) => {
            try {
                console.log('Odpowiedź na intencję:', response);
                if (window.intentionComponent) {
                    window.intentionComponent.handleIntentionResponse(response);
                }
            } catch (error) {
                console.error('Błąd obsługi odpowiedzi na intencję:', error);
            }
        });

        this.socket.on('being_created', (being) => {
            try {
                console.log('Nowy byt w wszechświecie:', being);
                this.addBeing(being);
            } catch (error) {
                console.error('Błąd dodawania bytu:', error);
            }
        });

        this.socket.on('error', (error) => {
            console.error('Błąd wszechświata:', error);
            this.showErrorMessage('Błąd połączenia z wszechświatem: ' + (error.message || error));
        });
    }

    initUniverse() {
        this.width = window.innerWidth;
        this.height = window.innerHeight - 70 - 120;

        this.svg = d3.select("#graph")
            .attr("width", this.width)
            .attr("height", this.height)
            .attr("viewBox", [-this.width/2, -this.height/2, this.width, this.height]);

        // Zoom i pan dla nawigacji po wszechświecie
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 50])
            .on("zoom", (event) => {
                this.container.attr("transform", event.transform);
                this.zoomLevel = event.transform.k;
            });

        this.svg.call(this.zoom);

        // Główny kontainer wszechświata
        this.container = this.svg.append("g");

        // Definicje gradientów i efektów
        this.setupUniverseEffects();

        // Grupy dla różne elementy wszechświata
        this.starsGroup = this.container.append("g").attr("class", "stars");
        this.orbitsGroup = this.container.append("g").attr("class", "orbits");
        this.linksGroup = this.container.append("g").attr("class", "links");
        this.beingsGroup = this.container.append("g").attr("class", "beings");
        this.effectsGroup = this.container.append("g").attr("class", "effects");

        // Tło przestrzeni kosmicznej
        this.createSpaceBackground();

        // Resize handler
        window.addEventListener('resize', () => {
            this.width = window.innerWidth;
            this.height = window.innerHeight - 70 - 120;
            this.svg.attr("width", this.width).attr("height", this.height);
            this.svg.attr("viewBox", [-this.width/2, -this.height/2, this.width, this.height]);
        });
    }

    setupUniverseEffects() {
        const defs = this.container.append("defs");

        // Gradient dla Lux (centralnej gwiazdy)
        const luxGradient = defs.append("radialGradient")
            .attr("id", "luxStar")
            .attr("cx", "50%")
            .attr("cy", "50%")
            .attr("r", "50%");

        luxGradient.append("stop")
            .attr("offset", "0%")
            .attr("stop-color", "#ffffff")
            .attr("stop-opacity", 1);

        luxGradient.append("stop")
            .attr("offset", "30%")
            .attr("stop-color", "#ffff00")
            .attr("stop-opacity", 0.9);

        luxGradient.append("stop")
            .attr("offset", "70%")
            .attr("stop-color", "#ffd700")
            .attr("stop-opacity", 0.7);

        luxGradient.append("stop")
            .attr("offset", "100%")
            .attr("stop-color", "#ff8c00")
            .attr("stop-opacity", 0.3);

        // Definicja strzałki dla relacji
        defs.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "-0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("orient", "auto")
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("xoverflow", "visible")
            .append("svg:path")
            .attr("d", "M 0,-5 L 10 ,0 L 0,5")
            .attr("fill", "#666")
            .style("stroke", "none");

        // Filter dla efektów świetlnych
        const glowFilter = defs.append("filter")
            .attr("id", "glow")
            .attr("width", "200%")
            .attr("height", "200%");

        glowFilter.append("feGaussianBlur")
            .attr("stdDeviation", "3")
            .attr("result", "coloredBlur");

        const feMerge = glowFilter.append("feMerge");
        feMerge.append("feMergeNode").attr("in", "coloredBlur");
        feMerge.append("feMergeNode").attr("in", "SourceGraphic");
    }

    createSpaceBackground() {
        // Utwórz gwiazdy w tle (ograniczona liczba dla wydajności)
        const starCount = 50;
        const stars = [];

        for (let i = 0; i < starCount; i++) {
            stars.push({
                x: (Math.random() - 0.5) * this.width * 2,
                y: (Math.random() - 0.5) * this.height * 2,
                size: Math.random() * 2,
                opacity: Math.random() * 0.8 + 0.2
            });
        }

        this.starsGroup.selectAll(".star")
            .data(stars)
            .enter().append("circle")
            .attr("class", "star")
            .attr("cx", d => d.x)
            .attr("cy", d => d.y)
            .attr("r", d => d.size)
            .attr("fill", "white")
            .attr("opacity", d => d.opacity);
    }

    updateUniverse(data) {
        console.log('🔄 Aktualizacja wszechświata:', data);

        const uniqueNodes = [];
        const seenSouls = new Set();

        (data.nodes || []).forEach(node => {
            const soulId = node.soul_uid || node.soul;
            if (!seenSouls.has(soulId)) {
                seenSouls.add(soulId);
                uniqueNodes.push(node);
            }
        });

        console.log(`📊 Filtracja: ${(data.nodes || []).length} → ${uniqueNodes.length} unikalnych bytów`);

        this.relationships = data.relationships || [];
        console.log('🔗 Otrzymano relacje:', this.relationships.length);

        this.beings = uniqueNodes.map(node => {
            try {
                if (typeof node._soul?.genesis === 'string') {
                    node._soul.genesis = JSON.parse(node._soul.genesis);
                }
                if (typeof node._soul?.attributes === 'string') {
                    node._soul.attributes = JSON.parse(node._soul.attributes);
                }
                if (typeof node._soul?.memories === 'string') {
                    node._soul.memories = JSON.parse(node._soul.memories);
                }
                if (typeof node._soul?.self_awareness === 'string') {
                    node._soul.self_awareness = JSON.parse(node._soul.self_awareness);
                }

                return {
                    soul: node.soul_uid || node.soul,
                    soul_uid: node.soul_uid,
                    genesis: node._soul?.genesis || node.genesis || { type: 'unknown', name: 'Unknown' },
                    attributes: node._soul?.attributes || node.attributes || { energy_level: 50 },
                    memories: node._soul?.memories || node.memories || [],
                    self_awareness: node._soul?.self_awareness || node.self_awareness || {}
                };
            } catch (e) {
                console.warn('Błąd parsowania danych bytu:', e, node);
                return {
                    soul: node.soul_uid || node.soul || 'unknown',
                    soul_uid: node.soul_uid,
                    genesis: { type: 'unknown', name: 'Unknown' },
                    attributes: { energy_level: 50 },
                    memories: [],
                    self_awareness: {}
                };
            }
        });

        this.updateStats();
        this.renderUniverse();
    }

    renderUniverse() {
        console.log(`🌌 Renderuję wszechświat z ${this.beings.length} bytami`);

        this.renderRelationships();
        this.renderBeings();
    }

    renderRelationships() {
        if (!this.relationships || this.relationships.length === 0) {
            this.linksGroup.selectAll(".relationship").remove();
            return;
        }

        const beingsMap = new Map();
        this.beings.forEach(being => {
            beingsMap.set(being.soul || being.soul_uid, being);
        });

        const validRelationships = this.relationships.filter(rel => {
            const source = beingsMap.get(rel.source_soul);
            const target = beingsMap.get(rel.target_soul);
            return source && target;
        }).map(rel => {
            return {
                ...rel,
                source: beingsMap.get(rel.source_soul),
                target: beingsMap.get(rel.target_soul)
            };
        });

        console.log('Renderuję relacje:', validRelationships.length);

        const linkSelection = this.linksGroup
            .selectAll(".relationship")
            .data(validRelationships, d => `${d.source_soul}-${d.target_soul}`)
            .join("line")
            .attr("class", "relationship")
            .attr("stroke", d => this.getRelationshipColor(d.genesis?.type || 'unknown'))
            .attr("stroke-width", d => Math.max(1, (d.attributes?.energy_level || 30) / 30))
            .attr("stroke-opacity", 0.6)
            .attr("marker-end", "url(#arrowhead)")
            .style("pointer-events", "none");

        this.updateRelationshipPositions = () => {
            linkSelection
                .attr("x1", d => d.source.x || 0)
                .attr("y1", d => d.source.y || 0)
                .attr("x2", d => d.target.x || 0)
                .attr("y2", d => d.target.y || 0);
        };

        this.updateRelationshipPositions();
    }

    getRelationshipColor(type) {
        const colors = {
            'calls': '#ff6b6b',
            'inherits': '#4CAF50',
            'contains': '#2196F3',
            'depends': '#FF9800',
            'creates': '#9C27B0',
            'modifies': '#FF5722',
            'references': '#607D8B',
            'extends': '#795548',
            'unknown': '#666666'
        };
        return colors[type] || colors.unknown;
    }

    renderBeings() {
        const visibleBeings = this.beings.slice(0, 50);

        this.initForceSimulation(visibleBeings);

        this.beingSelection = this.beingsGroup
            .selectAll(".being")
            .data(visibleBeings, d => d.soul)
            .join("g")
            .attr("class", d => `being ${this.isLuxAgent(d) ? 'lux-agent' : d.genesis?.type || 'unknown'}`)
            .style("cursor", "pointer")
            .call(d3.drag()
                .on("start", this.dragstarted.bind(this))
                .on("drag", this.dragged.bind(this))
                .on("end", this.dragended.bind(this)))
            .on("click", (event, d) => {
                event.stopPropagation();
                this.selectBeing(d);
            });

        this.beingSelection.selectAll("*").remove();

        const self = this;
        this.beingSelection.each(function(d) {
            const being = d3.select(this);
            const energySize = Math.max(5, Math.min(25, (d.attributes?.energy_level || 50) / 4));

            being.append("circle")
                .attr("r", energySize)
                .attr("fill", self.getBeingColor ? self.getBeingColor(d) : '#666666')
                .attr("stroke", "#ffffff")
                .attr("stroke-width", 1);

            being.append("text")
                .attr("class", "being-name")
                .attr("dy", energySize + 15)
                .style("text-anchor", "middle")
                .style("fill", "white")
                .style("font-size", "10px")
                .style("font-weight", "bold")
                .style("pointer-events", "none")
                .text(d.genesis?.name || d.soul?.slice(0, 8) || 'Being');
        });
    }

    initForceSimulation(nodes) {
        if (this.simulation) {
            this.simulation.stop();
        }

        this.simulation = d3.forceSimulation(nodes)
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(0, 0).strength(0.8))
            .force("collision", d3.forceCollide()
                .radius(d => Math.max(12, Math.min(30, (d.attributes?.energy_level || 50) / 3)))
                .strength(0.9))
            .alphaMin(0.001)
            .on("tick", () => {
                this.updateNodePositions();
            });

        nodes.forEach((d, index) => {
            if (!d.x || !d.y) {
                const angle = (index * 2 * Math.PI) / Math.max(nodes.length - 1, 1);
                const radius = 80 + Math.random() * 60;
                d.x = Math.cos(angle) * radius;
                d.y = Math.sin(angle) * radius;
            }
        });
    }

    updateNodePositions() {
        if (!this.beingSelection) return;

        this.beingSelection
            .attr("transform", d => {
                const maxDistance = 300;
                let x = d.x || 0;
                let y = d.y || 0;

                const distance = Math.sqrt(x * x + y * y);
                if (distance > maxDistance) {
                    const scale = maxDistance / distance;
                    x = x * scale;
                    y = y * scale;
                    d.x = x;
                    d.y = y;
                }

                return `translate(${x}, ${y})`;
            });

        if (this.updateRelationshipPositions) {
            this.updateRelationshipPositions();
        }
    }

    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    isLuxAgent(being) {
        return being.soul === '00000000-0000-0000-0000-000000000001' || 
               being.genesis?.lux_identifier === 'lux-core-consciousness' ||
               (being.genesis?.name === 'Lux' && being.genesis?.type === 'agent');
    }

    getBeingColor(being) {
        const type = being.genesis?.type || 'unknown';
        const colors = {
            'agent': '#ff6b6b',
            'function': '#4CAF50',
            'class': '#2196F3',
            'data': '#FF9800',
            'task': '#9C27B0',
            'component': '#FF5722',
            'message': '#607D8B',
            'scenario': '#795548',
            'unknown': '#666666'
        };
        return colors[type] || colors.unknown;
    }

    selectBeing(being) {
        console.log('Kliknięto byt:', being.soul, being.genesis?.name);
    }

    addBeing(being) {
        try {
            const processedBeing = {
                soul: being.soul_uid || being.soul,
                soul_uid: being.soul_uid,
                genesis: being._soul?.genesis || being.genesis || { type: 'unknown', name: 'Unknown' },
                attributes: being._soul?.attributes || being.attributes || { energy_level: 50 },
                memories: being._soul?.memories || being.memories || [],
                self_awareness: being._soul?.self_awareness || being.self_awareness || {}
            };

            const existingIndex = this.beings.findIndex(b => 
                b.soul === processedBeing.soul || b.soul_uid === processedBeing.soul_uid);

            if (existingIndex !== -1) {
                this.beings[existingIndex] = processedBeing;
            } else {
                const angle = Math.random() * 2 * Math.PI;
                const radius = 150 + Math.random() * 100;
                processedBeing.x = Math.cos(angle) * radius;
                processedBeing.y = Math.sin(angle) * radius;
                this.beings.push(processedBeing);
            }

            console.log('Dodano/zaktualizowano byt:', processedBeing);
            this.updateStats();
            this.renderUniverse();
        } catch (error) {
            console.error('Błąd dodawania bytu:', error, being);
        }
    }

    updateStats() {
        document.getElementById('nodesCount').textContent = this.beings.length;
        document.getElementById('linksCount').textContent = (this.relationships || []).length;
    }

    updateConnectionStatus(connected) {
        const dot = document.getElementById('connectionDot');
        const status = document.getElementById('connectionStatus');

        if (connected) {
            dot.classList.add('connected');
            status.textContent = 'Wszechświat aktywny';
            status.className = 'status-connected';
        } else {
            dot.classList.remove('connected');
            status.textContent = 'Wszechświat nieaktywny';
            status.className = 'status-disconnected';
        }
    }

    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: #ff4444;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 2000;
            max-width: 300px;
        `;

        document.body.appendChild(errorDiv);

        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts -1), 5000);

            console.log(`Próba reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} za ${delay}ms`);

            const status = document.getElementById('connectionStatus');
            if (status) {
                status.textContent = `Łączenie... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`;
            }

            setTimeout(() => {
                if (!this.socket.connected) {
                    try {
                        this.socket.connect();
                    } catch (error) {
                        console.error('Błąd podczas reconnect:', error);
                        this.attemptReconnect();
                    }
                }
            }, delay);
        } else {
            console.log('Maksymalna liczba prób reconnect osiągnięta - resetuję licznik');
            this.showErrorMessage('Problemy z połączeniem - spróbuję ponownie...');

            setTimeout(() => {
                this.reconnectAttempts = 0;
                this.attemptReconnect();
            }, 30000);
        }
    }

    throttledUpdate(data) {
        const now = Date.now();
        if (now - this.lastUpdateTime < this.updateThrottle) {
            return;
        }
        this.lastUpdateTime = now;
        this.updateUniverse(data);
    }

    startHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }

        this.heartbeatInterval = setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('ping');
            }
        }, 30000);
    }

    // Metody dla kompatybilności
    zoomIn() {
        this.svg.transition().duration(300).call(this.zoom.scaleBy, 1.5);
    }

    zoomOut() {
        this.svg.transition().duration(300).call(this.zoom.scaleBy, 1 / 1.5);
    }

    resetZoom() {
        this.svg.transition().duration(500).call(
            this.zoom.transform,
            d3.zoomIdentity
        );
    }

    resizeGraph() {
        if (this.svg && this.container) {
            this.width = window.innerWidth;
            this.height = window.innerHeight - 70 - 120;

            this.svg
                .attr("width", this.width)
                .attr("height", this.height);

            if (this.simulation) {
                this.simulation
                    .force("center", d3.forceCenter(0, 0))
                    .alpha(0.3)
                    .restart();
            }
        }
    }
}

// Ensure single global declaration
if (typeof window.LuxOSGraph === 'undefined') {
    window.LuxOSGraph = LuxOSUniverse;
    console.log('✅ LuxOSGraph class defined and available globally');
} else {
    console.log('⚠️ LuxOSGraph already defined, skipping redefinition');
}