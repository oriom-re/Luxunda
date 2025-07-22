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
        this.updateThrottle = 100; // Minimum 100ms between updates
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
            console.log('Połączono z wszechświatem');
            this.updateConnectionStatus(true);
            this.reconnectAttempts = 0; // Reset counter on successful connection

            // Natychmiast poproś o dane po połączeniu
            setTimeout(() => {
                this.socket.emit('get_graph_data');
            }, 100);

            // Rozpocznij heartbeat monitoring
            this.startHeartbeat();
        });

        this.socket.on('disconnect', (reason) => {
            console.log('Rozłączono ze wszechświatem:', reason);
            this.updateConnectionStatus(false);

            // Nie próbuj reconnect jeśli to było ręczne rozłączenie
            if (reason !== 'io client disconnect') {
                this.attemptReconnect();
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('Błąd połączenia z wszechświatem:', error);
            this.updateConnectionStatus(false);
        });

        // Obsługa otrzymanych danych grafu z throttling
        this.socket.on('graph_data', (data) => {
            console.log('Aktualizacja wszechświata:', data);
            this.throttledUpdate(data);
        });

        // Obsługa kontekstu głównej intencji LuxOS
        this.socket.on('main_intention_context', (data) => {
            console.log('Otrzymano kontekst głównej intencji LuxOS:', data);
            this.handleMainIntentionContext(data);
        });

        // Event listenery dla głównej intencji
        this.setupMainIntentionControls();

        this.socket.on('universe_state', (data) => {
            try {
                this.updateUniversePositions(data);
            } catch (error) {
                console.error('Błąd aktualizacji pozycji:', error);
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

        // Obsługa odpowiedzi na zadania z callback systemem
        this.socket.on('task_response', (response) => {
            console.log('🔄 Otrzymano odpowiedź na zadanie:', response);
            if (response.taskId) {
                this.socket.emit(`task_response_${response.taskId}`, response);
            }
        });

        this.socket.on('intention_response', (response) => {
            try {
                console.log('Odpowiedź na intencję:', response);
                // Przekaż do intention component jeśli istnieje
                if (window.intentionComponent) {
                    window.intentionComponent.handleIntentionResponse(response);
                }
            } catch (error) {
                console.error('Błąd obsługi odpowiedzi na intencję:', error);
            }
        });

        this.socket.on('component_created', (componentData) => {
            try {
                console.log('Nowy komponent D3.js utworzony:', componentData);
                this.handleNewComponent(componentData);
            } catch (error) {
                console.error('Błąd obsługi nowego komponentu:', error);
            }
        });

        this.socket.on('error', (error) => {
            console.error('Błąd wszechświata:', error);
            this.showErrorMessage('Błąd połączenia z wszechświatem: ' + (error.message || error));
        });

        // Globalna obsługa nieobsłużonych błędów Promise
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Nieobsłużony błąd Promise:', event.reason);
            // Nie zapobiegamy domyślnemu logowaniu - pozwól na debugging
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
                // Usuń updateDetailsLevel() - zoom nie powinien zmieniać pozycji bytów
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
        const starCount = 50; // Zmniejszone z 200 na 50
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

        // Bezpieczna deserializacja danych - usuń duplikaty po soul_uid
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

        // Pobierz relacje między bytami
        this.relationships = data.relationships || [];
        console.log('🔗 Otrzymano relacje:', this.relationships.length);

        this.beings = uniqueNodes.map(node => {
            try {
                // Parsuj stringi JSON z backendu
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

                // Mapuj strukturę dla kompatybilności
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

        this.ensureLuxAgent();
        this.updateStats();
        this.renderUniverse();
    }

    updateUniversePositions(data) {
        console.log('Aktualizacja pozycji wszechświata:', data);

        this.beingsPositions = data.beings_positions || {};
        this.updateBeingPositions();
    }

    ensureLuxAgent() {
        // KOMPLETNIE USUNIĘTE - backend w pełni zarządza Lux
        console.log('🚫 Frontend NIE tworzy agenta Lux - backend zarządza wszystkim');
        // NIE RÓB NICZEGO - backend ma pełną kontrolę
    }
            fx: 0,
            fy: 0
        };

        this.beings.unshift(luxAgent);
        this.socket.emit('create_being', {
            being_type: 'agent',
            genesis: luxAgent.genesis,
            attributes: luxAgent.attributes,
            memories: luxAgent.memories,
            self_awareness: luxAgent.self_awareness
        });

        console.log('Utworzono Lux jako głównego agenta:', luxAgent);
    }

    createMainIntention() {
        const mainIntention = {
            soul: '11111111-1111-1111-1111-111111111111',
            genesis: {
                type: 'message',
                name: 'LuxOS Main Intention',
                source: 'System.Core.MainIntention.Initialize()',
                description: 'Główna intencja systemu LuxOS'
            },
            attributes: {
                energy_level: 500,
                metadata: {
                    message_type: 'intention',
                    is_main_intention: true
                },
                message_data: {
                    content: 'System LuxOS Core Intention'
                },
                tags: ['intention', 'main', 'core', 'luxos']
            },
            self_awareness: {
                trust_level: 1.0,
                confidence: 1.0,
                introspection_depth: 0.8
            },
            memories: [{
                type: 'genesis',
                data: 'Main system intention initialization',
                timestamp: new Date().toISOString(),
                importance: 1.0
            }]
        };

        this.beings.push(mainIntention);
        console.log('Utworzono główną intencję LuxOS:', mainIntention);
    }

    renderUniverse() {
        console.log(`🌌 Renderuję wszechświat z ${this.beings.length} bytami`);
        
        // Renderuj orbity
        this.renderOrbits();

        // Renderuj relacje między bytami
        this.renderRelationships();

        // Renderuj byty jako ciała niebieskie
        this.renderBeings();

        // Dodaj efekty wszechświata
        this.addUniverseEffects();
    }

    renderOrbits() {
        // Zlikwidowano renderowanie orbit - już nie potrzebne
        this.orbitsGroup.selectAll(".orbit").remove();
    }

    renderRelationships() {
        if (!this.relationships || this.relationships.length === 0) {
            this.linksGroup.selectAll(".relationship").remove();
            return;
        }

        // Utwórz mapę bytów dla szybkiego wyszukiwania pozycji
        const beingsMap = new Map();
        this.beings.forEach(being => {
            beingsMap.set(being.soul || being.soul_uid, being);
        });

        // Przygotuj dane dla relacji - tylko te które mają oba końce
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

        // Renderuj linie relacji
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

        // Aktualizuj pozycje linii na podstawie pozycji bytów
        this.updateRelationshipPositions = () => {
            linkSelection
                .attr("x1", d => d.source.x || 0)
                .attr("y1", d => d.source.y || 0)
                .attr("x2", d => d.target.x || 0)
                .attr("y2", d => d.target.y || 0);
        };

        // Wywołaj aktualizację pozycji
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

    drawMainIntentionOrbit() {
        // Usuń poprzednią orbitę
        this.orbitsGroup.selectAll(".main-intention-orbit").remove();

        // Narysuj cienką, prawie przezroczystą orbitę dla głównej intencji
        const orbitRadius = 100; // Dopasuj do nowego promienia

        this.orbitsGroup.append("circle")
            .attr("class", "main-intention-orbit")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", orbitRadius)
            .attr("fill", "none")
            .attr("stroke", "#00ff88")
            .attr("stroke-width", 1)
            .attr("stroke-dasharray", "5,5")
            .attr("opacity", 0.3)
            .style("pointer-events", "none");
    }

    renderBeings() {
        // Limit do 50 bytów dla wydajności
        const visibleBeings = this.beings.slice(0, 50);

        // Inicjalizuj symulację D3 force
        this.initForceSimulation(visibleBeings);

        // Narysuj orbitę dla głównej intencji (cienka, prawie przezroczysta)
        this.drawMainIntentionOrbit();

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
            })
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                this.showBeingContextMenu(d, event);
            });

        // Usuń poprzednie elementy tylko jeśli konieczne
        this.beingSelection.selectAll("*").remove();

        // Uruchom ciągłą animację orbit tylko dla specjalnych bytów
        this.startOrbitalAnimation();

        // Renderuj Lux jako centralną gwiazdę (bez żółtego pierścienia)
        this.beingSelection.filter(d => this.isLuxAgent(d))
            .each(function(d) {
                const being = d3.select(this);

                // Główna gwiazda - bez dodatkowego pierścienia
                being.append("circle")
                    .attr("r", 40)
                    .attr("fill", "url(#luxStar)")
                    .style("filter", "url(#glow)");

                // Nazwa Lux
                being.append("text")
                    .attr("class", "lux-label")
                    .attr("dy", 55)
                    .style("text-anchor", "middle")
                    .style("fill", "#ffff00")
                    .style("font-size", "12px")
                    .style("font-weight", "bold")
                    .style("pointer-events", "none")
                    .text("LUX");

                // Typ genesis dla Lux
                being.append("text")
                    .attr("class", "lux-type")
                    .attr("dy", 68)
                    .style("text-anchor", "middle")
                    .style("fill", "#ffd700")
                    .style("font-size", "9px")
                    .style("font-weight", "normal")
                    .style("pointer-events", "none")
                    .style("opacity", "0.8")
                    .text(`[${d.genesis?.type || 'agent'}]`);
            });

        // Wiadomości nie są renderowane - tylko na żądanie

        // Renderuj główną intencję LuxOS jako specjalny byt
        this.beingSelection.filter(d => d.soul === '11111111-1111-1111-1111-111111111111' || 
                                     (d.genesis?.type === 'message' && d.attributes?.metadata?.is_main_intention))
            .each(function(d) {
                const being = d3.select(this);

                // Główne ciało intencji - większe i bardziej widoczne
                being.append("circle")
                    .attr("r", 12)
                    .attr("fill", "#00ff88")
                    .attr("stroke", "#ffffff")
                    .attr("stroke-width", 2)
                    .style("filter", "url(#glow)")
                    .style("opacity", 1);

                // Dodatkowy pierścień dla lepszej widoczności
                being.append("circle")
                    .attr("r", 16)
                    .attr("fill", "none")
                    .attr("stroke", "#00ff88")
                    .attr("stroke-width", 1)
                    .attr("opacity", 0.4);

                // Nazwa zawsze widoczna
                being.append("text")
                    .attr("class", "being-label")
                    .attr("dy", 25)
                    .style("text-anchor", "middle")
                    .style("fill", "#00ff88")
                    .style("font-size", "10px")
                    .style("font-weight", "bold")
                    .style("pointer-events", "none")
                    .text("LuxOS Intention");

                // Typ genesis
                being.append("text")
                    .attr("class", "being-type")
                    .attr("dy", 38)
                    .style("text-anchor", "middle")
                    .style("fill", "#00ff88")
                    .style("font-size", "8px")
                    .style("font-weight", "normal")
                    .style("pointer-events", "none")
                    .style("opacity", "0.7")
                    .text(`[${d.genesis?.type || 'intention'}]`);
            });

        // Renderuj pozostałe byty jako planety/komety
        const self = this;
        this.beingSelection.filter(d => !this.isLuxAgent(d) && d.genesis?.type !== 'message' && d.soul !== '11111111-1111-1111-1111-111111111111')
            .each(function(d) {
                const being = d3.select(this);
                const energySize = Math.max(5, Math.min(25, (d.attributes?.energy_level || 50) / 4));

                // Główne ciało
                being.append("circle")
                    .attr("r", energySize)
                    .attr("fill", self.getBeingColor ? self.getBeingColor(d) : '#666666')
                    .attr("stroke", "#ffffff")
                    .attr("stroke-width", 1)
                    .style("filter", d.attributes?.energy_level > 80 ? "url(#glow)" : null);

                // Nazwa bytu
                being.append("text")
                    .attr("class", "being-name")
                    .attr("dy", energySize + 15)
                    .style("text-anchor", "middle")
                    .style("fill", "white")
                    .style("font-size", "10px")
                    .style("font-weight", "bold")
                    .style("pointer-events", "none")
                    .text(d.genesis?.name || d.soul?.slice(0, 8) || 'Being');

                // Typ genesis - zawsze widoczny
                being.append("text")
                    .attr("class", "being-type")
                    .attr("dy", energySize + 28)
                    .style("text-anchor", "middle")
                    .style("fill", self.getBeingColor ? self.getBeingColor(d) : '#666666')
                    .style("font-size", "8px")
                    .style("font-weight", "normal")
                    .style("pointer-events", "none")
                    .style("opacity", "0.8")
                    .text(`[${d.genesis?.type || 'unknown'}]`);
            });
    }

    initForceSimulation(nodes) {
        // Zatrzymaj poprzednią symulację jeśli istnieje
        if (this.simulation) {
            this.simulation.stop();
        }

        // Utwórz symulację D3 force
        this.simulation = d3.forceSimulation(nodes)
            .force("charge", d3.forceManyBody()
                .strength(d => {
                    // Lux ma silniejsze odpychanie ale kontrolowane
                    if (this.isLuxAgent(d)) return -800;
                    // Główna intencja ma średnie odpychanie
                    if (d.soul === '11111111-1111-1111-1111-111111111111') return -300;
                    return -200; // Zbalansowane odpychanie
                }))
            .force("center", d3.forceCenter(0, 0).strength(0.8)) // Silniejsza siła center - trzyma byty w zasięgu wzroku
            .force("collision", d3.forceCollide()
                .radius(d => {
                    if (this.isLuxAgent(d)) return 50;
                    if (d.soul === '11111111-1111-1111-1111-111111111111') return 25;
                    return Math.max(12, Math.min(30, (d.attributes?.energy_level || 50) / 3)); // Mniejsze ale wystarczające promienie
                })
                .strength(0.9)) // Silna kolizja ale nie maksymalna
            .force("radial", d3.forceRadial(d => {
                // Lux w centrum
                if (this.isLuxAgent(d)) return 0;
                // Główna intencja na bliskiej orbicie
                if (d.soul === '11111111-1111-1111-1111-111111111111') return 80;
                // Inne byty w kontrolowanej odległości
                return 60 + Math.random() * 120; // Maksymalnie 180px od centrum
            }, 0, 0).strength(0.3)) // Silniejsza siła radial dla kontroli pozycji
            .alphaMin(0.001) // Niższy próg zatrzymania dla lepszej stabilizacji
            .on("tick", () => {
                this.updateNodePositions();
            });

        // Ustaw początkowe pozycje
        nodes.forEach((d, index) => {
            if (this.isLuxAgent(d)) {
                d.x = 0;
                d.y = 0;
                d.fx = 0; // Zablokuj Lux w centrum
                d.fy = 0;
            } else if (d.soul === '11111111-1111-1111-1111-111111111111') {
                // Główna intencja na stałej orbicie
                d.x = 80;
                d.y = 0;
            } else if (!d.x || !d.y) {
                // Równomierne rozmieszczenie w okręgu - widoczne w zasięgu wzroku
                const angle = (index * 2 * Math.PI) / Math.max(nodes.length - 1, 1); // Równomierny podział kąta
                const radius = 80 + Math.random() * 60; // Kontrolowana odległość 80-140px
                d.x = Math.cos(angle) * radius;
                d.y = Math.sin(angle) * radius;
            }
        });
    }

    updateNodePositions() {
        if (!this.beingSelection) return;

        // Aktualizuj pozycje wszystkich bytów (oprócz specjalnych) z ograniczeniami
        this.beingSelection
            .filter(d => d.soul !== '11111111-1111-1111-1111-111111111111') // Główna intencja ma własną animację
            .attr("transform", d => {
                // Ogranicz pozycje do rozsądnego obszaru (maksymalnie 300px od centrum)
                const maxDistance = 300;
                let x = d.x || 0;
                let y = d.y || 0;

                // Jeśli byt jest zbyt daleko od centrum, przyciągnij go
                const distance = Math.sqrt(x * x + y * y);
                if (distance > maxDistance && !this.isLuxAgent(d)) {
                    const scale = maxDistance / distance;```python
                    x = x * scale;
                    y = y * scale;
                    // Aktualizuj pozycję w danych
                    d.x = x;
                    d.y = y;
                }

                return `translate(${x}, ${y})`;
            });

        // Aktualizuj pozycje relacji jeśli funkcja istnieje
        if (this.updateRelationshipPositions) {
            this.updateRelationshipPositions();
        }
    }

    // Obsługa przeciągania
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
        // Nie zwalniaj Lux
        if (!this.isLuxAgent(d)) {
            d.fx = null;
            d.fy = null;
        }
    }

    updateBeingPositions() {
        // Ta metoda już nie jest potrzebna - symulacja zarządza pozycjami
        if (this.simulation) {
            this.simulation.alpha(0.3).restart();
        }
    }

    updateDetailsLevel() {
        // Aktualizuj poziom szczegółowości na podstawie zoomu
        if (this.zoomLevel < 1) {
            this.detailsLevel = 1; // Tylko największe obiekty
        } else if (this.zoomLevel < 5) {
            this.detailsLevel = 2; // Główne obiekty z etykietami
        } else if (this.zoomLevel < 15) {
            this.detailsLevel = 3; // Wszystkie obiekty z szczegółami
        } else {
            this.detailsLevel = 4; // Maksymalne szczegóły, chmury punktów
        }

        // Przerenderuj z nowym poziomem szczegółowości
        this.renderBeings();
    }

    addUniverseEffects() {
        // Dodaj efekty dla wysokiego zoomu
        if (this.zoomLevel > 10) {
            // Można dodać chmury punktów dla danych
            this.addDataClouds();
        }
    }

    addDataClouds() {
        // Implementacja chmur punktów dla danych bytów
        const dataBeings = this.beings.filter(d => d.genesis?.type === 'data');

        dataBeings.forEach(being => {
            if (this.beingsPositions[being.soul]) {
                // Dodaj chmurę punktów reprezentującą dane
                const pos = this.beingsPositions[being.soul];
                const cloudSize = (being.attributes?.energy_level || 50) / 10;

                for (let i = 0; i < cloudSize; i++) {
                    this.effectsGroup.append("circle")
                        .attr("cx", pos.x + (Math.random() - 0.5) * 20)
                        .attr("cy", pos.y + (Math.random() - 0.5) * 20)
                        .attr("r", 1)
                        .attr("fill", this.getBeingColor(being))
                        .attr("opacity", 0.5);
                }
            }
        });
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
        // Zlikwidowano zaznaczanie bytów - teraz tylko logowanie
        console.log('Kliknięto byt:', being.soul, being.genesis?.name);
    }

    addBeing(being) {
        try {
            // Bezpieczna deserializacja nowego bytu
            const processedBeing = {
                soul: being.soul_uid || being.soul,
                soul_uid: being.soul_uid,
                genesis: being._soul?.genesis || being.genesis || { type: 'unknown', name: 'Unknown' },
                attributes: being._soul?.attributes || being.attributes || { energy_level: 50 },
                memories: being._soul?.memories || being.memories || [],
                self_awareness: being._soul?.self_awareness || being.self_awareness || {}
            };

            // Sprawdź czy byt już istnieje
            const existingIndex = this.beings.findIndex(b => 
                b.soul === processedBeing.soul || b.soul_uid === processedBeing.soul_uid);

            if (existingIndex !== -1) {
                // Zaktualizuj istniejący byt
                this.beings[existingIndex] = processedBeing;
            } else {
                // Dodaj nowy byt z losową pozycją startową
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

    updateBeingStyles() {
        // Zlikwidowano stylowanie zaznaczonych bytów
        if (this.beingSelection) {
            this.beingSelection.selectAll("circle")
                .attr("stroke", d => this.isLuxAgent(d) ? "#ffff00" : "#ffffff")
                .attr("stroke-width", 1);
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

    showBeingContextMenu(being, event) {
        const contextMenu = [
            {
                label: '🧬 Edytuj genetykę',
                action: () => this.editBeingGenetics(being)
            },
            {
                label: '📋 Szczegóły bytu',
                action: () => this.showBeingDetails(being)
            },
            {
                label: '🗑️ Usuń byt',
                action: () => this.deleteBeing(being),
                dangerous: true
            },
            {
                label: '🚀 Śledź orbitę',
                action: () => this.trackBeing(being)
            },
            {
                label: '⭐ Analiza spektralna',
                action: () => this.showSpectralAnalysis(being)
            }
        ];

        this.showContextMenu(contextMenu, event);
    }

    trackBeing(being) {
        // Śledź byt - przesuń widok żeby go śledzić
        const pos = this.beingsPositions[being.soul];
        if (pos) {
            this.svg.transition().duration(1000).call(
                this.zoom.transform,
                d3.zoomIdentity.translate(-pos.x, -pos.y).scale(5)
            );
        }
    }

    showOrbitalParams(being) {
        const params = being.attributes?.orbital_params;
        if (params) {
            alert(`Parametry orbitalne dla ${being.genesis?.name || being.soul}:
                Promień orbity: ${params.orbital_radius?.toFixed(1)}
                Prędkość orbitalna: ${params.orbital_speed?.toFixed(2)}
                Kąt obecny: ${(params.orbital_angle * 180 / Math.PI)?.toFixed(1)}°`);
        }
    }

    showSpectralAnalysis(being) {
        alert(`Analiza spektralna ${being.genesis?.name || being.soul}:
            Energia: ${being.attributes?.energy_level || 0}
            Typ: ${being.genesis?.type || 'unknown'}
            Masa (data): ${JSON.stringify(being.attributes).length} bajtów`);
    }

    editBeingGenetics(being) {
        this.createGeneticsEditor(being);
    }

    createGeneticsEditor(being) {
        // Usuń poprzedni edytor jeśli istnieje
        const existingEditor = document.getElementById('genetics-editor');
        if (existingEditor) {
            existingEditor.remove();
        }

        // Utwórz kontener edytora
        const editorContainer = document.createElement('div');
        editorContainer.id = 'genetics-editor';
        editorContainer.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 600px;
            max-height: 80vh;
            background: rgba(26, 26, 26, 0.98);
            border: 2px solid #00ff88;
            border-radius: 15px;
            padding: 20px;
            z-index: 3000;
            overflow-y: auto;
            backdrop-filter: blur(15px);
            box-shadow: 0 20px 40px rgba(0, 255, 136, 0.4);
        `;

        // Nagłówek
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            color: #00ff88;
            font-size: 18px;
            font-weight: bold;
        `;
        header.innerHTML = `
            <span>🧬 Genetyka Bytu: ${being.genesis?.name || being.soul?.slice(0, 8)}</span>
            <button id="close-genetics-editor" style="background: none; border: none; color: #00ff88; font-size: 24px; cursor: pointer;">×</button>
        `;

        // Sekcja Genesis
        const genesisSection = this.createEditableSection('Genesis', being.genesis || {}, [
            { key: 'name', label: 'Nazwa', type: 'text' },
            { key: 'type', label: 'Typ', type: 'select', options: ['function', 'class', 'data', 'task', 'component', 'message', 'scenario', 'agent'] },
            { key: 'source', label: 'Źródło', type: 'textarea' },
            { key: 'description', label: 'Opis', type: 'textarea' },
            { key: 'created_by', label: 'Utworzony przez', type: 'text' }
        ]);

        // Sekcja Attributes
        const attributesSection = this.createEditableSection('Atrybuty', being.attributes || {}, [
            { key: 'energy_level', label: 'Poziom energii', type: 'number', min: 0, max: 1000 },
            { key: 'trust_level', label: 'Poziom zaufania', type: 'number', min: 0, max: 1, step: 0.1 },
            { key: 'tags', label: 'Tagi (oddzielone przecinkami)', type: 'text' }
        ]);

        // Sekcja Self Awareness
        const selfAwarenessSection = this.createEditableSection('Samoświadomość', being.self_awareness || {}, [
            { key: 'confidence', label: 'Pewność siebie', type: 'number', min: 0, max: 1, step: 0.1 },
            { key: 'trust_level', label: 'Poziom zaufania', type: 'number', min: 0, max: 1, step: 0.1 },
            { key: 'introspection_depth', label: 'Głębokość introspekcji', type: 'number', min: 0, max: 1, step: 0.1 }
        ]);

        // Przyciski akcji
        const actionsDiv = document.createElement('div');
        actionsDiv.style.cssText = `
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 20px;
        `;
        actionsDiv.innerHTML = `
            <button id="save-genetics" style="background: #00ff88; color: #1a1a1a; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">💾 Zapisz zmiany</button>
            <button id="cancel-genetics" style="background: #ff4444; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">❌ Anuluj</button>
        `;

        // Składanie edytora
        editorContainer.appendChild(header);
        editorContainer.appendChild(genesisSection);
        editorContainer.appendChild(attributesSection);
        editorContainer.appendChild(selfAwarenessSection);
        editorContainer.appendChild(actionsDiv);
        document.body.appendChild(editorContainer);

        // Event listenery
        document.getElementById('close-genetics-editor').onclick = () => editorContainer.remove();
        document.getElementById('cancel-genetics').onclick = () => editorContainer.remove();
        document.getElementById('save-genetics').onclick = () => {
            this.saveBeingGenetics(being, editorContainer);
        };

        // Zamknięcie na ESC
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                editorContainer.remove();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    }

    createEditableSection(title, data, fields) {
        const section = document.createElement('div');
        section.style.cssText = `
            margin-bottom: 25px;
            padding: 15px;
            border: 1px solid #444;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.3);
        `;

        const sectionTitle = document.createElement('h3');
        sectionTitle.textContent = title;
        sectionTitle.style.cssText = `
            color: #00ff88;
            margin-bottom: 15px;
            font-size: 16px;
        `;
        section.appendChild(sectionTitle);

        fields.forEach(field => {
            const fieldDiv = document.createElement('div');
            fieldDiv.style.cssText = `margin-bottom: 12px;`;

            const label = document.createElement('label');
            label.textContent = field.label + ':';
            label.style.cssText = `
                display: block;
                color: #ccc;
                margin-bottom: 5px;
                font-size: 14px;
            `;

            let input;
            const currentValue = data[field.key];

            if (field.type === 'select') {
                input = document.createElement('select');
                field.options.forEach(option => {
                    const optionEl = document.createElement('option');
                    optionEl.value = option;
                    optionEl.textContent = option;
                    optionEl.selected = currentValue === option;
                    input.appendChild(optionEl);
                });
            } else if (field.type === 'textarea') {
                input = document.createElement('textarea');
                input.rows = 3;
                input.value = currentValue || '';
            } else {
                input = document.createElement('input');
                input.type = field.type || 'text';
                if (field.min !== undefined) input.min = field.min;
                if (field.max !== undefined) input.max = field.max;
                if (field.step !== undefined) input.step = field.step;

                if (field.key === 'tags' && Array.isArray(currentValue)) {
                    input.value = currentValue.join(', ');
                } else {
                    input.value = currentValue || '';
                }
            }

            input.dataset.field = field.key;
            input.dataset.section = title.toLowerCase();
            input.style.cssText = `
                width: 100%;
                padding: 8px;
                background: #333;
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
                font-family: inherit;
            `;

            fieldDiv.appendChild(label);
            fieldDiv.appendChild(input);
            section.appendChild(fieldDiv);
        });

        return section;
    }

    saveBeingGenetics(being, editorContainer) {
        try {
            // Zbierz dane z formularza
            const inputs = editorContainer.querySelectorAll('input, select, textarea');
            const updatedData = {
                genesis: { ...being.genesis },
                attributes: { ...being.attributes },
                self_awareness: { ...being.self_awareness }
            };

            inputs.forEach(input => {
                const field = input.dataset.field;
                const section = input.dataset.section;
                let value = input.value;

                // Specjalna obsługa różnych typów danych
                if (input.type === 'number') {
                    value = parseFloat(value) || 0;
                } else if (field === 'tags') {
                    value = value.split(',').map(tag => tag.trim()).filter(tag => tag);
                }

                if (section === 'genesis') {
                    updatedData.genesis[field] = value;
                } else if (section === 'atrybuty') {
                    updatedData.attributes[field] = value;
                } else if (section === 'samoświadomość') {
                    updatedData.self_awareness[field] = value;
                }
            });

            // Wyślij aktualizację do serwera
            if (this.socket && this.socket.connected) {
                this.socket.emit('update_being', {
                    soul: being.soul || being.soul_uid,
                    genesis: updatedData.genesis,
                    attributes: updatedData.attributes,
                    self_awareness: updatedData.self_awareness
                });

                this.showSuccessMessage('Genetyka bytu została zaktualizowana!');
                editorContainer.remove();
            } else {
                throw new Error('Brak połączenia z serwerem');
            }

        } catch (error) {
            console.error('Błąd zapisywania genetyki:', error);
            this.showErrorMessage('Błąd zapisywania: ' + error.message);
        }
    }

    deleteBeing(being) {
        // Potwierdź usunięcie
        const beingName = being.genesis?.name || being.soul?.slice(0, 8) || 'Nieznany byt';
        const confirmDelete = confirm(`Czy na pewno chcesz usunąć byt "${beingName}"?\n\nTa operacja jest nieodwracalna.`);

        if (confirmDelete) {
            if (this.socket && this.socket.connected) {
                console.log('🗑️ Usuwam byt:', being.soul);

                // Generuj unikalny ID zadania
                const taskId = `delete_${being.soul}_${Date.now()}`;
                
                // Dodaj nasłuchiwanie na odpowiedź z tym konkretnym task ID
                this.socket.once(`task_response_${taskId}`, (response) => {
                    console.log('🔄 Otrzymano odpowiedź na zadanie:', taskId, response);
                    
                    if (response.success) {
                        console.log('✅ Byt usunięty pomyślnie:', response);
                        this.showSuccessMessage(`Byt "${beingName}" został usunięty`);

                        // Usuń byt z lokalnej listy - sprawdź wszystkie możliwe identyfikatory
                        const targetSoul = being.soul || being.soul_uid;
                        const beforeCount = this.beings.length;
                        
                        this.beings = this.beings.filter(b => {
                            const bSoul = b.soul || b.soul_uid;
                            return bSoul !== targetSoul;
                        });
                        
                        const afterCount = this.beings.length;
                        console.log(`🔄 Usunięto ${beforeCount - afterCount} bytów z lokalnej listy`);

                        // Usuń relacje związane z tym bytem
                        if (this.relationships) {
                            const beforeRelCount = this.relationships.length;
                            this.relationships = this.relationships.filter(rel => 
                                rel.source_soul !== targetSoul && rel.target_soul !== targetSoul
                            );
                            const afterRelCount = this.relationships.length;
                            console.log(`🔗 Usunięto ${beforeRelCount - afterRelCount} relacji z lokalnej listy`);
                        }

                        // Zatrzymaj symulację przed re-renderowaniem
                        if (this.simulation) {
                            this.simulation.stop();
                        }

                        // Wyczyść graf przed ponownym renderowaniem
                        if (this.beingsGroup) {
                            this.beingsGroup.selectAll(".being").remove();
                        }
                        if (this.linksGroup) {
                            this.linksGroup.selectAll(".relationship").remove();
                        }

                        // Przerenderuj graf z nową listą bytów
                        this.renderUniverse();
                        this.updateStats();
                        
                        console.log(`📊 Graf zaktualizowany - pozostało ${this.beings.length} bytów`);
                    } else {
                        console.error('❌ Błąd usuwania bytu:', response);
                        this.showErrorMessage(`Błąd usuwania: ${response.error || 'Nieznany błąd'}`);
                    }
                });

                // Wyślij żądanie z task ID
                this.socket.emit('delete_being', {
                    soul: being.soul || being.soul_uid,
                    taskId: taskId
                });

                // Timeout po 10 sekundach
                setTimeout(() => {
                    this.socket.off(`task_response_${taskId}`);
                    this.showErrorMessage('Timeout - operacja usuwania nie została potwierdzona');
                }, 10000);

            } else {
                this.showErrorMessage('Brak połączenia z serwerem');
            }
        }
    }

    showBeingDetails(being) {
        // Utwórz okno szczegółów (read-only)
        const detailsContainer = document.createElement('div');
        detailsContainer.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 500px;
            max-height: 80vh;
            background: rgba(26, 26, 26, 0.98);
            border: 2px solid #0088ff;
            border-radius: 15px;
            padding: 20px;
            z-index: 3000;
            overflow-y: auto;
            backdrop-filter: blur(15px);
            box-shadow: 0 20px 40px rgba(0, 136, 255, 0.4);
        `;

        detailsContainer.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; color: #0088ff; font-size: 18px; font-weight: bold;">
                <span>📋 Szczegóły Bytu</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: #0088ff; font-size: 24px; cursor: pointer;">×</button>
            </div>

            <div style="color: #ccc; line-height: 1.6;">
                <h4 style="color: #00ff88; margin-bottom: 10px;">🧬 Genesis</h4>
                <pre style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px; overflow-x: auto; margin-bottom: 15px;">${JSON.stringify(being.genesis, null, 2)}</pre>

                <h4 style="color: #00ff88; margin-bottom: 10px;">⚡ Atrybuty</h4>
                <pre style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px; overflow-x: auto; margin-bottom: 15px;">${JSON.stringify(being.attributes, null, 2)}</pre>

                <h4 style="color: #00ff88; margin-bottom: 10px;">🧠 Samoświadomość</h4>
                <pre style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px; overflow-x: auto; margin-bottom: 15px;">${JSON.stringify(being.self_awareness, null, 2)}</pre>

                <h4 style="color: #00ff88; margin-bottom: 10px;">💭 Wspomnienia (${(being.memories || []).length})</h4>
                <pre style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px; overflow-x: auto;">${JSON.stringify(being.memories || [], null, 2)}</pre>
            </div>
        `;

        document.body.appendChild(detailsContainer);
    }

    showContextMenu(items, event) {
        // Usuń poprzednie menu kontekstowe
        const existingMenu = document.getElementById('context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }

        // Utwórz menu
        const menu = document.createElement('div');
        menu.id = 'context-menu';
        menu.style.cssText = `
            position: fixed;
            left: ${event.pageX}px;
            top: ${event.pageY}px;
            background: rgba(26, 26, 26, 0.98);
            border: 2px solid #00ff88;
            border-radius: 8px;
            padding: 8px 0;
            z-index: 4000;
            min-width: 200px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.3);
        `;

        items.forEach((item, index) => {
            const menuItem = document.createElement('div');
            menuItem.textContent = item.label;
            menuItem.style.cssText = `
                padding: 10px 15px;
                color: ${item.dangerous ? '#ff4444' : '#ccc'};
                cursor: pointer;
                transition: all 0.2s ease;
                border-bottom: ${index < items.length - 1 ? '1px solid #333' : 'none'};
            `;

            menuItem.onmouseover = () => {
                menuItem.style.background = item.dangerous ? 'rgba(255, 68, 68, 0.2)' : 'rgba(0, 255, 136, 0.2)';
                menuItem.style.color = item.dangerous ? '#ff6666' : '#00ff88';
            };

            menuItem.onmouseout = () => {
                menuItem.style.background = 'transparent';
                menuItem.style.color = item.dangerous ? '#ff4444' : '#ccc';
            };

            menuItem.onclick = () => {
                item.action();
                menu.remove();
            };

            menu.appendChild(menuItem);
        });

        document.body.appendChild(menu);

        // Usuń menu po kliknięciu poza nim
        const removeMenu = (e) => {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', removeMenu);
            }
        };
        setTimeout(() => document.addEventListener('click', removeMenu), 100);
    }

    // Metody kompatybilności z IntentionComponent
    processIntention(intention) {
        console.log('Universe processing intention:', intention);
        this.socket.emit('process_intention', {
            intention: intention,
            context: {
                selected_beings: this.selectedNodes.map(n => n.soul),
                universe_center: this.universeCenter,
                zoom_level: this.zoomLevel
            }
        });
    }

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

    handleNewComponent(componentData) {
        try {
            const containerId = componentData.config.container;

            // Utwórz kontener dla komponentu jeśli nie istnieje
            if (!document.getElementById(containerId)) {
                const componentContainer = document.createElement('div');
                componentContainer.id = containerId;
                componentContainer.className = 'lux-component-container';
                componentContainer.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    z-index: 1500;
                    background: rgba(26, 26, 26, 0.95);
                    border: 2px solid #00ff88;
                    border-radius: 10px;
                    padding: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 0 30px rgba(0, 255, 136, 0.3);
                `;

                // Dodaj nagłówek
                const header = document.createElement('div');
                header.className = 'component-header';
                header.style.cssText = `
                    color: #00ff88;
                    font-weight: bold;
                    margin-bottom: 15px;
                    text-align: center;
                    font-size: 18px;
                `;
                header.textContent = `Komponent: ${componentData.genesis.name}`;

                // Dodaj przycisk zamknięcia
                const closeBtn = document.createElement('button');
                closeBtn.innerHTML = '×';
                closeBtn.style.cssText = `
                    position: absolute;
                    top: 10px;
                    right: 15px;
                    background: none;
                    border: none;
                    color: #00ff88;
                    font-size: 24px;
                    cursor: pointer;
                    z-index: 10;
                `;
                closeBtn.onclick = () => {
                    componentContainer.remove();
                };

                componentContainer.appendChild(header);
                componentContainer.appendChild(closeBtn);
                document.body.appendChild(componentContainer);
            }

            // Wykonaj kod D3.js komponenta
            this.executeComponentCode(componentData.genesis.d3_code, componentData);

            // Pokaż komunikat o powodzeniu
            this.showSuccessMessage(`Komponent ${componentData.genesis.name} został utworzony!`);

        } catch (error) {
            console.error('Błąd tworzenia komponentu:', error);
            this.showErrorMessage('Błąd tworzenia komponentu D3.js');
        }
    }

    executeComponentCode(d3Code, componentData) {
        try {
            // Bezpieczne wykonanie kodu D3.js
            const scriptElement = document.createElement('script');
            scriptElement.textContent = d3Code;

            // Dodaj kod do head
            document.head.appendChild(scriptElement);

            // Usuń script po wykonaniu (opcjonalnie)
            setTimeout(() => {
                if (scriptElement.parentNode) {
                    scriptElement.parentNode.removeChild(scriptElement);
                }
            }, 1000);

            console.log('Kod D3.js komponenta wykonany pomyślnie');

        } catch (error) {
            console.error('Błąd wykonania kodu D3.js:', error);
            throw error;
        }
    }

    showSuccessMessage(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        successDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: #00ff88;
            color: #1a1a1a;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 2000;
            max-width: 300px;
            font-weight: bold;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
        `;

        document.body.appendChild(successDiv);

        // Usuń po 4 sekundach
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 4000);
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 5000);

            console.log(`Próba reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} za ${delay}ms`);

            // Aktualizuj status podczas próby reconnect
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
                        this.attemptReconnect(); // Spróbuj ponownie
                    }
                }
            }, delay);
        } else {
            console.log('Maksymalna liczba prób reconnect osiągnięta - resetuję licznik');
            this.showErrorMessage('Problemy z połączeniem - spróbuję ponownie...');

            // Reset licznika po 30 sekundach i spróbuj ponownie
            setTimeout(() => {
                this.reconnectAttempts = 0;
                this.attemptReconnect();
            }, 30000);
        }
    }

    throttledUpdate(data) {
        const now = Date.now();
        if (now - this.lastUpdateTime < this.updateThrottle) {
            return; // Skip update if too frequent
        }
        this.lastUpdateTime = now;
        this.updateUniverse(data);
    }

    showErrorMessage(message) {
        // Pokaż komunikat błędu w interfejsie
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;top: 100px;
            right: 20px;
            background: #ff4444;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 2000;
            max-width: 300px;
        `;

        document.body.appendChild(errorDiv);

        // Usuń po 5 sekundach
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    handleMainIntentionContext(data) {
        // Tutaj obsłuż dane kontekstu głównej intencji LuxOS
        console.log("Dane kontekstu głównej intencji LuxOS:", data);
        // Możesz np. wyświetlić informacje w specjalnym panelu UI
    }

    setupMainIntentionControls() {
        // Konfiguracja kontrolek dla głównej intencji LuxOS
        // Przyciski, suwaki, itp.
        console.log("Konfiguracja kontrolek dla głównej intencji LuxOS");
    }

    startHeartbeat() {
        // Wyczyść poprzedni heartbeat
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }

        // Wysyłaj ping co 30 sekund
        this.heartbeatInterval = setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('ping');
            }
        }, 30000);
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    destroy() {
        // Zatrzymaj wszystkie animacje i timery
        if (this.orbitalAnimationId) {
            cancelAnimationFrame(this.orbitalAnimationId);
            this.orbitalAnimationId = null;
        }
        // Zatrzymaj symulację fizyki
        if (this.simulation) {
            this.simulation.stop();
        }
        this.stopHeartbeat();
        if (this.socket) {
            this.socket.disconnect();
        }
    }

    startOrbitalAnimation() {
        // Zatrzymaj poprzednią animację jeśli istnieje
        if (this.orbitalAnimationId) {
            cancelAnimationFrame(this.orbitalAnimationId);
        }

        let lastTime = 0;
        const targetFPS = 60; // Zwiększone FPS dla płynniejszej animacji
        const interval = 1000 / targetFPS;

        const animate = (currentTime) => {
            if (currentTime - lastTime >= interval) {
                if (this.beingSelection) {
                    const time = currentTime * 0.002; // Zwiększona prędkość - widoczna dla oka

                    // Animuj główną intencję LuxOS na orbicie (jeśli istnieje)
                    this.beingSelection
                        .filter(d => d.soul === '11111111-1111-1111-1111-111111111111' || 
                                   (d.genesis?.type === 'message' && d.attributes?.metadata?.is_main_intention))
                        .attr("transform", d => {
                            const radius = 100; // Nieco większy promień
                            const speed = 1.0; // Znacznie szybsza prędkość
                            const x = Math.cos(time * speed) * radius;
                            const y = Math.sin(time * speed) * radius;
                            return `translate(${x}, ${y})`;
                        });
                }
                lastTime = currentTime;
            }

            this.orbitalAnimationId = requestAnimationFrame(animate);
        };

        // Rozpocznij animację
        animate(0);
    }

    // Metoda do zmiany rozmiaru grafu
    resizeGraph() {
        if (this.svg && this.container) {
            const containerRect = this.container.getBoundingClientRect();
            this.width = containerRect.width;
            this.height = containerRect.height;

            this.svg
                .attr("width", this.width)
                .attr("height", this.height);

            if (this.simulation) {
                this.simulation
                    .force("center", d3.forceCenter(this.width / 2, this.height / 2))
                    .alpha(0.3)
                    .restart();
            }
        }
    }

    // Metody pomocnicze
    getNodeColor(genesis) {
        if (typeof genesis === 'string') {
            try {
                genesis = JSON.parse(genesis);
            } catch (e) {
                return '#666';
            }
        }

        const type = genesis?.type || 'unknown';

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

    // Obsługa tick simulation
    this.simulation.on("tick", () => {
        if (this.updateNodePositions) this.updateNodePositions();
        if (this.updateRelationshipPositions) this.updateRelationshipPositions();
        if (this.updateRelationshipLabelPositions) this.updateRelationshipLabelPositions();
    });
}

