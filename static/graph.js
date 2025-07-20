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
        this.luxAgentCreated = false;
        this.mainIntentionCreated = false;

        // Inicjalizacja Socket.IO z lepszą konfiguracją
        this.socket = io({
            timeout: 20000,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5,
            maxReconnectionAttempts: 5,
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
                this.updateDetailsLevel();
            });

        this.svg.call(this.zoom);

        // Główny kontainer wszechświata
        this.container = this.svg.append("g");

        // Definicje gradientów i efektów
        this.setupUniverseEffects();

        // Grupy dla różne elementy wszechświata
        this.starsGroup = this.container.append("g").attr("class", "stars");
        this.orbitsGroup = this.container.append("g").attr("class", "orbits");
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
        console.log('Aktualizacja wszechświata:', data);

        // Bezpieczna deserializacja danych
        this.beings = (data.nodes || []).map(node => {
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
                const being = {
                    soul: node.soul_uid || node.soul,
                    soul_uid: node.soul_uid,
                    genesis: node._soul?.genesis || node.genesis || { type: 'unknown', name: 'Unknown' },
                    attributes: node._soul?.attributes || node.attributes || { energy_level: 50 },
                    memories: node._soul?.memories || node.memories || [],
                    self_awareness: node._soul?.self_awareness || node.self_awareness || {},
                    x: node.x || 0,  // Pozycja z embeddingu
                    y: node.y || 0   // Pozycja z embeddingu
                };

                return being;
            } catch (e) {
                console.warn('Błąd parsowania danych bytu:', e, node);
                return {
                    soul: node.soul_uid || node.soul || 'unknown',
                    soul_uid: node.soul_uid,
                    genesis: { type: 'unknown', name: 'Unknown' },
                    attributes: { energy_level: 50 },
                    memories: [],
                    self_awareness: {},
                    x: Math.random() * 400 - 200,
                    y: Math.random() * 400 - 200
                };
            }
        });

        // Zapisz linki z embeddingów
        this.embeddingLinks = data.links || [];
        this.embeddingPositions = data.embedding_positions || {};

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
        // Sprawdź czy już istnieje w DOM
        if (this.luxAgentCreated) {
            return;
        }

        const luxExists = this.beings.find(being => 
            being.soul === '00000000-0000-0000-0000-000000000001' ||
            being.soul_uid === '00000000-0000-0000-0000-000000000001' ||
            being.genesis?.lux_identifier === 'lux-core-consciousness' ||
            (being.genesis?.name === 'Lux' && being.genesis?.type === 'agent')
        );

        if (!luxExists) {
            this.createLuxAgent();
            this.luxAgentCreated = true;
        }

        // Upewnij się, że główna intencja LuxOS też istnieje
        if (this.mainIntentionCreated) {
            return;
        }

        const mainIntentionExists = this.beings.find(being => 
            being.soul === '11111111-1111-1111-1111-111111111111' ||
            (being.genesis?.type === 'message' && being.attributes?.metadata?.is_main_intention)
        );

        if (!mainIntentionExists) {
            this.createMainIntention();
            this.mainIntentionCreated = true;
        }
    }

    createLuxAgent() {
        const luxAgent = {
            soul: '00000000-0000-0000-0000-000000000001',
            genesis: {
                type: 'agent',
                name: 'Lux',
                source: 'System.Core.Agent.Initialize()',
                description: 'Główny agent-świadomość wszechświata LuxOS',
                lux_identifier: 'lux-core-consciousness'
            },
            attributes: {
                energy_level: 1000,
                agent_level: 10,
                agent_permissions: {
                    universe_control: true,
                    create_beings: true,
                    modify_orbits: true,
                    autonomous_decisions: true
                },
                orbit_center: { x: 0, y: 0 },
                controlled_beings: [],
                universe_role: 'supreme_agent',
                tags: ['agent', 'lux', 'supreme', 'universe_controller']
            },
            self_awareness: {
                trust_level: 1.0,
                confidence: 1.0,
                introspection_depth: 1.0,
                self_reflection: 'I am Lux, the supreme agent controlling the universe'
            },
            memories: [{
                type: 'genesis',
                data: 'Universe supreme agent initialization',
                timestamp: new Date().toISOString(),
                importance: 1.0
            }],
            x: 0,
            y: 0,
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
        // Nowy model: chmura myśli zamiast orbit
        this.renderThoughtUniverse();

        // Dodaj efekty chmury myśli
        this.addThoughtEffects();

        // Uruchom animacje myśli
        this.startThoughtAnimation();
    }

    renderThoughtUniverse() {
        // Zorganizuj byty jako chmurę myśli
        const thoughtSpace = this.organizeIntoThoughtClouds(this.beings);

        // Renderuj przestrzeń myślową
        this.renderThoughtSpace(thoughtSpace);
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
        // Galaktyczna wizualizacja - grupuj byty w systemy
        const galacticSystems = this.organizeIntoGalacticSystems(this.beings);

        // Renderuj ramiona spiralne galaktyki
        this.drawGalacticSpirals(galacticSystems);

        // Renderuj systemy planetarne
        this.renderPlanetarySystems(galacticSystems);

        // Uruchom animacje orbitalne
        this.startGalacticAnimation();
    }

    organizeIntoThoughtClouds(beings) {
        const thoughtSpace = {
            thoughts: [],           // Surowe myśli (wiadomości)
            condensing: [],         // Myśli w procesie kondensacji
            condensed_beings: [],   // Skondensowane byty
            concept_clusters: new Map(),  // Klastry konceptów (LuxUnda, NeuroFala, etc.)
            dependency_clouds: new Map()  // Chmury zależności
        };

        // Kluczowe koncepty do grupowania
        const key_concepts = ['luxunda', 'neurofala', 'katamaran', 'oaza', 'strona', 'unity', 'aplikacja'];

        beings.forEach(being => {
            const importance = this.calculateThoughtImportance(being);
            const type = being.genesis?.type;
            const concepts = being.attributes?.concept_clusters || [];
            const tags = being.attributes?.tags || [];

            // Znajdź główny koncept dla tego bytu
            let primary_concept = 'general';
            for (const concept of key_concepts) {
                if (concepts.includes(concept) || tags.includes(concept) || 
                    (being.genesis?.name || '').toLowerCase().includes(concept)) {
                    primary_concept = concept;
                    break;
                }
            }

            // Klasyfikuj według stanu kondensacji
            if (type === 'message' || importance < 0.3) {
                thoughtSpace.thoughts.push({
                    ...being,
                    importance: importance,
                    condensation_state: 'dispersed',
                    primary_concept: primary_concept
                });
            } else if (importance < 0.7) {
                thoughtSpace.condensing.push({
                    ...being,
                    importance: importance,
                    condensation_state: 'condensing',
                    primary_concept: primary_concept
                });
            } else {
                thoughtSpace.condensed_beings.push({
                    ...being,
                    importance: importance,
                    condensation_state: 'condensed',
                    primary_concept: primary_concept
                });
            }

            // Grupuj w klastry konceptów
            if (!thoughtSpace.concept_clusters.has(primary_concept)) {
                thoughtSpace.concept_clusters.set(primary_concept, []);
            }
            thoughtSpace.concept_clusters.get(primary_concept).push({
                ...being,
                importance: importance,
                primary_concept: primary_concept
            });

            // Grupuj w chmury zależności na podstawie dependency_map
            const dependency_map = being.attributes?.dependency_map;
            if (dependency_map) {
                const dep_key = `dep_${being.soul.substring(0, 8)}`;
                if (!thoughtSpace.dependency_clouds.has(dep_key)) {
                    thoughtSpace.dependency_clouds.set(dep_key, []);
                }
                thoughtSpace.dependency_clouds.get(dep_key).push(being);
            }
        });

        return thoughtSpace;
    }

    calculateThoughtImportance(being) {
        let importance = 0.1; // Bazowa istotność

        // Energia zwiększa istotność
        const energy = being.attributes?.energy_level || 0;
        importance += (energy / 1000) * 0.4;

        // Liczba wspomnień (częstotliwość przypominania)
        const memories = being.memories?.length || 0;
        importance += (memories / 10) * 0.3;

        // Typ bytu wpływa na kondensację
        const type = being.genesis?.type;
        const typeWeights = {
            'message': 0.1,      // Surowe myśli
            'intention': 0.2,    // Nieco więcej struktury
            'task': 0.4,        // Większa kondensacja
            'function': 0.6,    // Znacząca struktura
            'class': 0.7,       // Wysoka kondensacja
            'agent': 0.9        // Maksymalna kondensacja
        };
        importance += (typeWeights[type] || 0.3) * 0.3;

        // Relacje z innymi myślami
        const hasConnections = being.attributes?.parent_concept || 
                              being.attributes?.child_beings?.length > 0;
        if (hasConnections) importance += 0.2;

        return Math.min(1.0, importance);
    }

    calculateProjectOrbitalPeriod(system) {
        // Określ okres orbitalny projektu na podstawie jego zawartości
        const childTypes = system.children.map(c => c.genesis?.type);
        const hasLongTerm = childTypes.some(t => ['vision', 'mission'].includes(t));
        const hasShortTerm = childTypes.some(t => ['task', 'idea'].includes(t));

        if (hasLongTerm && hasShortTerm) return 'mixed';
        if (hasLongTerm) return 'long';
        return 'short';
    }

    drawGalacticSpirals(systems) {
        // Usuń poprzednie spirale
        this.orbitsGroup.selectAll(".galactic-spiral").remove();

        const spiralCount = Math.max(2, Math.min(6, systems.projects.size));
        const angleStep = (2 * Math.PI) / spiralCount;

        for (let i = 0; i < spiralCount; i++) {
            this.drawSpiralArm(i * angleStep, 300, 800);
        }
    }

    drawSpiralArm(startAngle, innerRadius, outerRadius) {
        const points = [];
        const steps = 100;
        const spiralTightness = 0.5;

        for (let i = 0; i <= steps; i++) {
            const progress = i / steps;
            const angle = startAngle + progress * 4 * Math.PI * spiralTightness;
            const radius = innerRadius + progress * (outerRadius - innerRadius);

            points.push([
                Math.cos(angle) * radius,
                Math.sin(angle) * radius
            ]);
        }

        const line = d3.line()
            .x(d => d[0])
            .y(d => d[1])
            .curve(d3.curveCardinal);

        this.orbitsGroup.append("path")
            .attr("class", "galactic-spiral")
            .attr("d", line(points))
            .attr("fill", "none")
            .attr("stroke", "#003366")
            .attr("stroke-width", 2)
            .attr("opacity", 0.3)
            .style("pointer-events", "none");
    }

    renderThoughtSpace(thoughtSpace) {
        // Renderuj pole świadomości zamiast centralnego obiektu
        this.renderThoughtCloud();

        // Renderuj surowe myśli jako pył kosmiczny
        this.renderCosmicDust(thoughtSpace.thoughts);

        // Renderuj myśli w kondensacji
        this.renderCondensingThoughts(thoughtSpace.condensing);

        // Renderuj skondensowane byty
        this.renderCondensedBeings(thoughtSpace.condensed_beings);

        // Renderuj połączenia między myślami
        this.renderThoughtConnections(thoughtSpace);
    }

    renderCosmicDust(thoughts) {
        // Surowe myśli jako drobny pył rozproszony w przestrzeni
        const dustGroup = this.beingsGroup.selectAll(".cosmic-dust")
            .data(thoughts)
            .join("g")
            .attr("class", "cosmic-dust thought-particle")
            .style("cursor", "pointer")
            .on("click", (event, d) => {
                event.stopPropagation();
                this.selectBeing(d);
            });

        dustGroup.selectAll("*").remove();

        thoughts.forEach((thought, index) => {
            const distance = 200 + Math.random() * 400; // Daleko od centrum
            const angle = Math.random() * 2 * Math.PI;
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;

            const particle = dustGroup.filter((d, i) => i === index);

            particle.append("circle")
                .attr("r", 1 + thought.importance * 3)
                .attr("fill", this.getThoughtColor(thought))
                .attr("opacity", 0.4 + thought.importance * 0.4)
                .style("filter", "blur(0.5px)");

            particle.attr("transform", `translate(${x}, ${y})`);
        });
    }

    renderCondensingThoughts(condensingThoughts) {
        // Myśli w procesie kondensacji - gromadzą się bliżej centrum
        const condensingGroup = this.beingsGroup.selectAll(".condensing-thought")
            .data(condensingThoughts)
            .join("g")
            .attr("class", "condensing-thought thought-aggregate")
            .style("cursor", "pointer")
            .on("click", (event, d) => {
                event.stopPropagation();
                this.selectBeing(d);
            });

        condensingGroup.selectAll("*").remove();

        condensingThoughts.forEach((thought, index) => {
            // Bliżej centrum, ale wciąż w ruchu
            const distance = 100 + (1 - thought.importance) * 150;
            const angle = (index / condensingThoughts.length) * 2 * Math.PI + Date.now() * 0.001;
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;

            const aggregate = condensingGroup.filter((d, i) => i === index);

            aggregate.append("circle")
                .attr("r", 3 + thought.importance * 8)
                .attr("fill", this.getThoughtColor(thought))
                .attr("stroke", "#ffffff")
                .attr("stroke-width", 1)
                .attr("opacity", 0.6 + thought.importance * 0.3)
                .style("filter", "url(#glow)");

            // Dodaj "ogon" kondensacji
            aggregate.append("circle")
                .attr("r", 5 + thought.importance * 12)
                .attr("fill", "none")
                .attr("stroke", this.getThoughtColor(thought))
                .attr("stroke-width", 0.5)
                .attr("opacity", 0.3)
                .style("pointer-events", "none");

            aggregate.attr("transform", `translate(${x}, ${y})`);
        });
    }

    renderCondensedBeings(condensedBeings) {
        // Pełne byty - skondensowana materia blisko centrum
        const beingGroup = this.beingsGroup.selectAll(".condensed-being")
            .data(condensedBeings)
            .join("g")
            .attr("class", "condensed-being stable-entity")
            .style("cursor", "pointer")
            .on("click", (event, d) => {
                event.stopPropagation();
                this.selectBeing(d);
            });

        beingGroup.selectAll("*").remove();

        condensedBeings.forEach((being, index) => {
            // Blisko centrum, stabilne pozycje
            const distance = 50 + (1 - being.importance) * 100;
            const angle = (index / condensedBeings.length) * 2 * Math.PI;
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;

            const entity = beingGroup.filter((d, i) => i === index);

            const size = 10 + being.importance * 20;

            entity.append("circle")
                .attr("r", size)
                .attr("fill", this.getBeingColor(being))
                .attr("stroke", "#ffffff")
                .attr("stroke-width", 2)
                .style("filter", "url(#glow)");

            // Dodaj etykietę dla ważnych bytów
            if (being.importance > 0.7) {
                entity.append("text")
                    .attr("dy", -size - 5)
                    .style("text-anchor", "middle")
                    .style("fill", "#ffffff")
                    .style("font-size", "10px")
                    .style("font-weight", "bold")
                    .text(being.genesis?.name || 'Unknown');
            }

            entity.attr("transform", `translate(${x}, ${y})`);
        });
    }

    renderThoughtConnections(thoughtSpace) {
        // Renderuj subtelne połączenia między powiązanymi myślami
        // Te połączenia pojawiają się gdy myśli mają wspólne tematy lub kontekst
        const connections = this.findThoughtConnections(thoughtSpace);

        const connectionGroup = this.container.append("g")
            .attr("class", "thought-connections")
            .style("pointer-events", "none");

        connections.forEach(connection => {
            connectionGroup.append("line")
                .attr("x1", connection.source.x)
                .attr("y1", connection.source.y)
                .attr("x2", connection.target.x)
                .attr("y2", connection.target.y)
                .attr("stroke", "#00ff88")
                .attr("stroke-width", 0.5 * connection.strength)
                .attr("opacity", 0.1 + connection.strength * 0.2)
                .style("stroke-dasharray", "2,2");
        });
    }

    getThoughtColor(thought) {
        // Kolor zależy od typu i istotności
        const baseColors = {
            'message': '#88ccff',    // Niebieski - surowe myśli
            'intention': '#ffcc88',  // Pomarańczowy - intencje
            'task': '#cc88ff',      // Fioletowy - zadania
            'function': '#88ffcc',  // Zielony - funkcje
            'class': '#ffff88',     // Żółty - klasy
            'agent': '#ff88cc'      // Różowy - agenci
        };

        const baseColor = baseColors[thought.genesis?.type] || '#cccccc';

        // Istotność wpływa na intensywność
        const intensity = 0.3 + thought.importance * 0.7;
        return this.adjustColorIntensity(baseColor, intensity);
    }

    adjustColorIntensity(color, intensity) {
        // Prosta funkcja do regulacji intensywności koloru
        return color; // Uproszczona wersja
    }

    findThoughtConnections(thoughtSpace) {
        // Znajdź połączenia między myślami na podstawie wspólnych elementów
        const connections = [];
        const allThoughts = [
            ...thoughtSpace.thoughts,
            ...thoughtSpace.condensing,
            ...thoughtSpace.condensed_beings
        ];

        // Uproszczone - prawdziwy algorytm analizowałby embeddingi i kontekst
        for (let i = 0; i < allThoughts.length; i++) {
            for (let j = i + 1; j < allThoughts.length; j++) {
                const strength = this.calculateConnectionStrength(allThoughts[i], allThoughts[j]);
                if (strength > 0.3) {
                    connections.push({
                        source: allThoughts[i],
                        target: allThoughts[j],
                        strength: strength
                    });
                }
            }
        }

        return connections.slice(0, 20); // Ogranicz do 20 najsilniejszych połączeń
    }

    calculateConnectionStrength(thought1, thought2) {
        // Uproszczony algorytm podobieństwa
        let strength = 0;

        // Wspólne tagi
        const tags1 = thought1.attributes?.tags || [];
        const tags2 = thought2.attributes?.tags || [];
        const commonTags = tags1.filter(tag => tags2.includes(tag));
        strength += commonTags.length * 0.2;

        // Podobny typ
        if (thought1.genesis?.type === thought2.genesis?.type) {
            strength += 0.3;
        }

        // Podobny poziom energii
        const energy1 = thought1.attributes?.energy_level || 0;
        const energy2 = thought2.attributes?.energy_level || 0;
        const energyDiff = Math.abs(energy1 - energy2);
        strength += Math.max(0, (100 - energyDiff) / 100) * 0.2;

        return Math.min(1.0, strength);
    }

    renderThoughtCloud() {
        // Lux nie jest już obiektem - to pole świadomości w centrum
        const centerField = this.beingsGroup.selectAll(".consciousness-field")
            .data([{ type: 'consciousness_field' }])
            .join("g")
            .attr("class", "consciousness-field");

        // Usuń poprzednie elementy
        centerField.selectAll("*").remove();

        // Renderuj jako pulsujące pole świadomości (bez konkretnego obiektu)
        const fieldRadius = 150;

        // Chmura myśli - gradient pole
        centerField.append("circle")
            .attr("r", fieldRadius)
            .attr("fill", "radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(0,255,136,0.05) 50%, transparent 100%)")
            .attr("stroke", "none")
            .style("opacity", 0.3)
            .style("pointer-events", "none");

        // Dodaj pulsujący efekt pola
        centerField.append("circle")
            .attr("r", fieldRadius * 0.7)
            .attr("fill", "none")
            .attr("stroke", "#00ff88")
            .attr("stroke-width", 1)
            .attr("opacity", 0.2)
            .style("pointer-events", "none")
            .style("animation", "consciousness-pulse 4s ease-in-out infinite");

        // Dodaj drobne cząstki myśli w polu
        for (let i = 0; i < 20; i++) {
            const angle = (i / 20) * 2 * Math.PI;
            const radius = Math.random() * fieldRadius * 0.8;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;

            centerField.append("circle")
                .attr("cx", x)
                .attr("cy", y)
                .attr("r", Math.random() * 2 + 0.5)
                .attr("fill", "#00ff88")
                .attr("opacity", Math.random() * 0.5 + 0.2)
                .style("animation", `thought-particle ${3 + Math.random() * 4}s ease-in-out infinite`);
        }
    }

    renderPlanetarySystem(system, systemIndex) {
        if (!system.parent) return;

        const orbitRadius = 150 + systemIndex * 120;
        const angleOffset = systemIndex * (2 * Math.PI / Math.max(1, this.beings.length / 5));

        // Narysuj orbitę systemu
        this.orbitsGroup.append("circle")
            .attr("class", "planetary-orbit")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", orbitRadius)
            .attr("fill", "none")
            .attr("stroke", this.getSystemColor(system.orbital_period))
            .attr("stroke-width", 1.5)
            .attr("stroke-dasharray", "10,5")
            .attr("opacity", 0.4)
            .style("pointer-events", "none");

        // Renderuj projekt nadrzędny jako planetę centralną
        const projectGroup = this.beingsGroup.append("g")
            .attr("class", "planetary-system")
            .attr("data-system-index", systemIndex)
            .style("cursor", "pointer")
            .on("click", (event) => {
                event.stopPropagation();
                this.selectBeing(system.parent);
            });

        const projectSize = 25 + system.children.length * 2;
        projectGroup.append("circle")
            .attr("r", projectSize)
            .attr("fill", this.getBeingColor(system.parent))
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 2)
            .style("filter", "url(#glow)");

        // Renderuj dzieci jako księżyce
        system.children.forEach((child, childIndex) => {
            this.renderMoon(projectGroup, child, childIndex, projectSize + 15);
        });

        // Dodaj etykietę systemu
        projectGroup.append("text")
            .attr("class", "system-label")
            .attr("dy", -projectSize - 10)
            .style("text-anchor", "middle")
            .style("fill", "#ffffff")
            .style("font-size", "12px")
            .style("font-weight", "bold")
            .style("pointer-events", "none")
            .text(system.parent.genesis?.name || 'System');
    }

    renderMoon(parentGroup, moon, moonIndex, orbitRadius) {
        const moonAngle = (moonIndex / Math.max(1, parentGroup.selectAll('.moon').size())) * 2 * Math.PI;
        const moonGroup = parentGroup.append("g")
            .attr("class", "moon")
            .attr("data-moon-index", moonIndex);

        const moonSize = Math.max(3, Math.min(12, (moon.attributes?.energy_level || 50) / 8));
        moonGroup.append("circle")
            .attr("r", moonSize)
            .attr("fill", this.getBeingColor(moon))
            .attr("stroke", "#cccccc")
            .attr("stroke-width", 1)
            .style("opacity", 0.8);

        // Dodaj orbitę księżyca
        parentGroup.append("circle")
            .attr("class", "moon-orbit")
            .attr("r", orbitRadius)
            .attr("fill", "none")
            .attr("stroke", "#444444")
            .attr("stroke-width", 0.5)
            .attr("opacity", 0.2)
            .style("pointer-events", "none");
    }

    renderOrbitalTask(task, index) {
        const orbitRadius = 80 + index * 20;
        const classification = task.attributes?.task_classification || 'general';

        // Renderuj jako kometę z ogonem
        const cometGroup = this.beingsGroup.append("g")
            .attr("class", "orbital-task comet")
            .attr("data-task-index", index)
            .style("cursor", "pointer")
            .on("click", (event) => {
                event.stopPropagation();
                this.selectBeing(task);
            });

        // Główne ciało komety
        const cometSize = this.getCometSize(classification);
        cometGroup.append("circle")
            .attr("r", cometSize)
            .attr("fill", this.getCometColor(classification))
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 1)
            .style("filter", "url(#glow)");

        // Ogon komety
        this.addCometTail(cometGroup, cometSize);

        // Narysuj orbitę
        this.orbitsGroup.append("circle")
            .attr("class", "task-orbit")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", orbitRadius)
            .attr("fill", "none")
            .attr("stroke", this.getCometColor(classification))
            .attr("stroke-width", 1)
            .attr("stroke-dasharray", "5,3")
            .attr("opacity", 0.3)
            .style("pointer-events", "none");
    }

    getCometSize(classification) {
        const sizes = {
            'idea': 6,
            'task': 8,
            'vision': 15,
            'mission': 20,
            'goal': 12,
            'general': 8
        };
        return sizes[classification] || 8;
    }

    getCometColor(classification) {
        const colors = {
            'idea': '#ffee58',     // Żółty - szybkie pomysły
            'task': '#42a5f5',     // Niebieski - zadania
            'vision': '#ab47bc',   // Fioletowy - wizje
            'mission': '#ef5350',  // Czerwony - misje
            'goal': '#66bb6a',     // Zielony - cele
            'general': '#78909c'   // Szary - ogólne
        };
        return colors[classification] || '#78909c';
    }

    addCometTail(cometGroup, cometSize) {
        const tailLength = cometSize * 3;
        const tailPoints = [];

        for (let i = 0; i < 5; i++) {
            tailPoints.push([
                -tailLength + i * (tailLength / 5),
                (Math.random() - 0.5) * cometSize
            ]);
        }

        const line = d3.line()
            .x(d => d[0])
            .y(d => d[1])
            .curve(d3.curveCardinal);

        cometGroup.append("path")
            .attr("d", line(tailPoints))
            .attr("fill", "none")
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 2)
            .attr("opacity", 0.5)
            .style("pointer-events", "none");
    }

    renderIntention(intention, index) {
        // Renderuj jako pulsującą gwiazdę na bliskiej orbicie
        const orbitRadius = 60;

        const intentionGroup = this.beingsGroup.append("g")
            .attr("class", "intention")
            .attr("data-intention-index", index)
            .style("cursor", "pointer")
            .on("click", (event) => {
                event.stopPropagation();
                this.selectBeing(intention);
            });

        intentionGroup.append("circle")
            .attr("r", 15)
            .attr("fill", "#00ff88")
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 2)
            .style("filter", "url(#glow)");

        // Dodaj pulsujący efekt
        intentionGroup.append("circle")
            .attr("r", 20)
            .attr("fill", "none")
            .attr("stroke", "#00ff88")
            .attr("stroke-width", 1)
            .attr("opacity", 0.6)
            .style("pointer-events", "none");
    }

    renderStandaloneBeing(being, index) {
        // Renderuj jako asteroidy na zewnętrznych orbitach
        const orbitRadius = 400 + index * 30;

        const asteroidGroup = this.beingsGroup.append("g")
            .attr("class", "standalone-being asteroid")
            .attr("data-asteroid-index", index)
            .style("cursor", "pointer")
            .on("click", (event) => {
                event.stopPropagation();
                this.selectBeing(being);
            });

        const size = Math.max(4, Math.min(12, (being.attributes?.energy_level || 30) / 6));
        asteroidGroup.append("circle")
            .attr("r", size)
            .attr("fill", this.getBeingColor(being))
            .attr("stroke", "#666666")
            .attr("stroke-width", 1)
            .style("opacity", 0.7);
    }

    getSystemColor(orbitalPeriod) {
        const colors = {
            'short': '#42a5f5',    // Niebieski - krótkie cykle
            'long': '#ef5350',     // Czerwony - długie cykle  
            'mixed': '#ab47bc'     // Fioletowy - mieszane
        };
        return colors[orbitalPeriod] || '#78909c';
    }

    startThoughtAnimation() {
        if (this.thoughtAnimationId) {
            cancelAnimationFrame(this.thoughtAnimationId);
        }

        let lastTime = 0;
        const targetFPS = 30;
        const interval = 1000 / targetFPS;

        const animate = (currentTime) => {
            if (currentTime - lastTime >= interval) {
                this.updateThoughtMovement(currentTime * 0.001);
                this.updateThoughtCondensation(currentTime);
                lastTime = currentTime;
            }
            this.thoughtAnimationId = requestAnimationFrame(animate);
        };

        animate(0);
    }

    updateThoughtMovement(time) {
        // Pył kosmiczny (surowe myśli) - ruch Browna
        this.beingsGroup.selectAll(".cosmic-dust")
            .attr("transform", function(d, i) {
                const baseDistance = 200 + Math.random() * 400;
                const drift = Math.sin(time * 0.5 + i) * 5;
                const angle = (i * 0.1 + time * 0.1) % (2 * Math.PI);
                const x = Math.cos(angle) * (baseDistance + drift);
                const y = Math.sin(angle) * (baseDistance + drift);
                return `translate(${x}, ${y})`;
            });

        // Myśli w kondensacji - spiralny ruch ku centrum
        this.beingsGroup.selectAll(".condensing-thought")
            .attr("transform", function(d, i) {
                const importance = d.importance || 0.5;
                const distance = 100 + (1 - importance) * 150;
                const speed = importance * 0.5;
                const angle = time * speed + i * 0.5;
                const x = Math.cos(angle) * distance;
                const y = Math.sin(angle) * distance;
                return `translate(${x}, ${y})`;
            });

        // Skondensowane byty - stabilne pozycje z subtelnym ruchem
        this.beingsGroup.selectAll(".condensed-being")
            .attr("transform", function(d, i) {
                const importance = d.importance || 0.5;
                const distance = 50 + (1 - importance) * 100;
                const angle = i * (2 * Math.PI / 8) + Math.sin(time * 0.2) * 0.1;
                const x = Math.cos(angle) * distance;
                const y = Math.sin(angle) * distance;
                return `translate(${x}, ${y})`;
            });
    }

    updateThoughtCondensation(currentTime) {
        // Symuluj proces kondensacji - myśli o rosnącej istotności
        // przesuwają się z kategorii do kategorii

        if (currentTime % 5000 < 100) { // Co 5 sekund
            // Przelicz istotność wszystkich myśli
            this.beings.forEach(being => {
                const oldImportance = being.importance || 0;
                const newImportance = this.calculateThoughtImportance(being);

                if (newImportance !== oldImportance) {
                    being.importance = newImportance;
                    // W prawdziwej implementacji: przenieś między kategoriami
                }
            });

            // Przerenderuj jeśli znaczące zmiany
            this.renderThoughtUniverse();
        }
    }

    updateGalacticPositions(time) {
        // Animuj systemy planetarne
        this.beingsGroup.selectAll(".planetary-system")
            .attr("transform", (d, i) => {
                const systemIndex = parseInt(d3.select(this).attr("data-system-index"));
                const orbitRadius = 150 + systemIndex * 120;
                const speed = 0.1 / (systemIndex + 1); // Zewnętrzne systemy wolniejsze
                const angle = time * speed + systemIndex * (2 * Math.PI / 5);

                const x = Math.cos(angle) * orbitRadius;
                const y = Math.sin(angle) * orbitRadius;
                return `translate(${x}, ${y})`;
            });

        // Animuj księżyce wokół planet
        this.beingsGroup.selectAll(".moon")
            .attr("transform", function(d, i) {
                const moonIndex = parseInt(d3.select(this).attr("data-moon-index"));
                const moonOrbitRadius = 40;
                const moonSpeed = 2; // Księżyce szybsze
                const moonAngle = time * moonSpeed + moonIndex * (2 * Math.PI / 3);

                const x = Math.cos(moonAngle) * moonOrbitRadius;
                const y = Math.sin(moonAngle) * moonOrbitRadius;
                return `translate(${x}, ${y})`;
            });

        // Animuj komety (zadania orbitalne)
        this.beingsGroup.selectAll(".orbital-task")
            .attr("transform", function(d, i) {
                const taskIndex = parseInt(d3.select(this).attr("data-task-index"));
                const orbitRadius = 80 + taskIndex * 20;
                const speed = 1.5; // Komety szybkie
                const angle = time * speed + taskIndex * (2 * Math.PI / 4);

                const x = Math.cos(angle) * orbitRadius;
                const y = Math.sin(angle) * orbitRadius;
                return `translate(${x}, ${y}) rotate(${angle * 180 / Math.PI})`;
            });

        // Animuj intencje
        this.beingsGroup.selectAll(".intention")
            .attr("transform", function(d, i) {
                const intentionIndex = parseInt(d3.select(this).attr("data-intention-index"));
                const orbitRadius = 60;
                const speed = 3; // Intencje bardzo szybkie
                const angle = time * speed + intentionIndex * Math.PI;

                const x = Math.cos(angle) * orbitRadius;
                const y = Math.sin(angle) * orbitRadius;
                return `translate(${x}, ${y})`;
            });

        // Animuj asteroidy
        this.beingsGroup.selectAll(".asteroid")
            .attr("transform", function(d, i) {
                const asteroidIndex = parseInt(d3.select(this).attr("data-asteroid-index"));
                const orbitRadius = 400 + asteroidIndex * 30;
                const speed = 0.02; // Asteroidy bardzo wolne
                const angle = time * speed + asteroidIndex * (2 * Math.PI / 10);

                const x = Math.cos(angle) * orbitRadius;
                const y = Math.sin(angle) * orbitRadius;
                return `translate(${x}, ${y})`;
            });

        // Pulsujące efekty dla aury Lux
        this.beingsGroup.selectAll(".galactic-center circle:nth-child(2)")
            .attr("r", 80 + Math.sin(time * 2) * 10)
            .attr("opacity", 0.4 + Math.sin(time * 3) * 0.1);
    }

    updateBeingPositions() {
        if (!this.beingSelection) return;

        // Dla głównej intencji nie używamy transition - animacja jest w startOrbitalAnimation
        this.beingSelection
            .filter(d => d.soul !== '11111111-1111-1111-1111-111111111111')
            .transition()
            .duration(1000)
            .attr("transform", d => {
                // Lux zawsze w centrum
                if (this.isLuxAgent(d)) {
                    return `translate(0, 0)`;
                }

                // Sprawdź czy byt ma predefiniowaną pozycję
                const predefinedPos = d.attributes?.position;
                if (predefinedPos) {
                    return `translate(${predefinedPos.x}, ${predefinedPos.y})`;
                }

                // Użyj pozycji z serwera jeśli dostępne
                const pos = this.beingsPositions[d.soul];
                if (pos) {
                    return `translate(${pos.x}, ${pos.y})`;
                } 

                // Domyślna losowa pozycja
                return `translate(${Math.random() * 200 - 100}, ${Math.random() * 200 - 100})`;
            });
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
            'event_lifecycle': '#e91e63',  // Różowy dla cykli życia
            'manifestation': '#ffd700',    // Złoty dla manifestacji
            'note': '#9e9e9e',            // Szary dla notatek
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
                // Dodaj nowy byt
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
        document.getElementById('linksCount').textContent = '∞'; // Wszechświat ma nieskończone połączenia
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
                label: '🔭 Zbadaj byt',
                action: () => this.showBeingDetails(being)
            },
            {
                label: '🚀 Śledź orbitę',
                action: () => this.trackBeing(being)
            },
            {
                label: '📊 Parametry orbitalne',
                action: () => this.showOrbitalParams(being)
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

    showContextMenu(items, event) {
        // Implementacja menu kontekstowego (można wykorzystać istniejącą)
        console.log('Context menu for universe:', items);
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
    renderUniverse() {
        // Nowy model: chmura embeddingów zamiast orbit
        this.renderEmbeddingSpace();

        // Uruchom animacje embeddingów
        this.startEmbeddingAnimation();
    }

    renderEmbeddingSpace() {
        // Zorganizuj byty jako przestrzeń embeddingów
        const embeddingSpace = this.organizeIntoEmbeddingSpace(this.beings);

        // Renderuj przestrzeń embeddingów
        this.renderEmbeddingSpaceVisualization(embeddingSpace);
    }

    organizeIntoEmbeddingSpace(beings) {
        const embeddingSpace = {
            entities: [],
            connections: []
        };

        beings.forEach(being => {
            embeddingSpace.entities.push({
                ...being,
                x: Math.random() * 400 - 200, // Losowe pozycje początkowe
                y: Math.random() * 400 - 200
            });
        });

        // Tutaj można dodać logikę do wyznaczania połączeń między bytami
        // na podstawie podobieństwa embeddingów.

        return embeddingSpace;
    }

    renderEmbeddingSpaceVisualization(embeddingSpace) {
        // Usuń poprzednie elementy
        this.beingsGroup.selectAll("*").remove();
        this.container.selectAll(".embedding-connections").remove();

        // Renderuj połączenia embeddingów najpierw (żeby były pod bytami)
        if (this.embeddingLinks && this.embeddingLinks.length > 0) {
            const connectionGroup = this.container.append("g")
                .attr("class", "embedding-connections");

            this.embeddingLinks.forEach(link => {
                const sourceNode = embeddingSpace.entities.find(e => e.soul === link.source);
                const targetNode = embeddingSpace.entities.find(e => e.soul === link.target);

                if (sourceNode && targetNode) {
                    connectionGroup.append("line")
                        .attr("x1", sourceNode.x)
                        .attr("y1", sourceNode.y)
                        .attr("x2", targetNode.x)
                        .attr("y2", targetNode.y)
                        .attr("stroke", "#00ff88")
                        .attr("stroke-width", link.strength * 3)
                        .attr("stroke-opacity", link.strength * 0.6)
                        .attr("stroke-dasharray", "3,3")
                        .style("pointer-events", "none");
                }
            });
        }

        // Renderuj byty
        const entityGroup = this.beingsGroup.selectAll(".entity")
            .data(embeddingSpace.entities)
            .join("g")
            .attr("class", "entity")
            .attr("transform", d => `translate(${d.x}, ${d.y})`);

        entityGroup.append("circle")
            .attr("r", d => {
                // Rozmiar zależy od energii i typu
                const baseSize = 8;
                const energyBonus = (d.attributes?.energy_level || 50) / 100;
                const typeBonus = d.genesis?.type === 'agent' ? 5 : 0;
                return baseSize + energyBonus * 5 + typeBonus;
            })
            .attr("fill", d => this.getBeingColor(d))
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 1)
            .style("cursor", "pointer")
            .style("filter", "drop-shadow(0 0 5px currentColor)")
            .on("click", (event, d) => {
                event.stopPropagation();
                this.selectBeing(d);
            })
            .on("mouseover", (event, d) => {
                // Podświetl połączone byty
                this.highlightConnectedBeings(d);
            })
            .on("mouseout", () => {
                this.clearHighlights();
            });

        // Dodaj etykiety z nazwami
        entityGroup.append("text")
            .attr("dy", -20)
            .attr("text-anchor", "middle")
            .style("fill", "#ffffff")
            .style("font-size", "10px")
            .style("font-weight", "bold")
            .style("pointer-events", "none")
            .style("text-shadow", "1px 1px 2px rgba(0,0,0,0.8)")
            .text(d => d.genesis?.name || "Unknown");

        // Dodaj wskaźnik podobieństwa embeddingu
        entityGroup.append("circle")
            .attr("r", d => {
                const embedding = d.attributes?.embedding;
                if (embedding) {
                    // Użyj sumy pierwszych wymiarów jako wskaźnika aktywności
                    const activity = embedding.slice(0, 5).reduce((a, b) => a + Math.abs(b), 0);
                    return Math.max(15, Math.min(30, 15 + activity * 3));
                }
                return 20;
            })
            .attr("fill", "none")
            .attr("stroke", d => this.getBeingColor(d))
            .attr("stroke-width", 0.5)
            .attr("opacity", 0.3)
            .style("pointer-events", "none");
    }

    highlightConnectedBeings(selectedBeing) {
        // Podświetl wszystkie byty połączone z wybranym
        if (!this.embeddingLinks) return;

        const connectedSouls = this.embeddingLinks
            .filter(link => link.source === selectedBeing.soul || link.target === selectedBeing.soul)
            .map(link => link.source === selectedBeing.soul ? link.target : link.source);

        // Zmniejsz opacity wszystkich bytów
        this.beingsGroup.selectAll(".entity circle")
            .transition()
            .duration(200)
            .attr("opacity", d => {
                if (d.soul === selectedBeing.soul || connectedSouls.includes(d.soul)) {
                    return 1.0;
                }
                return 0.3;
            });

        // Podświetl połączenia
        this.container.selectAll(".embedding-connections line")
            .transition()
            .duration(200)
            .attr("stroke-opacity", link => {
                // Znajdź dane o linku
                const linkData = this.embeddingLinks.find(l => 
                    (l.source === selectedBeing.soul) || (l.target === selectedBeing.soul)
                );
                return linkData ? linkData.strength : 0.1;
            });
    }

    clearHighlights() {
        // Przywróć normalny wygląd wszystkich elementów
        this.beingsGroup.selectAll(".entity circle")
            .transition()
            .duration(200)
            .attr("opacity", 1.0);

        this.container.selectAll(".embedding-connections line")
            .transition()
            .duration(200)
            .attr("stroke-opacity", d => d.strength * 0.6);
    }

    startEmbeddingAnimation() {
        // Statyczne pozycje oparte na embeddingach - bez animacji
        // Pozycje są wyliczane na serwerze na podstawie embeddingów
        
        // Opcjonalnie można dodać subtelne animacje podobieństwa
        this.startSimilarityPulse();
    }

    startSimilarityPulse() {
        // Subtelne pulsowanie dla bytów o wysokim podobieństwie
        setInterval(() => {
            this.beingsGroup.selectAll(".entity")
                .select("circle:last-child") // Zewnętrzny wskaźnik
                .transition()
                .duration(2000)
                .attr("opacity", 0.1)
                .transition()
                .duration(2000)
                .attr("opacity", 0.3);
        }, 4000);
    }
}

