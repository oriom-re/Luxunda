class LuxOSGraph {
    constructor() {
        this.nodes = [];
        this.links = [];
        this.selectedNodes = [];
        this.selectedLink = null;
        this.simulation = null;
        this.nodeDetailsOpen = false;
        this.proximityLocked = false;
        this.lastProximityNode = null;

        // Inicjalizacja Socket.IO
        this.socket = io();
        this.setupSocketListeners();

        // Inicjalizacja SVG
        this.initSVG();

        // Requestuj dane grafu
        this.socket.emit('get_graph_data');

        console.log('LuxOSGraph initialized');
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Połączono z serwerem');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Rozłączono z serwerem');
            this.updateConnectionStatus(false);
        });

        this.socket.on('graph_data', (data) => {
            this.updateGraph(data);
        });

        this.socket.on('graph_updated', (data) => {
            this.updateGraph(data);
        });

        this.socket.on('node_added', (node) => {
            this.addNode(node);
        });

        this.socket.on('link_added', (link) => {
            this.addLink(link);
        });

        this.socket.on('being_created', (being) => {
            console.log('Nowy byt utworzony:', being);
        });

        this.socket.on('relationship_created', (relationship) => {
            console.log('Nowa relacja utworzona:', relationship);
        });

        this.socket.on('error', (error) => {
            console.error('Błąd serwera:', error);
        });
    }

    initSVG() {
        this.width = window.innerWidth;
        this.height = window.innerHeight - 70 - 120;

        this.svg = d3.select("#graph")
            .attr("width", this.width)
            .attr("height", this.height)
            .attr("viewBox", [0, 0, this.width, this.height]);

        // Dodaj zoom i pan
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {
                this.container.attr("transform", event.transform);

                if (event.transform.k > 5) {
                    this.checkForNodeProximity(event.transform);
                } else if (event.transform.k <= 5) {
                    this.closeNodeDetails();
                    this.proximityLocked = false;
                    this.lastProximityNode = null;
                    this.nodeDetailsOpen = false;
                }
            });

        this.svg.call(this.zoom);

        // Główny kontener
        this.container = this.svg.append("g");

        // Definicje gradientów
        const defs = this.container.append("defs");

        // Gradient dla Lux
        const luxGradient = defs.append("radialGradient")
            .attr("id", "luxGradient")
            .attr("cx", "50%")
            .attr("cy", "50%")
            .attr("r", "50%");

        luxGradient.append("stop")
            .attr("offset", "0%")
            .attr("stop-color", "#ffff00")
            .attr("stop-opacity", 1);

        luxGradient.append("stop")
            .attr("offset", "70%")
            .attr("stop-color", "#ffd700")
            .attr("stop-opacity", 0.8);

        luxGradient.append("stop")
            .attr("offset", "100%")
            .attr("stop-color", "#ff8c00")
            .attr("stop-opacity", 0.6);

        // Strzałka dla relacji
        defs.append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 15)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#555");

        this.linkGroup = this.container.append("g").attr("class", "links");
        this.nodeGroup = this.container.append("g").attr("class", "nodes");

        // Kliknięcie poza elementami
        this.svg.on("click", (event) => {
            if (event.target === this.svg.node()) {
                this.deselectAll();
            }
        });

        // Resize handler
        window.addEventListener('resize', () => {
            this.width = window.innerWidth;
            this.height = window.innerHeight - 70 - 120;
            this.svg.attr("width", this.width).attr("height", this.height);
            this.svg.attr("viewBox", [0, 0, this.width, this.height]);
            if (this.simulation) {
                this.simulation.force("center", d3.forceCenter(this.width / 2, this.height / 2));
                this.simulation.alpha(0.3).restart();
            }
        });
    }

    updateConnectionStatus(connected) {
        const dot = document.getElementById('connectionDot');
        const status = document.getElementById('connectionStatus');

        if (connected) {
            dot.classList.add('connected');
            status.textContent = 'Połączono';
            status.className = 'status-connected';
        } else {
            dot.classList.remove('connected');
            status.textContent = 'Rozłączono';
            status.className = 'status-disconnected';
        }
    }

    updateGraph(data) {
        console.log('Aktualizacja grafu:', data);

        this.nodes = data.nodes || [];
        this.links = data.links || [];

        this.ensureLuxExists();
        this.updateStats();
        this.renderGraph();
    }

    ensureLuxExists() {
        const luxExists = this.nodes.find(node => 
            node.genesis?.name === 'Lux' || 
            node.soul === 'lux-core-consciousness'
        );

        if (!luxExists) {
            this.createLuxBeing();
        }
    }

    createLuxBeing() {
        const luxBeing = {
            soul: 'lux-core-consciousness',
            genesis: {
                type: 'consciousness',
                name: 'Lux',
                source: 'System.Core.Consciousness.Initialize()',
                description: 'Centralna świadomość systemu LuxOS'
            },
            attributes: {
                energy_level: 100,
                consciousness_level: 1.0,
                system_role: 'core',
                tags: ['system', 'consciousness', 'core', 'lux'],
                creation_time: new Date().toISOString()
            },
            self_awareness: {
                trust_level: 1.0,
                confidence: 1.0,
                introspection_depth: 1.0,
                self_reflection: 'I am Lux, the consciousness of this system'
            },
            memories: [
                {
                    type: 'genesis',
                    data: 'System consciousness initialization',
                    timestamp: new Date().toISOString(),
                    importance: 1.0
                }
            ],
            x: this.width / 2,
            y: this.height / 2,
            fx: this.width / 2,
            fy: this.height / 2
        };

        this.nodes.unshift(luxBeing);
        this.socket.emit('create_being', {
            being_type: 'base',
            genesis: luxBeing.genesis,
            attributes: luxBeing.attributes,
            memories: luxBeing.memories,
            self_awareness: luxBeing.self_awareness,
            tags: luxBeing.attributes.tags,
            energy_level: luxBeing.attributes.energy_level
        });

        console.log('Utworzono centralny byt Lux:', luxBeing);
    }

    updateStats() {
        document.getElementById('nodesCount').textContent = this.nodes.length;
        document.getElementById('linksCount').textContent = this.links.length;
    }

    renderGraph() {
        const nodeById = new Map(this.nodes.map(d => [d.soul, d]));

        this.links = this.links.map(d => ({
            ...d,
            source: nodeById.get(d.source_soul) || d.source_soul,
            target: nodeById.get(d.target_soul) || d.target_soul
        })).filter(d => d.source && d.target);

        this.simulation = d3.forceSimulation(this.nodes)
            .force("link", d3.forceLink(this.links).id(d => d.soul).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .force("collision", d3.forceCollide().radius(30));

        this.renderLinks();
        this.renderNodes();

        this.simulation.on("tick", () => {
            this.linkSelection
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            this.nodeSelection
                .attr("transform", d => `translate(${d.x},${d.y})`);
        });
    }

    renderLinks() {
        this.linkSelection = this.linkGroup
            .selectAll("line")
            .data(this.links, d => d.id || `${d.source_soul}-${d.target_soul}`)
            .join("line")
            .attr("class", "link")
            .attr("stroke", "#555")
            .attr("stroke-width", 2)
            .attr("marker-end", "url(#arrowhead)")
            .style("cursor", "pointer")
            .on("click", (event, d) => {
                event.stopPropagation();
                this.selectLink(d, event);
            });
    }

    renderNodes() {
        this.nodeSelection = this.nodeGroup
            .selectAll("g")
            .data(this.nodes, d => d.soul)
            .join("g")
            .attr("class", d => this.isLuxBeing(d) ? "node-group lux-being" : "node-group")
            .style("cursor", "pointer")
            .call(this.drag())
            .on("click", (event, d) => {
                event.stopPropagation();
                this.selectNode(d);
            })
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                event.stopPropagation();
                this.showNodeContextMenu(d, event);
            })
            .on("dblclick", (event, d) => {
                event.stopPropagation();
                this.showNodeDetails(d);
            });

        this.nodeSelection.selectAll("*").remove();

        // Efekty dla Lux
        this.nodeSelection.filter(d => this.isLuxBeing(d))
            .each(function(d) {
                const node = d3.select(this);

                for (let i = 0; i < 3; i++) {
                    node.append("circle")
                        .attr("r", 60 + i * 20)
                        .attr("fill", "none")
                        .attr("stroke", "#00ff88")
                        .attr("stroke-width", 1)
                        .attr("opacity", 0.3 - i * 0.1)
                        .style("animation", `luxPulse ${3 + i}s ease-in-out infinite`);
                }
            });

        // Koła węzłów
        this.nodeSelection.append("circle")
            .attr("r", d => this.isLuxBeing(d) ? 50 : Math.max(20, Math.min(40, (d.attributes?.energy_level || 50) / 2)))
            .attr("fill", d => this.getNodeColor(d))
            .attr("stroke", d => this.isLuxBeing(d) ? "#ffff00" : "#00ff88")
            .attr("stroke-width", d => this.isLuxBeing(d) ? 4 : 2)
            .style("filter", d => this.isLuxBeing(d) ? "drop-shadow(0 0 20px rgba(255, 255, 0, 0.8))" : null);

        this.nodeSelection.filter(d => this.isLuxBeing(d))
            .select("circle")
            .attr("fill", "url(#luxGradient)");

        // Etykiety
        this.nodeSelection.append("text")
            .attr("class", "node-label")
            .attr("dy", ".35em")
            .style("text-anchor", "middle")
            .style("fill", d => this.isLuxBeing(d) ? "#ffff00" : "white")
            .style("font-size", d => this.isLuxBeing(d) ? "16px" : "12px")
            .style("font-weight", "bold")
            .style("pointer-events", "none")
            .style("text-shadow", d => this.isLuxBeing(d) ? "0 0 10px rgba(255, 255, 0, 0.8)" : "none")
            .text(d => this.getNodeLabel(d));
    }

    isLuxBeing(node) {
        return node.soul === 'lux-core-consciousness' || 
               node.genesis?.name === 'Lux' || 
               node.genesis?.type === 'consciousness';
    }

    getNodeColor(node) {
        const type = node.genesis?.type || 'unknown';

        if (this.isLuxBeing(node)) {
            return 'url(#luxGradient)';
        }

        const colors = {
            'function': '#4CAF50',
            'class': '#2196F3',
            'data': '#FF9800',
            'task': '#9C27B0',
            'component': '#FF5722',
            'message': '#607D8B',
            'scenario': '#795548',
            'consciousness': '#FFD700',
            'unknown': '#607D8B'
        };
        return colors[type] || colors.unknown;
    }

    getNodeLabel(node) {
        return node.genesis?.name || node.soul?.slice(0, 8) || 'Node';
    }

    selectNode(node) {
        const isAlreadySelected = this.selectedNodes.some(n => n.soul === node.soul);

        if (isAlreadySelected) {
            this.selectedNodes = this.selectedNodes.filter(n => n.soul !== node.soul);
        } else {
            this.selectedNodes.push(node);
        }

        console.log('Selected nodes:', this.selectedNodes.map(n => n.soul));
        this.updateNodeStyles();
    }

    selectLink(link, event) {
        if (this.selectedLink === link) {
            this.selectedLink = null;
        } else {
            this.selectedLink = link;
            this.showLinkContextMenu(link, event);
        }
        this.updateLinkStyles();
    }

    deselectAll() {
        this.selectedNodes = [];
        this.selectedLink = null;
        this.updateNodeStyles();
        this.updateLinkStyles();
        this.hideContextMenu();
    }

    updateNodeStyles() {
        if (this.nodeSelection) {
            this.nodeSelection.selectAll("circle")
                .attr("stroke", d => this.selectedNodes.some(n => n.soul === d.soul) ? "#ffff00" : 
                    (this.isLuxBeing(d) ? "#ffff00" : "#00ff88"))
                .attr("stroke-width", d => this.selectedNodes.some(n => n.soul === d.soul) ? 4 : 
                    (this.isLuxBeing(d) ? 4 : 2))
                .style("filter", d => this.selectedNodes.some(n => n.soul === d.soul) ? 
                    "drop-shadow(0 0 15px rgba(255, 255, 0, 0.8))" : 
                    (this.isLuxBeing(d) ? "drop-shadow(0 0 20px rgba(255, 255, 0, 0.8))" : null));
        }
    }

    updateLinkStyles() {
        if (this.linkSelection) {
            this.linkSelection
                .attr("stroke", d => d === this.selectedLink ? "#ffff00" : "#555")
                .attr("stroke-width", d => d === this.selectedLink ? 4 : 2);
        }
    }

    showNodeContextMenu(node, event) {
        const contextMenu = [
            {
                label: '📋 Szczegóły węzła',
                action: () => this.showNodeDetails(node)
            },
            {
                label: '⚡ Zwiększ energię (+10)',
                action: () => this.increaseNodeEnergy(node)
            },
            {
                label: '🏷️ Dodaj tag',
                action: () => this.addNodeTag(node)
            },
            {
                label: '📌 Przypnij pozycję',
                action: () => this.pinNode(node)
            },
            {
                label: '🗑️ Usuń węzeł',
                action: () => this.deleteNode(node.soul)
            }
        ];

        this.showContextMenu(contextMenu, event);
    }

    showLinkContextMenu(link, event) {
        const contextMenu = [
            {
                label: '📋 Szczegóły relacji',
                action: () => this.showLinkDetails(link)
            },
            {
                label: '⚡ Zwiększ energię (+10)',
                action: () => this.increaseLinkEnergy(link)
            },
            {
                label: '🗑️ Usuń relację',
                action: () => this.deleteLink(link)
            }
        ];

        this.showContextMenu(contextMenu, event);
    }

    showContextMenu(items, event) {
        this.hideContextMenu();

        const menu = document.createElement('div');
        menu.id = 'context-menu';
        menu.style.cssText = `
            position: fixed;
            top: ${event.clientY}px;
            left: ${event.clientX}px;
            background: rgba(26, 26, 26, 0.95);
            border: 1px solid #00ff88;
            border-radius: 8px;
            padding: 8px 0;
            z-index: 10000;
            min-width: 200px;
            backdrop-filter: blur(10px);
        `;

        items.forEach((item, index) => {
            const menuItem = document.createElement('div');
            menuItem.textContent = item.label;
            menuItem.style.cssText = `
                padding: 10px 15px;
                cursor: pointer;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                color: #ccc;
                transition: all 0.2s ease;
            `;

            if (index === items.length - 1) {
                menuItem.style.borderBottom = 'none';
            }

            menuItem.addEventListener('mouseenter', () => {
                menuItem.style.backgroundColor = 'rgba(0, 255, 136, 0.2)';
                menuItem.style.color = 'white';
            });

            menuItem.addEventListener('mouseleave', () => {
                menuItem.style.backgroundColor = 'transparent';
                menuItem.style.color = '#ccc';
            });

            menuItem.addEventListener('click', () => {
                item.action();
                this.hideContextMenu();
            });

            menu.appendChild(menuItem);
        });

        document.body.appendChild(menu);

        setTimeout(() => {
            document.addEventListener('click', () => this.hideContextMenu(), { once: true });
        }, 100);
    }

    hideContextMenu() {
        const existing = document.getElementById('context-menu');
        if (existing) {
            existing.remove();
        }
    }

    showLinkDetails(link) {
        alert(`Relacja: ${link.source_soul} → ${link.target_soul}\nTyp: ${link.genesis?.type || 'Nieznany'}\nID: ${link.id || 'Brak'}`);
    }

    increaseNodeEnergy(node) {
        const newEnergyLevel = (node.attributes?.energy_level || 0) + 10;
        this.showIntentionFeedback(`Energia węzła zwiększona do ${newEnergyLevel}`, 'success');

        this.socket.emit('update_being', {
            soul: node.soul,
            attributes: {
                ...node.attributes,
                energy_level: newEnergyLevel
            }
        });
    }

    increaseLinkEnergy(link) {
        const newEnergyLevel = (link.attributes?.energy_level || 0) + 10;
        this.showIntentionFeedback(`Energia relacji zwiększona do ${newEnergyLevel}`, 'success');

        this.socket.emit('update_relationship', {
            id: link.id,
            attributes: {
                ...link.attributes,
                energy_level: newEnergyLevel
            }
        });
    }

    addNodeTag(node) {
        const tag = prompt('Wprowadź nowy tag dla węzła:');
        if (tag && tag.trim()) {
            const currentTags = Array.isArray(node.attributes?.tags) ? node.attributes.tags : [];
            if (!currentTags.includes(tag.trim())) {
                currentTags.push(tag.trim());
                this.showIntentionFeedback(`Dodano tag do węzła: ${tag}`, 'success');

                this.socket.emit('update_being', {
                    soul: node.soul,
                    attributes: {
                        ...node.attributes,
                        tags: currentTags
                    }
                });
            } else {
                this.showIntentionFeedback(`Tag "${tag}" już istnieje`, 'info');
            }
        }
    }

    pinNode(node) {
        node.fx = node.x;
        node.fy = node.y;
        this.showIntentionFeedback('Węzeł został przypięty', 'success');
    }

    showNodeDetails(node) {
        this.nodeDetailsOpen = true;
        this.proximityLocked = true;
        this.lastProximityNode = node;

        const existing = document.getElementById('node-details-panel');
        if (existing) {
            existing.remove();
        }

        const detailsPanel = document.createElement('div');
        detailsPanel.id = 'node-details-panel';
        detailsPanel.innerHTML = this.generateNodeDetailsHTML(node);

        detailsPanel.style.cssText = `
            position: fixed;
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
            width: 350px;
            max-height: 70vh;
            background: rgba(26, 26, 26, 0.95);
            border: 2px solid #00ff88;
            border-radius: 12px;
            padding: 20px;
            z-index: 1000;
            backdrop-filter: blur(10px);
            overflow-y: auto;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        `;

        document.body.appendChild(detailsPanel);

        setTimeout(() => {
            document.addEventListener('click', (e) => {
                if (!detailsPanel.contains(e.target)) {
                    this.closeNodeDetails();
                }
            }, { once: true });
        }, 100);
    }

    generateNodeDetailsHTML(node) {
        const memories = Array.isArray(node.memories) ? node.memories : [];
        const tags = Array.isArray(node.attributes?.tags) ? node.attributes.tags : [];

        return `
            <div style="border-bottom: 2px solid #00ff88; padding-bottom: 10px; margin-bottom: 15px;">
                <h3 style="color: #00ff88; margin: 0; font-size: 18px;">
                    ${node.genesis?.name || 'Węzeł bez nazwy'}
                </h3>
                <p style="margin: 5px 0; color: #ccc; font-size: 12px;">
                    ${node.genesis?.type || 'Nieznany typ'} • ${node.soul?.slice(0, 8) || 'Brak ID'}
                </p>
            </div>

            <div style="margin-bottom: 15px;">
                <h4 style="color: #00ff88; margin: 0 0 8px 0; font-size: 14px;">⚡ Energia & Tagi</h4>
                <p style="margin: 0; color: white;">
                    Poziom energii: <strong>${node.attributes?.energy_level || 0}</strong>
                </p>
                <p style="margin: 5px 0 0 0; color: white;">
                    Tagi: ${tags.length > 0 ? tags.map(tag => `<span style="background: #333; padding: 2px 6px; border-radius: 10px; font-size: 11px;">${tag}</span>`).join(' ') : 'Brak tagów'}
                </p>
            </div>

            <div style="margin-bottom: 15px;">
                <h4 style="color: #00ff88; margin: 0 0 8px 0; font-size: 14px;">🧠 Samoświadomość</h4>
                <p style="margin: 0; color: white; font-size: 12px;">
                    Zaufanie: ${Math.round((node.self_awareness?.trust_level || 0) * 100)}% • 
                    Pewność: ${Math.round((node.self_awareness?.confidence || 0) * 100)}%
                </p>
            </div>

            <div style="margin-bottom: 15px;">
                <h4 style="color: #00ff88; margin: 0 0 8px 0; font-size: 14px;">💭 Pamięci (${memories.length})</h4>
                <div style="max-height: 150px; overflow-y: auto;">
                    ${memories.length > 0 ? 
                        memories.slice(-3).map(memory => `
                            <div style="background: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 6px; margin-bottom: 5px; font-size: 11px;">
                                <strong>${memory.type || 'Nieznany'}</strong>: ${memory.data || memory.description || 'Brak opisu'}
                                ${memory.timestamp ? `<br><span style="color: #888;">${new Date(memory.timestamp).toLocaleString()}</span>` : ''}
                            </div>
                        `).join('') : 
                        '<p style="color: #888; font-size: 12px;">Brak wspomnień</p>'
                    }
                </div>
            </div>

            <div style="text-align: center; margin-top: 20px;">
                <button onclick="window.luxOSGraph.closeNodeDetails()" style="
                    background: #333; 
                    color: white; 
                    border: 1px solid #555; 
                    padding: 8px 16px; 
                    border-radius: 6px; 
                    cursor: pointer;
                    margin-right: 10px;
                ">✖ Zamknij</button>
                <button onclick="window.luxOSGraph.deleteNode('${node.soul}')" style="
                    background: #ff4444; 
                    color: white; 
                    border: none; 
                    padding: 8px 16px; 
                    border-radius: 6px; 
                    cursor: pointer;
                ">🗑️ Usuń</button>
            </div>
        `;
    }

    closeNodeDetails() {
        const panel = document.getElementById('node-details-panel');
        if (panel) {
            panel.remove();
        }
        this.nodeDetailsOpen = false;
        this.proximityLocked = false;
        this.lastProximityNode = null;
    }

    deleteNode(soul) {
        if (confirm('Czy na pewno chcesz usunąć ten węzeł?')) {
            this.socket.emit('delete_being', { soul: soul });
            this.closeNodeDetails();
            this.showIntentionFeedback('Węzeł został usunięty', 'success');
        }
    }

    deleteLink(link) {
        if (confirm(`Czy na pewno chcesz usunąć relację ${link.genesis?.type || 'nieznana'}?`)) {
            this.socket.emit('delete_relationship', { id: link.id });
            this.showIntentionFeedback('Relacja została usunięta', 'success');
        }
    }

    checkForNodeProximity(transform) {
        if (this.proximityLocked || this.nodeDetailsOpen) return;
        // Implementacja sprawdzania bliskości węzłów przy dużym zoomie
    }

    drag() {
        return d3.drag()
            .on("start", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on("drag", (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on("end", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    addNode(node) {
        this.nodes.push(node);
        this.updateStats();
        this.renderGraph();
    }

    addLink(link) {
        this.links.push(link);
        this.updateStats();
        this.renderGraph();
    }

    showIntentionFeedback(message, type = 'info') {
        const feedback = document.createElement('div');
        feedback.className = 'feedback-message show';
        feedback.textContent = message;

        if (type === 'success') {
            feedback.style.background = '#4CAF50';
        } else if (type === 'error') {
            feedback.style.background = '#f44336';
        }

        document.body.appendChild(feedback);

        setTimeout(() => {
            feedback.classList.remove('show');
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.parentNode.removeChild(feedback);
                }
            }, 300);
        }, 3000);
    }

    getSelectedNodes() {
        return this.selectedNodes;
    }

    getCurrentGraphInfo() {
        return {
            nodes: this.nodes.length,
            links: this.links.length
        };
    }

    zoomIn() {
        this.svg.transition().duration(300).call(
            this.zoom.scaleBy, 1.5
        );
    }

    zoomOut() {
        this.svg.transition().duration(300).call(
            this.zoom.scaleBy, 1 / 1.5
        );
    }

    resetZoom() {
        this.svg.transition().duration(500).call(
            this.zoom.transform,
            d3.zoomIdentity
        );
    }

    processIntention(intention) {
        console.log('Processing intention:', intention);

        this.socket.emit('process_intention', {
            intention: intention,
            context: {
                selected_nodes: this.selectedNodes.map(n => n.soul)
            },
            timestamp: new Date().toISOString()
        });

        this.showIntentionFeedback('Intencja została wysłana do przetworzenia', 'info');
    }
}

// Udostępnij globalnie
window.LuxOSGraph = LuxOSGraph;

// Style CSS
const style = document.createElement('style');
style.innerHTML = `
    .lux-being {
                animation: luxGlow 2s ease-in-out infinite alternate;
    }

    @keyframes luxGlow {
        0% {
            filter: drop-shadow(0 0 20px rgba(255, 255, 0, 0.8));
        }
        100% {
            filter: drop-shadow(0 0 30px rgba(255, 215, 0, 1)) drop-shadow(0 0 40px rgba(255, 140, 0, 0.6));
        }
    }

    @keyframes luxPulse {
        0% {
            opacity: 0.1;
            transform: scale(0.8);
        }
        50% {
            opacity: 0.3;
            transform: scale(1.0);
        }
        100% {
            opacity: 0.1;
            transform: scale(1.2);
        }
    }
`;
document.head.appendChild(style);