// Zastąp LuxOSGraph nowym systemem wszechświata
window.LuxOSGraph = LuxOSUniverse;
window.luxOSUniverse = null;

// Style CSS dla wszechświata (zoptymalizowane)
const universeStyle = document.createElement('style');
universeStyle.innerHTML = `
    .being {
        transition: opacity 0.1s ease;
    }

    .being:hover {
        opacity: 0.8;
    }

    .lux-component-container {
        animation: componentAppear 0.2s ease-out;
    }

    @keyframes componentAppear {
        from { 
            opacity: 0; 
            transform: translate(-50%, -50%) scale(0.95);
        }
        to { 
            opacity: 1; 
            transform: translate(-50%, -50%) scale(1);
        }
    }

    .success-message {
        transition: transform 0.2s ease-out, opacity 0.2s ease-out;
    }

    #graph {
            width: calc(100% - 280px);
            height: calc(100vh - 70px - 120px);
            margin-left: 280px;
            background: radial-gradient(circle at 50% 50%, rgba(0, 255, 136, 0.1) 0%, transparent 50%);
            transition: all 0.3s ease;
            position: relative;
        }

        #graph.explorer-collapsed {
            width: calc(100% - 40px);
            margin-left: 40px;
        }
`;
document.head.appendChild(universeStyle);