class LuxOSGraph {
    constructor() {
        this.svg = d3.select("#graph");
        this.width = window.innerWidth;
        this.height = window.innerHeight - 190;
        this.nodes = [];
        this.links = [];
        this.selectedNodes = [];
        this.simulation = null;
        this.socket = null;
        this.mouseDownTime = 0;
        this.proximityLocked = false;
        this.lastProximityNode = null;

        // Globalna referencja dla przycisków w panelu szczegółów
        window.luxosGraph = this;

        this.initializeSocket();
        this.initializeGraph();
        this.setupEventListeners();
    }

    initializeSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Połączono z serwerem');
            document.getElementById('connectionStatus').textContent = 'Połączono';
            document.getElementById('connectionDot').classList.add('connected');
            // Nie wysyłamy get_graph_data - backend automatycznie wyśle dane po połączeniu
        });

        this.socket.on('disconnect', () => {
            console.log('Rozłączono z serwerem');
            document.getElementById('connectionStatus').textContent = 'Rozłączono';
            document.getElementById('connectionDot').classList.remove('connected');
        });

        this.socket.on('graph_data', (data) => {
            this.updateGraph(data);
        });

        this.socket.on('graph_update', (data) => {
            this.updateGraph(data);
        });

        this.socket.on('graph_updated', (data) => {
            this.updateGraph(data);
        });

        this.socket.on('intention_response', (response) => {
            this.handleIntentionResponse(response);
        });

        this.socket.on('being_created', (being) => {
            console.log('Nowy byt utworzony:', being);
        });

        this.socket.on('relationship_created', (relationship) => {
            console.log('Nowa relacja utworzona:', relationship);
        });

        this.socket.on('node_added', (node) => {
            console.log('Dodawanie węzła:', node);
            this.addNode(node);
        });

        this.socket.on('link_added', (link) => {
            console.log('Dodawanie relacji:', link);
            this.addLink(link);
        });

        this.socket.on('node_updated', (node) => {
            console.log('Aktualizacja węzła:', node);
            this.updateNode(node);
        });

        this.socket.on('being_updated', (being) => {
            console.log('Byt zaktualizowany:', being);
            this.updateNode(being);
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.showIntentionFeedback(error.message || 'Wystąpił błąd', 'error');
        });
    }

    initializeGraph() {
        this.svg
            .attr("width", this.width)
            .attr("height", this.height)
            .attr("viewBox", [0, 0, this.width, this.height]);

        // Dodaj zoom i pan (scroll i lewy przycisk)
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {
                this.container.attr("transform", event.transform);

                // Sprawdź czy zoom jest na wysokim poziomie i czy jest blisko węzła
                if (event.transform.k > 5) { // Zwiększony próg zoom
                    this.checkForNodeProximity(event.transform);
                } else if (event.transform.k <= 50) {
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

        this.simulation = d3.forceSimulation()
            .force("link", d3.forceLink().id(d => d.soul).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .force("collision", d3.forceCollide().radius(30));
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.width = window.innerWidth;
            this.height = window.innerHeight - 190;
            this.svg.attr("width", this.width).attr("height", this.height);
            this.simulation.force("center", d3.forceCenter(this.width / 2, this.height / 2));
        });

        // Zablokuj domyślne menu kontekstowe przeglądarki
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });

        // Obsługa kliknięcia lewym przyciskiem w puste miejsce - ukryj menu i odznacz relacje
        this.svg.on('click', () => {
            this.hideContextMenu();
            this.clearLinkSelection();
        });

        // Usunięto obsługę środkowego przycisku myszy
    }

    updateGraph(data) {
        this.nodes = data.nodes || [];
        this.links = data.links || [];

        document.getElementById('nodesCount').textContent = this.nodes.length;
        document.getElementById('linksCount').textContent = this.links.length;

        this.renderGraph();
    }

    renderGraph() {
        const link = this.linkGroup
            .selectAll(".link")
            .data(this.links, d => `${d.source_soul}-${d.target_soul}`);

        link.exit().remove();

        const linkEnter = link.enter()
            .append("g")
            .attr("class", "link-group");

        // Niewidoczna linia dla lepszego wykrywania kliknięć (szerszy obszar)
        linkEnter.append("line")
            .attr("class", "link-hit-area")
            .attr("stroke", "transparent")
            .attr("stroke-width", 15) // Szerszy obszar wykrywania
            .on("click", (event, d) => {
                event.stopPropagation();
                this.handleLinkSelection(event, d);
            })
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                event.stopPropagation();
                this.showLinkContextMenu(event, d);
            });

        // Widoczna linia
        linkEnter.append("line")
            .attr("class", "link")
            .attr("pointer-events", "none"); // Wyłącz eventy na widocznej linii

        link.merge(linkEnter);

        const node = this.nodeGroup
            .selectAll(".node-group")
            .data(this.nodes, d => d.soul);

        node.exit().remove();

        const nodeEnter = node.enter()
            .append("g")
            .attr("class", "node-group")
            .call(this.drag());

        nodeEnter.append("circle")
            .attr("class", "node")
            .attr("r", 20)
            .attr("fill", d => this.getNodeColor(d));

        nodeEnter.append("text")
            .attr("class", "node-label")
            .attr("dy", "0.3em")
            .text(d => d.genesis?.name || "Unnamed");

        const nodeUpdate = node.merge(nodeEnter);

        nodeUpdate.select(".node")
            .attr("fill", d => this.getNodeColor(d));

        nodeUpdate.select(".node-label")
            .text(d => d.genesis?.name || "Unnamed");

        nodeUpdate.on("mousedown", (event, d) => {
            this.mouseDownTime = Date.now();
        })
        .on("click", (event, d) => {
            this.handleNodeSelection(event, d);
        })
        .on("dblclick", (event, d) => {
            event.preventDefault();
            this.openNodeDetails(d);
        })
        .on("contextmenu", (event, d) => {
            event.preventDefault();
            event.stopPropagation();
            this.showContextMenu(event, d);
        });

        this.simulation.nodes(this.nodes);
        this.simulation.force("link").links(this.links.map(d => ({
            source: d.source_soul,
            target: d.target_soul
        })));

        this.simulation.on("tick", () => {
            this.linkGroup.selectAll(".link-group").selectAll("line")
                .attr("x1", d => {
                    const sourceNode = this.nodes.find(n => n.soul === d.source_soul);
                    return sourceNode ? sourceNode.x : 0;
                })
                .attr("y1", d => {
                    const sourceNode = this.nodes.find(n => n.soul === d.source_soul);
                    return sourceNode ? sourceNode.y : 0;
                })
                .attr("x2", d => {
                    const targetNode = this.nodes.find(n => n.soul === d.target_soul);
                    return targetNode ? targetNode.x : 0;
                })
                .attr("y2", d => {
                    const targetNode = this.nodes.find(n => n.soul === d.target_soul);
                    return targetNode ? targetNode.y : 0;
                });

            this.nodeGroup.selectAll(".node-group")
                .attr("transform", d => `translate(${d.x},${d.y})`);
        });

        this.simulation.alpha(1).restart();
    }

    getNodeColor(node) {
        const type = node.genesis?.type || 'unknown';
        const colors = {
            'function': '#4CAF50',
            'class': '#2196F3',
            'variable': '#FF9800',
            'module': '#9C27B0',
            'unknown': '#607D8B'
        };
        return colors[type] || colors.unknown;
    }

    handleNodeSelection(event, node) {
        event.stopPropagation();

        // Sprawdź czy to było przeciąganie
        if (node.isDragging || (node.lastDragTime && Date.now() - node.lastDragTime < 200)) {
            return;
        }

        // Sprawdź czy to pojedyncze kliknięcie (nie przeciąganie)
        const timeSinceMouseDown = Date.now() - (this.mouseDownTime || 0);
        if (timeSinceMouseDown > 300) {
            return; // To było przeciąganie
        }

        // Obsługa selekcji węzła
        const nodeElement = this.nodeGroup.selectAll(".node").filter(d => d.soul === node.soul);
        const isSelected = this.selectedNodes.includes(node.soul);

        if (isSelected) {
            // Usuń z selekcji
            this.selectedNodes = this.selectedNodes.filter(id => id !== node.soul);
            nodeElement.classed("selected", false);
        } else {
            // Dodaj do selekcji
            this.selectedNodes.push(node.soul);
            nodeElement.classed("selected", true);
        }

        console.log('Selected nodes:', this.selectedNodes);
    }

    handleLinkSelection(event, link) {
        event.stopPropagation();

        const linkElement = this.linkGroup.selectAll(".link-group").filter(l => l.source_soul === link.source_soul && l.target_soul === link.target_soul);
        const isSelected = linkElement.select(".link").classed("selected");

        if (isSelected) {
            linkElement.select(".link").classed("selected", false);
        } else {
            linkElement.select(".link").classed("selected", true);
        }

        console.log('Link selection changed:', link.id || `${link.source_soul}-${link.target_soul}`);
    }

    clearLinkSelection() {
        this.linkGroup.selectAll(".link").classed("selected", false);
    }

    showLinkContextMenu(event, link) {
        this.hideContextMenu();

        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.position = 'fixed';
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';
        menu.style.background = 'rgba(26, 26, 26, 0.95)';
        menu.style.border = '1px solid #00ff88';
        menu.style.borderRadius = '8px';
        menu.style.padding = '8px 0';
        menu.style.zIndex = '2000';
        menu.style.minWidth = '150px';
        menu.style.backdropFilter = 'blur(10px)';
        menu.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.5)';

        const menuItems = [
            {
                text: '🔍 Szczegóły relacji',
                action: () => this.showLinkDetails(link)
            },
            {
                text: '⚡ Zwiększ energię',
                action: () => this.increaseLinkEnergy(link)
            },
            {
                text: '🏷️ Dodaj tag',
                action: () => this.addLinkTag(link)
            },
            {
                text: '📝 Edytuj typ',
                action: () => this.editLinkType(link)
            },
            {
                text: '🗑️ Usuń relację',
                action: () => this.deleteLink(link)
            }
        ];

        menuItems.forEach(item => {
            const menuItem = document.createElement('div');
            menuItem.textContent = item.text;
            menuItem.style.padding = '8px 16px';
            menuItem.style.color = 'white';
            menuItem.style.cursor = 'pointer';
            menuItem.style.fontSize = '14px';
            menuItem.style.borderBottom = '1px solid #333';

            menuItem.addEventListener('mouseenter', () => {
                menuItem.style.background = '#00ff88';
                menuItem.style.color = '#1a1a1a';
            });

            menuItem.addEventListener('mouseleave', () => {
                menuItem.style.background = 'transparent';
                menuItem.style.color = 'white';
            });

            menuItem.addEventListener('click', () => {
                item.action();
                this.hideContextMenu();
            });

            menu.appendChild(menuItem);
        });

        // Usuń ostatnią linię
        if (menu.lastChild) {
            menu.lastChild.style.borderBottom = 'none';
        }

        document.body.appendChild(menu);

        // Zamknij menu po kliknięciu gdzie indziej
        setTimeout(() => {
            document.addEventListener('click', () => this.hideContextMenu(), { once: true });
        }, 100);
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
        if (confirm(`Czy na pewno chcesz usunąć relację "${link.genesis?.type || 'Nieznana'}" między bytami?`)) {
            this.showIntentionFeedback('Relacja usunięta', 'info');

            // Wyślij do backendu
            this.socket.emit('delete_relationship', { id: link.id });
        }
    }


    drag() {
        return d3.drag()
            .on("start", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                // Oznacz węzeł jako przeciągany w metadanych, ale zachowaj fizyczność
                d.isDragging = true;
                d.dragStartTime = Date.now();
            })
            .on("drag", (event, d) => {
                // Aktualizuj pozycję bez blokowania fizyki
                d.x = event.x;
                d.y = event.y;
            })
            .on("end", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                // Usuń oznaczenie przeciągania, zachowując pozycję
                d.isDragging = false;
                d.lastDragTime = Date.now();
                // Nie blokuj pozycji - pozwól fizyce działać normalnie
            });
    }

    processIntention(intention) {
        if (!intention.trim()) {
            this.showIntentionFeedback('Wprowadź treść intencji', 'error');
            return;
        }

        const context = {
            selected_nodes: this.selectedNodes,
            current_graph: {
                nodes: this.nodes.length,
                links: this.links.length
            }
        };

        this.socket.emit('process_intention', {
            intention: intention,
            context: context
        });

        console.log('Wysłano intencję:', intention);
        this.showIntentionFeedback('Przetwarzanie intencji...', 'info');
    }

    handleIntentionResponse(response) {
        console.log('Odpowiedź na intencję:', response);

        if (response.actions && response.actions.length > 0) {
            this.executeActions(response.actions);
        }

        this.showIntentionFeedback(response.message || 'Intencja przetworzona', 'success');
        this.selectedNodes = [];
        this.nodeGroup.selectAll(".node").classed("selected", false);
    }

    executeActions(actions) {
        actions.forEach(action => {
            console.log('Wykonywanie akcji:', action);

            if (action.type === 'create_being') {
                this.socket.emit('create_being', action.data);
            } else if (action.type === 'create_relationship') {
                this.socket.emit('create_relationship', action.data);
            }
        });

        // Granularne aktualizacje - nie potrzebujemy pełnego odświeżenia
    }

    // Granularne aktualizacje
    addNode(nodeData) {
        // Sprawdź czy węzeł już istnieje
        const existingIndex = this.nodes.findIndex(n => n.soul === nodeData.soul);
        if (existingIndex !== -1) {
            return; // Węzeł już istnieje
        }

        // Dodaj nowy węzeł
        this.nodes.push(nodeData);
        this.updateStats();
        this.renderNewNode(nodeData);
    }

    addLink(linkData) {
        // Sprawdź czy relacja już istnieje
        const existingIndex = this.links.findIndex(l => l.id === linkData.id);
        if (existingIndex !== -1) {
            return; // Relacja już istnieje
        }

        // Dodaj nową relację
        this.links.push(linkData);
        this.updateStats();
        this.renderNewLink(linkData);
    }

    updateNode(nodeData) {
        // Znajdź i zaktualizuj węzeł
        const index = this.nodes.findIndex(n => n.soul === nodeData.soul);
        if (index !== -1) {
            this.nodes[index] = nodeData;
            this.renderUpdatedNode(nodeData);
        }
    }

    updateStats() {
        document.getElementById('nodesCount').textContent = this.nodes.length;
        document.getElementById('linksCount').textContent = this.links.length;
    }

    renderNewNode(nodeData) {
        // Dodaj nowy węzeł do symulacji
        this.simulation.nodes(this.nodes);

        // Renderuj nowy węzeł
        const nodeGroup = this.nodeGroup
            .selectAll(".node-group")
            .data(this.nodes, d => d.soul);

        const nodeEnter = nodeGroup.enter()
            .append("g")
            .attr("class", "node-group")
            .call(this.drag());

        nodeEnter.append("circle")
            .attr("class", "node")
            .attr("r", 20)
            .attr("fill", d => this.getNodeColor(d));

        nodeEnter.append("text")
            .attr("class", "node-label")
            .attr("dy", "0.3em")
            .text(d => d.genesis?.name || "Unnamed");

        nodeEnter.on("click", (event, d) => {
            this.handleNodeClick(event, d);
        });

        // Restart symulacji z nowym węzłem
        this.simulation.alpha(0.3).restart();
    }

    renderNewLink(linkData) {
        // Dodaj nową relację do symulacji
        this.simulation.force("link").links(this.links.map(d => ({
            source: d.source_soul,
            target: d.target_soul
        })));

        // Renderuj nową relację
        const link = this.linkGroup
            .selectAll(".link-group")
            .data(this.links, d => `${d.source_soul}-${d.target_soul}`);

        const linkEnter = link.enter()
            .append("g")
            .attr("class", "link-group");

        // Niewidoczna linia dla lepszego wykrywania kliknięć
        linkEnter.append("line")
            .attr("class", "link-hit-area")
            .attr("stroke", "transparent")
            .attr("stroke-width", 15)
            .on("click", (event, d) => {
                event.stopPropagation();
                this.handleLinkSelection(event, d);
            })
            .on("contextmenu", (event, d) => {
                event.preventDefault();
                event.stopPropagation();
                this.showLinkContextMenu(event, d);
            });

        // Widoczna linia
        linkEnter.append("line")
            .attr("class", "link")
            .attr("pointer-events", "none");

        // Restart symulacji z nową relacją
        this.simulation.alpha(0.3).restart();
    }

    renderUpdatedNode(nodeData) {
        // Znajdź istniejący węzeł w symulacji i zachowaj jego pozycję
        const existingNode = this.simulation.nodes().find(n => n.soul === nodeData.soul);
        if (existingNode) {
            // Zachowaj pozycję węzła
            nodeData.x = existingNode.x;
            nodeData.y = existingNode.y;
            nodeData.vx = existingNode.vx;
            nodeData.vy = existingNode.vy;
        }

        // Aktualizuj węzeł w tablicy
        const nodeIndex = this.nodes.findIndex(n => n.soul === nodeData.soul);
        if (nodeIndex !== -1) {
            this.nodes[nodeIndex] = nodeData;
        }

        // Aktualizuj symulację z zachowanymi pozycjami
        this.simulation.nodes(this.nodes);

        // Aktualizuj wizualnie węzeł
        const nodeGroup = this.nodeGroup
            .selectAll(".node-group")
            .data(this.nodes, d => d.soul);

        nodeGroup.select(".node")
            .attr("fill", d => this.getNodeColor(d));

        nodeGroup.select(".node-label")
            .text(d => d.genesis?.name || "Unnamed");

        // Delikatny restart symulacji tylko jeśli potrzebny
        if (this.simulation.alpha() < 0.1) {
            this.simulation.alpha(0.1).restart();
        }
    }

    // Funkcje zoom
    zoomIn() {
        this.svg.transition().duration(300).call(
            this.zoom.scaleBy, 1.2
        );
    }

    zoomOut() {
        this.svg.transition().duration(300).call(
            this.zoom.scaleBy, 1 / 1.2
        );
    }

    resetZoom() {
        this.svg.transition().duration(500).call(
            this.zoom.transform,
            d3.zoomIdentity
        );
    }

    showContextMenu(event, node) {
        this.hideContextMenu();

        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.position = 'fixed';
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';
        menu.style.background = 'rgba(26, 26, 26, 0.95)';
        menu.style.border = '1px solid #00ff88';
        menu.style.borderRadius = '8px';
        menu.style.padding = '8px 0';
        menu.style.zIndex = '2000';
        menu.style.minWidth = '150px';
        menu.style.backdropFilter = 'blur(10px)';
        menu.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.5)';

        const menuItems = [
            {
                text: '🔍 Szczegóły',
                action: () => this.showNodeDetails(node)
            },
            {
                text: '⚡ Zwiększ energię',
                action: () => this.increaseNodeEnergy(node)
            },
            {
                text: '🏷️ Dodaj tag',
                action: () => this.addNodeTag(node)
            },
            {
                text: '🗑️ Usuń węzeł',
                action: () => this.deleteNode(node)
            }
        ];

        menuItems.forEach(item => {
            const menuItem = document.createElement('div');
            menuItem.textContent = item.text;
            menuItem.style.padding = '8px 16px';
            menuItem.style.color = 'white';
            menuItem.style.cursor = 'pointer';
            menuItem.style.fontSize = '14px';
            menuItem.style.borderBottom = '1px solid #333';

            menuItem.addEventListener('mouseenter', () => {
                menuItem.style.background = '#00ff88';
                menuItem.style.color = '#1a1a1a';
            });

            menuItem.addEventListener('mouseleave', () => {
                menuItem.style.background = 'transparent';
                menuItem.style.color = 'white';
            });

            menuItem.addEventListener('click', () => {
                item.action();
                this.hideContextMenu();
            });

            menu.appendChild(menuItem);
        });

        // Usuń ostatnią linię
        if (menu.lastChild) {
            menu.lastChild.style.borderBottom = 'none';
        }

        document.body.appendChild(menu);

        // Zamknij menu po kliknięciu gdzie indziej
        setTimeout(() => {
            document.addEventListener('click', () => this.hideContextMenu(), { once: true });
        }, 100);
    }

    hideContextMenu() {
        const menu = document.querySelector('.context-menu');
        if (menu) {
            menu.remove();
        }
    }

    openNodeDetails(node) {
        // Usuń poprzednie okno szczegółów jeśli istnieje
        this.closeNodeDetails();

        const detailsPanel = document.createElement('div');
        detailsPanel.className = 'node-details-panel';
        detailsPanel.style.position = 'fixed';
        detailsPanel.style.top = '50%';
        detailsPanel.style.left = '50%';
        detailsPanel.style.transform = 'translate(-50%, -50%)';
        detailsPanel.style.width = '500px';
        detailsPanel.style.maxHeight = '80vh';
        detailsPanel.style.background = 'rgba(26, 26, 26, 0.98)';
        detailsPanel.style.border = '2px solid #00ff88';
        detailsPanel.style.borderRadius = '12px';
        detailsPanel.style.padding = '20px';
        detailsPanel.style.zIndex = '2000';
        detailsPanel.style.backdropFilter = 'blur(15px)';
        detailsPanel.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.8)';
        detailsPanel.style.overflowY = 'auto';
        detailsPanel.style.color = 'white';
        detailsPanel.style.fontFamily = 'monospace';

        const header = document.createElement('div');
        header.style.display = 'flex';
        header.style.justifyContent = 'space-between';
        header.style.alignItems = 'center';
        header.style.marginBottom = '20px';
        header.style.borderBottom = '1px solid #555';
        header.style.paddingBottom = '15px';

        const title = document.createElement('h2');
        title.textContent = `🧠 ${node.genesis?.name || 'Byt Bez Nazwy'}`;
        title.style.margin = '0';
        title.style.color = '#00ff88';
        title.style.fontSize = '24px';

        const closeBtn = document.createElement('button');
        closeBtn.textContent = '✕';
        closeBtn.style.background = '#ff4444';
        closeBtn.style.color = 'white';
        closeBtn.style.border = 'none';
        closeBtn.style.borderRadius = '50%';
        closeBtn.style.width = '30px';
        closeBtn.style.height = '30px';
        closeBtn.style.cursor = 'pointer';
        closeBtn.style.fontSize = '16px';
        closeBtn.style.fontWeight = 'bold';
        closeBtn.addEventListener('click', () => this.closeNodeDetails());

        header.appendChild(title);
        header.appendChild(closeBtn);

        const content = document.createElement('div');
        content.innerHTML = this.generateNodeDetailsHTML(node);

        detailsPanel.appendChild(header);
        detailsPanel.appendChild(content);

        document.body.appendChild(detailsPanel);

        // Animacja wejścia
        detailsPanel.style.opacity = '0';
        detailsPanel.style.transform = 'translate(-50%, -50%) scale(0.8)';
        setTimeout(() => {
            detailsPanel.style.transition = 'all 0.3s ease';
            detailsPanel.style.opacity = '1';
            detailsPanel.style.transform = 'translate(-50%, -50%) scale(1)';
        }, 10);

        // Zamknij po kliknięciu poza panelem
        setTimeout(() => {
            document.addEventListener('click', (e) => {
                if (!detailsPanel.contains(e.target)) {
                    this.closeNodeDetails();
                }
            }, { once: true });
        }, 100);

        // Zamknij po ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeNodeDetails();
            }
        }, { once: true });

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
                if (newScale <= 4) {
                    this.closeNodeDetails();
                    this.proximityLocked = false;
                    this.lastProximityNode = null;
                    this.nodeDetailsOpen = false;
                }
            }
        });
    }

    generateNodeDetailsHTML(node) {
        const genesis = node.genesis || {};
        const attributes = node.attributes || {};
        const memories = Array.isArray(node.memories) ? node.memories : [];
        const selfAwareness = node.self_awareness || {};

        return `
            <div style="display: grid; gap: 15px;">
                <div style="background: rgba(0, 255, 136, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #00ff88;">
                    <h3 style="margin: 0 0 10px 0; color: #00ff88;">📊 Podstawowe Informacje</h3>
                    <div><strong>Soul ID:</strong> <code>${node.soul}</code></div>
                    <div><strong>Typ:</strong> ${genesis.type || 'Nieznany'}</div>
                    <div><strong>Utworzony przez:</strong> ${genesis.created_by || 'System'}</div>
                    <div><strong>Data utworzenia:</strong> ${node.created_at || 'Nieznana'}</div>
                </div>

                ${genesis.source ? `
                <div style="background: rgba(33, 150, 243, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #2196F3;">
                    <h3 style="margin: 0 0 10px 0; color: #2196F3;">💻 Kod Źródłowy</h3>
                    <pre style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; font-size: 12px;">${genesis.source}</pre>
                </div>
                ` : ''}

                <div style="background: rgba(255, 152, 0, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #FF9800;">
                    <h3 style="margin: 0 0 10px 0; color: #FF9800;">⚡ Atrybuty</h3>
                    <div><strong>Energia:</strong> ${attributes.energy_level || 0}</div>
                    <div><strong>Tagi:</strong> ${Array.isArray(attributes.tags) ? attributes.tags.map(tag => `<span style="background: #555; padding: 2px 6px; border-radius: 3px; margin: 2px;">${tag}</span>`).join(' ') : 'Brak'}</div>
                    ${attributes.created_via ? `<div><strong>Utworzony via:</strong> ${attributes.created_via}</div>` : ''}
                    ${attributes.intention_text ? `<div><strong>Tekst intencji:</strong> "${attributes.intention_text}"</div>` : ''}
                </div>

                <div style="background: rgba(156, 39, 176, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #9C27B0;">
                    <h3 style="margin: 0 0 10px 0; color: #9C27B0;">🧠 Samoświadomość</h3>
                    <div><strong>Poziom zaufania:</strong> ${selfAwareness.trust_level || 'Nieznany'}</div>
                    <div><strong>Pewność siebie:</strong> ${selfAwareness.confidence || 'Nieznana'}</div>
                </div>

                ${memories.length > 0 ? `
                <div style="background: rgba(96, 125, 139, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #607D8B;">
                    <h3 style="margin: 0 0 10px 0; color: #607D8B;">💭 Pamięci</h3>
                    ${memories.map(memory => `
                        <div style="background: rgba(0,0,0,0.3); padding: 8px; margin: 5px 0; border-radius: 4px;">
                            <strong>${memory.type || 'Memory'}:</strong> ${memory.data || 'Brak danych'}
                        </div>
                    `).join('')}
                </div>
                ` : ''}

                <div style="background: rgba(76, 175, 80, 0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">
                    <h3 style="margin: 0 0 10px 0; color: #4CAF50;">🛠️ Akcje</h3>
                    <button onclick="window.luxosGraph.increaseNodeEnergy('${node.soul}')" style="background: #00ff88; color: #1a1a1a; border: none; padding: 8px 12px; margin: 5px; border-radius: 4px; cursor: pointer;">⚡ Zwiększ Energię</button>
                    <button onclick="window.luxosGraph.addNodeTag('${node.soul}')" style="background: #2196F3; color: white; border: none; padding: 8px 12px; margin: 5px; border-radius: 4px; cursor: pointer;">🏷️ Dodaj Tag</button>
                    <button onclick="window.luxosGraph.closeNodeDetails()" style="background: #607D8B; color: white; border: none; padding: 8px 12px; margin: 5px; border-radius: 4px; cursor: pointer;">🚪 Zamknij</button>
                </div>


            </div>
        `;
    }

    closeNodeDetails() {
        const panel = document.querySelector('.node-details-panel');
        if (panel) {
            panel.style.transition = 'all 0.3s ease';
            panel.style.opacity = '0';
            panel.style.transform = 'translate(-50%, -50%) scale(0.8)';
            setTimeout(() => {
                if (panel.parentNode) {
                    panel.remove();
                }
            }, 300);
        }
    }

    showNodeDetails(node) {
        // Przekieruj do nowej funkcji
        this.openNodeDetails(node);
    }

    increaseNodeEnergy(soulId) {
        const node = this.nodes.find(n => n.soul === soulId);
        if (!node) return;

        // Symulacja zwiększenia energii
        const newEnergyLevel = (node.attributes?.energy_level || 0) + 10;
        this.showIntentionFeedback(`Energia węzła zwiększona do ${newEnergyLevel}`, 'success');

        // Tutaj można dodać komunikację z backendem
        this.socket.emit('update_being', {
            soul: node.soul,
            attributes: {
                ...node.attributes,
                energy_level: newEnergyLevel
            }
        });
    }

    addNodeTag(soulId) {
        const node = this.nodes.find(n => n.soul === soulId);
        if (!node) return;

        const tag = prompt('Wprowadź nowy tag:');
        if (tag && tag.trim()) {
            const currentTags = Array.isArray(node.attributes?.tags) ? node.attributes.tags : [];
            if (!currentTags.includes(tag.trim())) {
                currentTags.push(tag.trim());

                // Aktualizuj lokalnie dane węzła zachowując pozycję
                const nodeIndex = this.nodes.findIndex(n => n.soul === node.soul);
                if (nodeIndex !== -1) {
                    this.nodes[nodeIndex].attributes = {
                        ...this.nodes[nodeIndex].attributes,
                        tags: currentTags
                    };
                }

                this.showIntentionFeedback(`Dodano tag: ${tag}`, 'success');

                // Wyślij do backendu
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

    deleteNode(node) {
        if (confirm(`Czy na pewno chcesz usunąć węzeł "${node.genesis?.name || 'Unnamed'}"?`)) {
            this.showIntentionFeedback('Węzeł usunięty', 'info');

            // Tutaj można dodać komunikację z backendem
            this.socket.emit('delete_being', { soul: node.soul });
        }
    }

    // Usunięto funkcję startMiddleMousePan - nie jest już potrzebna

    checkForNodeProximity(transform) {
        // Jeśli użytkownik nie opuścił strefy od ostatniego otwarcia
        if (this.proximityLocked) {
            return;
        }

        const centerX = this.width / 2;
        const centerY = this.height / 2;

        // Przekształć współrzędne centrum viewport na współrzędne grafu
        const graphCenterX = (centerX - transform.x) / transform.k;
        const graphCenterY = (centerY - transform.y) / transform.k;

        // Znajdź najbliższy węzeł do centrum viewport
        let closestNode = null;
        let minDistance = Infinity;

        this.nodes.forEach(node => {
            if (node.x !== undefined && node.y !== undefined) {
                const distance = Math.sqrt(
                    Math.pow(node.x - graphCenterX, 2) + 
                    Math.pow(node.y - graphCenterY, 2)
                );

                if (distance < minDistance && distance < 25) { // Zmniejszony obszar wykrywania do 25 jednostek
                    minDistance = distance;
                    closestNode = node;
                }
            }
        });

        // Jeśli znaleziono bliski węzeł i zoom jest wystarczająco duży, otwórz szczegóły
        if (closestNode && transform.k > 5 && !this.nodeDetailsOpen && !this.proximityLocked) {
            this.nodeDetailsOpen = true;
            this.proximityLocked = true;
            this.lastProximityNode = closestNode;
            this.openNodeDetails(closestNode);

            // Rozpocznij monitorowanie opuszczenia strefy
            this.startProximityMonitoring(transform);
        }
    }

    startProximityMonitoring(transform) {
        const checkExit = () => {
            if (!this.proximityLocked) return;

            const currentTransform = d3.zoomTransform(this.svg.node());
            const centerX = this.width / 2;
            const centerY = this.height / 2;

            const graphCenterX = (centerX - currentTransform.x) / currentTransform.k;
            const graphCenterY = (centerY - currentTransform.y) / currentTransform.k;

            if (this.lastProximityNode && this.lastProximityNode.x !== undefined && this.lastProximityNode.y !== undefined) {
                const distance = Math.sqrt(
                    Math.pow(this.lastProximityNode.x - graphCenterX, 2) + 
                    Math.pow(this.lastProximityNode.y - graphCenterY, 2)
                );

                // Jeśli oddalił się poza strefę (większy obszar do wyjścia)
                if (distance > 40 || currentTransform.k <= 4) {
                    this.proximityLocked = false;
                    this.lastProximityNode = null;
                    this.nodeDetailsOpen = false;
                    return;
                }
            }

            // Kontynuuj monitorowanie
            requestAnimationFrame(checkExit);
        };

        requestAnimationFrame(checkExit);
    }

    showIntentionFeedback(message, type = 'success') {
        const existing = document.querySelector('.intention-feedback');
        if (existing) {
            existing.remove();
        }

        const feedback = document.createElement('div');
        feedback.className = `intention-feedback ${type}`;
        feedback.textContent = message;

        feedback.style.position = 'fixed';
        feedback.style.top = '80px';
        feedback.style.right = '20px';
        feedback.style.padding = '12px 18px';
        feedback.style.borderRadius = '8px';
        feedback.style.zIndex = '1001';
        feedback.style.fontSize = '14px';
        feedback.style.fontWeight = 'bold';
        feedback.style.transform = 'translateX(100%)';
        feedback.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
        feedback.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';

        if (type === 'error') {
            feedback.style.background = '#ff4444';
            feedback.style.color = 'white';
        } else if (type === 'info') {
            feedback.style.background = '#2196F3';
            feedback.style.color = 'white';
        } else {
            feedback.style.background = '#00ff88';
            feedback.style.color = '#1a1a1a';
        }

        document.body.appendChild(feedback);

        setTimeout(() => {
            feedback.style.transform = 'translateX(0)';
        }, 10);

        setTimeout(() => {
            feedback.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.remove();
                }
            }, 300);
        }, 3000);
    }
}

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