// Zastąp LuxOSGraph nowym systemem wszechświata
window.LuxOSGraph = LuxOSUniverse;
window.luxOSUniverse = null;

// Style CSS dla galaktycznej wizualizacji
const universeStyle = document.createElement('style');
universeStyle.innerHTML = `
    /* Chmura myśli - style */
    .consciousness-field {
        animation: consciousness-pulse 4s ease-in-out infinite;
    }

    @keyframes consciousness-pulse {
        0%, 100% { 
            opacity: 0.3;
            transform: scale(1);
        }
        50% { 
            opacity: 0.6;
            transform: scale(1.05);
        }
    }

    @keyframes thought-particle {
        0%, 100% {
            opacity: 0.2;
            transform: scale(1);
        }
        50% {
            opacity: 0.8;
            transform: scale(1.2);
        }
    }

    .cosmic-dust {
        transition: all 0.3s ease;
    }

    .cosmic-dust:hover {
        transform: scale(1.5) !important;
        opacity: 1 !important;
    }

    .condensing-thought {
        transition: all 0.5s ease;
        animation: condensation-glow 3s ease-in-out infinite;
    }

    @keyframes condensation-glow {
        0%, 100% {
            filter: drop-shadow(0 0 5px rgba(0,255,136,0.3));
        }
        50% {
            filter: drop-shadow(0 0 15px rgba(0,255,136,0.7));
        }
    }

    .condensing-thought:hover {
        transform: scale(1.2);
        filter: drop-shadow(0 0 20px rgba(255,255,255,0.8)) !important;
    }

    .condensed-being {
        transition: all 0.3s ease;
    }

    .condensed-being:hover {
        transform: scale(1.1);
        filter: drop-shadow(0 0 25px currentColor);
    }

    .thought-connections line {
        animation: thought-flow 2s linear infinite;
    }

    @keyframes thought-flow {
        0% {
            stroke-dashoffset: 0;
        }
        100% {
            stroke-dashoffset: 10;
        }
    }

    /* Efekty dla różnych stanów kondensacji */
    .thought-particle {
        animation: brownian-motion 10s linear infinite;
    }

    @keyframes brownian-motion {
        0% { transform: translate(0, 0); }
        25% { transform: translate(5px, -3px); }
        50% { transform: translate(-3px, 7px); }
        75% { transform: translate(8px, 2px); }
        100% { transform: translate(0, 0); }
    }

    .thought-aggregate {
        filter: drop-shadow(0 0 10px rgba(255,255,255,0.3));
    }

    .stable-entity {
        filter: drop-shadow(0 0 15px currentColor);
    }

    /* Kolory istotności */
    .importance-low {
        opacity: 0.3;
    }

    .importance-medium {
        opacity: 0.6;
    }

    .importance-high {
        opacity: 0.9;
        filter: brightness(1.2);
    }

    /* Animacje kondensacji */
    .condensation-process {
        animation: matter-condensation 5s ease-in-out infinite;
    }

    @keyframes matter-condensation {
        0% {
            opacity: 0.3;
            transform: scale(0.8);
        }
        50% {
            opacity: 0.8;
            transform: scale(1.2);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }

    /* Pole świadomości */
    .consciousness-field circle {
        pointer-events: none;
    }

    /* Interakcje z myślami */
    .thought-particle:hover .tooltip {
        display: block;
    }

    .tooltip {
        display: none;
        position: absolute;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 5px;
        border-radius: 3px;
        font-size: 12px;
        z-index: 1000;
    }

    /* Efekty przejścia między stanami */
    .state-transition {
        animation: state-change 1s ease-in-out;
    }

    @keyframes state-change {
        0% {
            opacity: 1;
            transform: scale(1);
        }
        50% {
            opacity: 0.5;
            transform: scale(1.5);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }
`;
document.head.appendChild(universeStyle);