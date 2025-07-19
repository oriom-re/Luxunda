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

        // Inicjalizacja Socket.IO
        this.socket = io();
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
        });

        this.socket.on('disconnect', () => {
            console.log('Rozłączono ze wszechświatem');
            this.updateConnectionStatus(false);
        });

        this.socket.on('graph_data', (data) => {
            this.updateUniverse(data);
        });

        this.socket.on('universe_state', (data) => {
            this.updateUniversePositions(data);
        });

        this.socket.on('being_created', (being) => {
            console.log('Nowy byt w wszechświecie:', being);
            this.addBeing(being);
        });

        this.socket.on('error', (error) => {
            console.error('Błąd wszechświata:', error);
            this.showErrorMessage('Błąd połączenia z wszechświatem: ' + error.message);
        });

        // Globalna obsługa nieobsłużonych błędów Promise
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Nieobsłużony błąd Promise:', event.reason);
            event.preventDefault(); // Zapobiegnij domyślnemu logowaniu
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
        // Utwórz gwiazdy w tle
        const starCount = 200;
        const stars = [];

        for (let i = 0; i < starCount; i++) {
            stars.push({
                x: (Math.random() - 0.5) * this.width * 4,
                y: (Math.random() - 0.5) * this.height * 4,
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
        const luxExists = this.beings.find(being => 
            being.soul === '00000000-0000-0000-0000-000000000001' ||
            being.genesis?.lux_identifier === 'lux-core-consciousness' ||
            (being.genesis?.name === 'Lux' && being.genesis?.type === 'agent')
        );

        if (!luxExists) {
            this.createLuxAgent();
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

    renderUniverse() {
        // Renderuj orbity
        this.renderOrbits();

        // Renderuj byty jako ciała niebieskie
        this.renderBeings();

        // Dodaj efekty wszechświata
        this.addUniverseEffects();
    }

    renderOrbits() {
        const orbitData = this.beings
            .filter(being => being.attributes?.orbital_params?.orbital_radius > 0)
            .map(being => ({
                soul: being.soul,
                radius: being.attributes.orbital_params.orbital_radius,
                center: { x: 0, y: 0 } // Wszyscy orbitują wokół Lux na razie
            }));

        this.orbitsGroup.selectAll(".orbit")
            .data(orbitData, d => d.soul)
            .join("circle")
            .attr("class", "orbit")
            .attr("cx", d => d.center.x)
            .attr("cy", d => d.center.y)
            .attr("r", d => d.radius)
            .attr("fill", "none")
            .attr("stroke", "rgba(100, 100, 100, 0.3)")
            .attr("stroke-width", 1)
            .attr("stroke-dasharray", "5,5");
    }

    renderBeings() {
        this.beingSelection = this.beingsGroup
            .selectAll(".being")
            .data(this.beings, d => d.soul)
            .join("g")
            .attr("class", d => `being ${this.isLuxAgent(d) ? 'lux-agent' : d.genesis?.type || 'unknown'}`)
            .style("cursor", "pointer")
            .on("click", (event, d) => {
                event.stopPropagation();
                this.selectBeing(d);
            })
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                this.showBeingContextMenu(d, event);
            })
            .on("dblclick", (event, d) => {
                event.preventDefault();
                this.showBeingDetails(d);
            });

        // Usuń poprzednie elementy
        this.beingSelection.selectAll("*").remove();

        // Renderuj Lux jako centralną gwiazdę
        this.beingSelection.filter(d => this.isLuxAgent(d))
            .each(function(d) {
                const being = d3.select(this);

                // Główna gwiazda
                being.append("circle")
                    .attr("r", 40)
                    .attr("fill", "url(#luxStar)")
                    .style("filter", "url(#glow)");

                // Pulsujące pierścienie
                for (let i = 0; i < 4; i++) {
                    being.append("circle")
                        .attr("r", 60 + i * 15)
                        .attr("fill", "none")
                        .attr("stroke", "#ffff00")
                        .attr("stroke-width", 2)
                        .attr("opacity", 0.4 - i * 0.1)
                        .style("animation", `luxPulse ${2 + i}s ease-in-out infinite`);
                }
            });

        // Renderuj wiadomości/intencje jako małe kropki na mapie dusz
        this.beingSelection.filter(d => d.genesis?.type === 'message')
            .each(function(d) {
                const being = d3.select(this);
                const isIntention = d.attributes?.metadata?.message_type === 'intention';

                // Mała kropka dla wiadomości/intencji
                being.append("circle")
                    .attr("r", isIntention ? 4 : 3)
                    .attr("fill", isIntention ? "#ffff00" : "#87ceeb")
                    .attr("stroke", "#ffffff")
                    .attr("stroke-width", 0.5)
                    .style("opacity", 0.8)
                    .style("filter", isIntention ? "url(#glow)" : null);

                // Pulsowanie dla nowych intencji
                if (isIntention) {
                    being.append("circle")
                        .attr("r", 8)
                        .attr("fill", "none")
                        .attr("stroke", "#ffff00")
                        .attr("stroke-width", 1)
                        .attr("opacity", 0.6)
                        .style("animation", "intentionPulse 2s ease-in-out infinite");
                }

                // Etykieta tylko przy wysokim zoomie
                if (self.zoomLevel > 10) {
                    being.append("text")
                        .attr("class", "being-label")
                        .attr("dy", 12)
                        .style("text-anchor", "middle")
                        .style("fill", "white")
                        .style("font-size", "6px")
                        .style("pointer-events", "none")
                        .text(d.attributes?.message_data?.content?.slice(0, 10) + '...' || 'Msg');
                }
            });

        // Renderuj pozostałe byty jako planety/komety
        const self = this;
        this.beingSelection.filter(d => !this.isLuxAgent(d) && d.genesis?.type !== 'message')
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

                // Etykieta (tylko przy odpowiednim zoomie)
                if (self.zoomLevel > 2) {
                    being.append("text")
                        .attr("class", "being-label")
                        .attr("dy", energySize + 15)
                        .style("text-anchor", "middle")
                        .style("fill", "white")
                        .style("font-size", "10px")
                        .style("pointer-events", "none")
                        .text(d.genesis?.name || d.soul?.slice(0, 8) || 'Being');
                }
            });
    }

    updateBeingPositions() {
        if (!this.beingSelection) return;

        this.beingSelection
            .transition()
            .duration(1000)
            .attr("transform", d => {
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

                // Lux zawsze w centrum
                if (this.isLuxAgent(d)) {
                    return `translate(0, 0)`;
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
            'unknown': '#666666'
        };
        return colors[type] || colors.unknown;
    }

    selectBeing(being) {
        const isSelected = this.selectedNodes.some(n => n.soul === being.soul);

        if (isSelected) {
            this.selectedNodes = this.selectedNodes.filter(n => n.soul !== being.soul);
        } else {
            this.selectedNodes.push(being);
        }

        console.log('Wybrane byty:', this.selectedNodes.map(n => n.soul));
        this.updateBeingStyles();
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
        if (this.beingSelection) {
            this.beingSelection.selectAll("circle")
                .attr("stroke", d => this.selectedNodes.some(n => n.soul === d.soul) ? "#ffff00" : 
                    (this.isLuxAgent(d) ? "#ffff00" : "#ffffff"))
                .attr("stroke-width", d => this.selectedNodes.some(n => n.soul === d.soul) ? 3 : 1);
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
}

// Zastąp LuxOSGraph nowym systemem wszechświata
window.LuxOSGraph = LuxOSUniverse;
window.luxOSUniverse = null;

// Style CSS dla wszechświata
const universeStyle = document.createElement('style');
universeStyle.innerHTML = `
    .lux-agent {
        animation: luxPulse 3s ease-in-out infinite;
    }

    .being {
        transition: all 0.3s ease;
    }

    .being:hover {
        filter: brightness(1.2) drop-shadow(0 0 10px rgba(255, 255, 255, 0.5));
    }

    .orbit {
        animation: orbitRotate 20s linear infinite;
    }

    @keyframes luxPulse {
        0% { filter: brightness(1) drop-shadow(0 0 20px rgba(255, 255, 0, 0.8)); }
        50% { filter: brightness(1.3) drop-shadow(0 0 40px rgba(255, 215, 0, 1)); }
        100% { filter: brightness(1) drop-shadow(0 0 20px rgba(255, 255, 0, 0.8)); }
    }

    @keyframes orbitRotate {
        from { stroke-dashoffset: 0; }
        to { stroke-dashoffset: 31.416; }
    }

    .star {
        animation: twinkle 3s ease-in-out infinite;
    }

    @keyframes twinkle {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }

    @keyframes intentionPulse {
        0% { transform: scale(1); opacity: 0.6; }
        50% { transform: scale(1.5); opacity: 0.3; }
        100% { transform: scale(1); opacity: 0.6; }
    }
`;
document.head.appendChild(universeStyle);