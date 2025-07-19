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

        // Dodaj zoom i pan (scroll i lewy przycisk)
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {
                this.container.attr("transform", event.transform);

                // Sprawdź czy zoom jest na wysokim poziomie i czy jest blisko węzła
                if (event.transform.k > 5) {
                    this.checkForNodeProximity(event.transform);
                } else if (event.transform.k <= 5) {
                    // Zamknij panel szczegółów przy oddaleniu
                    this.closeNodeDetails();
                    this.proximityLocked = false;
                    this.lastProximityNode = null;
                    this.nodeDetailsOpen = false;
                }
            });

        this.svg.call(this.zoom);

        // Główny kontener dla wszystkich elementów grafu
        this.container = this.svg.append("g");

        this.container.append("defs").append("marker")
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

        // Dodaj obsługę kliknięcia poza elementami
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

        // Aktualizuj statystyki
        this.updateStats();

        this.renderGraph();
    }

    updateStats() {
        document.getElementById('nodesCount').textContent = this.nodes.length;
        document.getElementById('linksCount').textContent = this.links.length;
    }

    renderGraph() {
        // Przygotuj dane linków z odnośnikami do węzłów
        const nodeById = new Map(this.nodes.map(d => [d.soul, d]));

        this.links = this.links.map(d => ({
            ...d,
            source: nodeById.get(d.source_soul) || d.source_soul,
            target: nodeById.get(d.target_soul) || d.target_soul
        })).filter(d => d.source && d.target);

        // Ustawienia symulacji
        this.simulation = d3.forceSimulation(this.nodes)
            .force("link", d3.forceLink(this.links).id(d => d.soul).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .force("collision", d3.forceCollide().radius(30));

        this.renderLinks();
        this.renderNodes();

        // Uruchom symulację
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
            })
            .on("mouseover", function(event, d) {
                d3.select(this).attr("stroke", "#00ff88").attr("stroke-width", 3);
            })
            .on("mouseout", function(event, d) {
                if (d !== this.selectedLink) {
                    d3.select(this).attr("stroke", "#555").attr("stroke-width", 2);
                }
            }.bind(this));
    }

    renderNodes() {
        this.nodeSelection = this.nodeGroup
            .selectAll("g")
            .data(this.nodes, d => d.soul)
            .join("g")
            .attr("class", "node-group")
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

        // Usuń poprzednie elementy węzłów
        this.nodeSelection.selectAll("*").remove();

        // Dodaj koła
        this.nodeSelection.append("circle")
            .attr("r", d => Math.max(20, Math.min(40, (d.attributes?.energy_level || 50) / 2)))
            .attr("fill", d => this.getNodeColor(d))
            .attr("stroke", "#00ff88")
            .attr("stroke-width", 2);

        // Dodaj etykiety
        this.nodeSelection.append("text")
            .attr("class", "node-label")
            .attr("dy", ".35em")
            .style("text-anchor", "middle")
            .style("fill", "white")
            .style("font-size", "12px")
            .style("font-weight", "bold")
            .style("pointer-events", "none")
            .text(d => this.getNodeLabel(d));
    }

    getNodeColor(node) {
        const type = node.genesis?.type || 'unknown';
        const colors = {
            'function': '#4CAF50',
            'class': '#2196F3',
            'module': '#FF9800',
            'variable': '#9C27B0',
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

    deselectAll() {
        this.selectedNodes = [];
        this.selectedLink = null;
        this.updateNodeStyles();
        this.updateLinkStyles();
        this.hideContextMenu();
    }

    updateNodeStyles() {
        this.nodeSelection.selectAll("circle")
            .attr("stroke", d => this.selectedNodes.some(n => n.soul === d.soul) ? "#ffff00" : "#00ff88")
            .attr("stroke-width", d => this.selectedNodes.some(n => n.soul === d.soul) ? 4 : 2)
            .style("filter", d => this.selectedNodes.some(n => n.soul === d.soul) ? 
                "drop-shadow(0 0 15px rgba(255, 255, 0, 0.8))" : null);
    }

    updateLinkStyles() {
        this.linkSelection
            .attr("stroke", d => d === this.selectedLink ? "#ffff00" : "#555")
            .attr("stroke-width", d => d === this.selectedLink ? 4 : 2);
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
                label: '🏷️ Dodaj tag',
                action: () => this.addLinkTag(link)
            },
            {
                label: '✏️ Zmień typ',
                action: () => this.editLinkType(link)
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

        // Zamknij menu po kliknięciu gdzie indziej
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

    increaseLinkEnergy(link) {
        const newEnergyLevel = (link.attributes?.energy_level || 0) + 10;
        this.showIntentionFeedback(`Energia relacji zwiększona do ${newEnergyLevel}`, 'success');

        // Tutaj można dodać komunikację z backendem
        this.socket.emit('update_relationship', {
            id: link.id,
            attributes: {
                ...link.attributes,
                energy_level: newEnergyLevel
            }
        });
    }

    addLinkTag(link) {
        const tag = prompt('Wprowadź nowy tag dla relacji:');
        if (tag && tag.trim()) {
            const currentTags = Array.isArray(link.attributes?.tags) ? link.attributes.tags : [];
            if (!currentTags.includes(tag.trim())) {
                currentTags.push(tag.trim());
                this.showIntentionFeedback(`Dodano tag do relacji: ${tag}`, 'success');

                // Wyślij do backendu
                this.socket.emit('update_relationship', {
                    id: link.id,
                    attributes: {
                        ...link.attributes,
                        tags: currentTags
                    }
                });
            } else {
                this.showIntentionFeedback(`Tag "${tag}" już istnieje`, 'info');
            }
        }
    }

    editLinkType(link) {
        const newType = prompt('Wprowadź nowy typ relacji:', link.genesis?.type || '');
        if (newType && newType.trim()) {
            this.showIntentionFeedback(`Zmieniono typ relacji na: ${newType}`, 'success');

            // Wyślij do backendu
            this.socket.emit('update_relationship', {
                id: link.id,
                genesis: {
                    ...link.genesis,
                    type: newType.trim()
                }
            });
        }
    }

    deleteLink(link) {
        if (confirm(`Czy na pewno chcesz usunąć relację ${link.genesis?.type || 'nieznana'}?`)) {
            this.socket.emit('delete_relationship', { id: link.id });
            this.showIntentionFeedback('Relacja została usunięta', 'success');
        }
    }

    showNodeDetails(node) {
        this.nodeDetailsOpen = true;
        this.proximityLocked = true;
        this.lastProximityNode = node;

        // Usuń poprzedni panel jeśli istnieje
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

        // Zamknij po kliknięciu poza panelem
        setTimeout(() => {
            document.addEventListener('click', (e) => {
                if (!detailsPanel.contains(e.target)) {
                    this.closeNodeDetails();
                }
            }, { once: true });
        }, 100);

        // Pozwól na zoom gdy kursor jest nad panelem szczegółów
        detailsPanel.addEventListener('wheel', (e) => {
            e.preventDefault();

            // Symuluj zoom na głównym grafie
            const zoomFactor = e.deltaY > 0 ? 1 / 1.2 : 1.2;
            const currentTransform = d3.zoomTransform(this.svg.node());
            const newScale = currentTransform.k * zoomFactor;

            // Sprawdź limity zoom
            if (newScale >= 0.1 && newScale <= 10) {
                this.svg.transition().duration(100).call(
                    this.zoom.scaleTo, newScale
                );

                // Zamknij panel przy oddaleniu
                if (newScale <= 3) {
                    this.closeNodeDetails();
                    this.proximityLocked = false;
                    this.lastProximityNode = null;
                    this.nodeDetailsOpen = false;
                }
            }
        });
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

            ${node.genesis?.source ? `
                <div style="margin-bottom: 15px;">
                    <h4 style="color: #00ff88; margin: 0 0 8px 0; font-size: 14px;">💻 Kod źródłowy</h4>
                    <pre style="background: #1a1a1a; padding: 10px; border-radius: 6px; font-size: 11px; overflow-x: auto; white-space: pre-wrap; border: 1px solid #333;">${node.genesis.source}</pre>
                </div>
            ` : ''}

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

    checkForNodeProximity(transform) {
        if (this.proximityLocked || this.nodeDetailsOpen) return;

        const mouseX = d3.pointer(d3.event || window.event, this.svg.node())[0];
        const mouseY = d3.pointer(d3.event || window.event, this.svg.node())[1];

        // Przekształć współrzędne myszy do układu współrzędnych grafu
        const graphX = (mouseX - transform.x) / transform.k;
        const graphY = (mouseY - transform.y) / transform.k;

        const proximityThreshold = 50;

        for (const node of this.nodes) {
            if (node.x && node.y) {
                const distance = Math.sqrt(
                    Math.pow(graphX - node.x, 2) + Math.pow(graphY - node.y, 2)
                );

                if (distance < proximityThreshold && node !== this.lastProximityNode) {
                    this.showNodeDetails(node);
                    break;
                }
            }
        }
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
                // Nie zamrażaj pozycji - pozwól na dalszą symulację
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

    // Kontrolki zoom
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
}

// Udostępnij globalnie dla HTML
window.LuxOSGraph = LuxOSGraph;

// Add CSS styles for relationship selection and highlighting
const style = document.createElement('style');
style.innerHTML = `
    .link {
        stroke: #555;
        stroke-width: 2px;
        marker-end: url(#arrowhead);
        cursor: pointer;
    }

    .link.highlighted {
        stroke: #00ff88;
        stroke-width: 3px;
    }

    .link.selected {
        stroke: #ffff00;
        stroke-width: 4px;
        filter: drop-shadow(0 0 8px rgba(255, 255, 0, 0.6));
    }
`;
document.head.appendChild(style);