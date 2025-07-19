class LuxOSGraph {
    constructor() {
        this.socket = null;
        this.nodes = [];
        this.links = [];
        this.selectedNodes = [];
        this.simulation = null;
        this.svg = null;
        this.nodeGroup = null;
        this.linkGroup = null;
        this.labelGroup = null;

        this.initSocket();
        this.initGraph();
        this.setupEventListeners();
        this.initIntentionSystem();
    }

    initSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Połączono z serwerem');
            this.updateStatus('Połączono', 'connected');
        });

        this.socket.on('disconnect', () => {
            console.log('Rozłączono z serwerem');
            this.updateStatus('Rozłączono', 'disconnected');
        });

        this.socket.on('graph_data', (data) => {
            this.updateGraph(data.nodes, data.links);
        });

        this.socket.on('graph_updated', (data) => {
            this.updateGraph(data.nodes, data.links);
        });

        this.socket.on('being_created', (being) => {
            console.log('Utworzono nowy byt:', being);
        });

        this.socket.on('relationship_created', (relationship) => {
            console.log('Utworzono nową relację:', relationship);
        });

        this.socket.on('error', (error) => {
            console.error('Błąd:', error.message);
            alert('Błąd: ' + error.message);
        });

        this.socket.on('intention_response', (response) => {
            console.log('Odpowiedź na intencję:', response);
            this.showIntentionFeedback(response.message || 'Intencja przetworzona');

            if (response.actions) {
                // Automatyczne wykonanie akcji na podstawie intencji
                this.executeIntentionActions(response.actions);
            }
        });

        this.socket.on('intention_response', (data) => {
            this.handleIntentionResponse(data);
        });

        this.socket.on('function_registered', (data) => {
            this.handleFunctionRegistered(data);
        });

        this.socket.on('function_executed', (data) => {
            this.handleFunctionExecuted(data);
        });

        this.socket.on('registered_functions', (data) => {
            this.showRegisteredFunctionsList(data);
        });

        this.socket.on('being_source', (data) => {
            this.showSourceCode(data);
        });
    }

    initGraph() {
        const graphElement = document.getElementById('graph');
        const width = window.innerWidth;
        const height = window.innerHeight - 190; // Account for header and intention system

        this.svg = d3.select('#graph')
            .attr('width', width)
            .attr('height', height);

        // Definicje gradientów i markerów
        const defs = this.svg.append('defs');

        // Marker dla strzałek
        defs.append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#999');

        // Grupy dla różnych elementów
        this.linkGroup = this.svg.append('g').attr('class', 'links');
        this.nodeGroup = this.svg.append('g').attr('class', 'nodes');
        this.labelGroup = this.svg.append('g').attr('class', 'labels');

        // Zoom i pan
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                const { transform } = event;
                this.nodeGroup.attr('transform', transform);
                this.linkGroup.attr('transform', transform);
                this.labelGroup.attr('transform', transform);
            });

        this.svg.call(zoom);

        // Symulacja fizyki
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.soul).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));
    }

    updateGraph(nodes, links) {
        this.nodes = nodes.map(d => ({
            ...d,
            x: d.x || Math.random() * 800,
            y: d.y || Math.random() * 600
        }));

        this.links = links.map(d => ({
            ...d,
            source: d.source_soul,
            target: d.target_soul
        }));

        // Aktualizuj statystyki
        document.getElementById('nodesCount').textContent = this.nodes.length;
        document.getElementById('linksCount').textContent = this.links.length;

        this.renderGraph();
    }

    renderGraph() {
        // Renderowanie linków
        const link = this.linkGroup
            .selectAll('.link')
            .data(this.links, d => d.id);

        link.exit().remove();

        const linkEnter = link.enter()
            .append('line')
            .attr('class', 'link')
            .attr('marker-end', 'url(#arrowhead)');

        const linkUpdate = linkEnter.merge(link);

        // Renderowanie węzłów
        const node = this.nodeGroup
            .selectAll('.node')
            .data(this.nodes, d => d.soul);

        node.exit().remove();

        const nodeEnter = node.enter()
            .append('circle')
            .attr('class', 'node')
            .attr('r', d => Math.max(15, (d.energy_level || d.attributes?.energy_level || 50) / 2))
            .attr('fill', d => this.getNodeColor(d))
            .call(this.drag());

        const nodeUpdate = nodeEnter.merge(node)
            .attr('r', d => Math.max(15, (d.energy_level || d.attributes?.energy_level || 50) / 2))
            .attr('fill', d => this.getNodeColor(d));

        // Event listenery dla węzłów
        nodeUpdate.on('click', (event, d) => {
            this.selectNode(d);
        });

        // Renderowanie etykiet
        const label = this.labelGroup
            .selectAll('.node-label')
            .data(this.nodes, d => d.soul);

        label.exit().remove();

        const labelEnter = label.enter()
            .append('text')
            .attr('class', 'node-label')
            .text(d => (d.genesis && d.genesis.name) || (d.soul ? d.soul.substring(0, 8) : 'Węzeł'));

        const labelUpdate = labelEnter.merge(label);

        // Aktualizacja symulacji
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);

        this.simulation.on('tick', () => {
            linkUpdate
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodeUpdate
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            labelUpdate
                .attr('x', d => d.x)
                .attr('y', d => d.y + 5);
        });

        this.simulation.alpha(1).restart();
    }

    getNodeColor(node) {
        const type = (node.genesis && node.genesis.type) || 'unknown';
        const colors = {
            'function': '#4CAF50',
            'class': '#2196F3',
            'runtime': '#FF9800',
            'kernel': '#F44336',
            'unknown': '#9E9E9E'
        };
        return colors[type] || colors.unknown;
    }

    selectNode(node) {
        // Usuwanie poprzednich zaznaczeń
        this.nodeGroup.selectAll('.node').classed('selected', false);

        // Dodawanie do listy wybranych
        const index = this.selectedNodes.findIndex(n => n.soul === node.soul);
        if (index === -1) {
            if (this.selectedNodes.length >= 2) {
                this.selectedNodes.shift(); // Usuń najstarszy wybór
            }
            this.selectedNodes.push(node);
        }

        // Zaznaczanie wybranych węzłów
        this.selectedNodes.forEach(selectedNode => {
            this.nodeGroup.selectAll('.node')
                .filter(d => d.soul === selectedNode.soul)
                .classed('selected', true);
        });

        // Wyświetlanie szczegółów
        this.showNodeDetails(node);

        console.log('Wybrane węzły:', this.selectedNodes.map(n => (n.genesis && n.genesis.name) || n.soul || 'Nieznany'));
    }

    showNodeDetails(node) {
        const panel = document.getElementById('selectedInfo');
        const details = document.getElementById('beingDetails');

        // Bezpieczne pobieranie wartości
        const soul = node.soul || 'Nieznane';
        const name = (node.genesis && node.genesis.name) || 'Brak';
        const type = (node.genesis && node.genesis.type) || 'Nieznany';
        const energyLevel = node.energy_level || node.attributes?.energy_level || 0;
        const tags = node.tags || node.attributes?.tags || [];

        let html = `
            <strong>Soul:</strong> ${soul}<br>
            <strong>Nazwa:</strong> ${name}<br>
            <strong>Typ:</strong> ${type}<br>
            <strong>Energia:</strong> 
            <div class="energy-bar">
                <div class="energy-fill" style="width: ${energyLevel}%"></div>
            </div>
            ${energyLevel}/100<br>
            <strong>Tagi:</strong><br>
        `;

        if (Array.isArray(tags)) {
            tags.forEach(tag => {
                html += `<span class="tag">${tag}</span>`;
            });
        }

        html += `<br><br><strong>Atrybuty:</strong><br>
            <pre style="font-size: 10px; background: #333; padding: 5px; border-radius: 3px; overflow-x: auto;">
${JSON.stringify(node.attributes || {}, null, 2)}</pre>`;

        if (node.memories && node.memories.length > 0) {
            html += `<br><strong>Wspomnienia:</strong><br>
                <pre style="font-size: 10px; background: #333; padding: 5px; border-radius: 3px; overflow-x: auto;">
${JSON.stringify(node.memories, null, 2)}</pre>`;
        }

        details.innerHTML = html;
        panel.style.display = 'block';
    }

    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            const width = window.innerWidth;
            const height = window.innerHeight - 190;

            this.svg.attr('width', width).attr('height', height);
            this.simulation.force('center', d3.forceCenter(width / 2, height / 2));
            this.simulation.alpha(1).restart();
        });
    }

    initIntentionSystem() {
        const intentionInput = document.getElementById('intentionInput');
        const sendButton = document.getElementById('sendIntention');
        const charCounter = document.getElementById('charCounter');

        // Auto-resize textarea
        intentionInput.addEventListener('input', () => {
            this.autoResizeTextarea(intentionInput);
            this.updateCharCounter(intentionInput, charCounter, sendButton);
            this.processEmoticons(intentionInput);
        });

        // Send intention on button click
        sendButton.addEventListener('click', () => {
            this.sendIntention();
        });

        // Send intention on Ctrl+Enter
        intentionInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.sendIntention();
            }
        });
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        const newHeight = Math.min(Math.max(textarea.scrollHeight, 40), 200);
        textarea.style.height = newHeight + 'px';
    }

    updateCharCounter(input, counter, button) {
        const length = input.value.length;
        const maxLength = 500;

        counter.textContent = `${length}/${maxLength}`;

        if (length > maxLength * 0.9) {
            counter.className = 'intention-counter danger';
        } else if (length > maxLength * 0.7) {
            counter.className = 'intention-counter warning';
        } else {
            counter.className = 'intention-counter';
        }

        button.disabled = length === 0 || length > maxLength;
    }

    processEmoticons(input) {
        const cursorPos = input.selectionStart;
        let text = input.value;

        // Mapa emotikonów
        const emoticonMap = {
            ':D': '😃',
            ':)': '😊',
            ':(': '😞',
            ':P': '😛',
            ';)': '😉',
            ':o': '😮',
            ':O': '😲',
            ':|': '😐',
            ':/': '😕',
            '<3': '❤️',
            '</3': '💔',
            ':*': '😘'
        };

        let replaced = false;
        for (const [emoticon, emoji] of Object.entries(emoticonMap)) {
            if (text.includes(emoticon)) {
                text = text.replaceAll(emoticon, emoji);
                replaced = true;
            }
        }

        if (replaced) {
            input.value = text;
            input.setSelectionRange(cursorPos, cursorPos);
        }
    }

    sendIntention() {
        const intentionInput = document.getElementById('intentionInput');
        const intention = intentionInput.value.trim();

        if (!intention) return;

        // Wyślij intencję przez Socket.IO
        this.socket.emit('process_intention', {
            intention: intention,
            context: {
                selected_nodes: this.selectedNodes.map(n => n.soul),
                timestamp: new Date().toISOString(),
                graph_state: {
                    nodes_count: this.nodes.length,
                    links_count: this.links.length
                }
            }
        });

        console.log('Wysłano intencję:', intention);

        // Wyczyść pole i zresetuj wysokość
        intentionInput.value = '';
        intentionInput.style.height = '40px';
        document.getElementById('charCounter').textContent = '0/500';
        document.getElementById('charCounter').className = 'intention-counter';
        document.getElementById('sendIntention').disabled = true;

        // Pokaż feedback
        this.showIntentionFeedback('Intencja wysłana...');
    }

    showIntentionFeedback(message) {
        // Tymczasowe powiadomienie w prawym górnym rogu
        const feedback = document.createElement('div');
        feedback.style.position = 'fixed';
        feedback.style.top = '60px';
        feedback.style.right = '10px';
        feedback.style.background = '#00ff88';
        feedback.style.color = 'black';
        feedback.style.padding = '10px 15px';
        feedback.style.borderRadius = '5px';
        feedback.style.zIndex = '1001';
        feedback.style.fontSize = '14px';
        feedback.textContent = message;

        document.body.appendChild(feedback);

        setTimeout(() => {
            feedback.remove();
        }, 3000);
    }

    executeIntentionActions(actions) {
        actions.forEach(action => {
            switch (action.type) {
                case 'create_being':
                    this.socket.emit('create_being', action.data);
                    break;
                case 'create_relationship':
                    this.socket.emit('create_relationship', action.data);
                    break;
                case 'select_nodes':
                    action.data.souls.forEach(soul => {
                        const node = this.nodes.find(n => n.soul === soul);
                        if (node) this.selectNode(node);
                    });
                    break;
                case 'highlight_path':
                    this.highlightPath(action.data.from, action.data.to);
                    break;
                default:
                    console.log('Nieznana akcja intencji:', action);
            }
        });
    }

    highlightPath(fromSoul, toSoul) {
        // Proste podświetlenie ścieżki między węzłami
        this.linkGroup.selectAll('.link')
            .classed('highlighted', d => 
                (d.source.soul === fromSoul && d.target.soul === toSoul) ||
                (d.source.soul === toSoul && d.target.soul === fromSoul)
            );

        setTimeout(() => {
            this.linkGroup.selectAll('.link').classed('highlighted', false);
        }, 3000);
    }

    updateStatus(message, type) {
        const statusElement = document.getElementById('connectionStatus');
        const dotElement = document.getElementById('connectionDot');

        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `status-${type}`;
        }

        if (dotElement) {
            if (type === 'connected') {
                dotElement.classList.add('connected');
            } else {
                dotElement.classList.remove('connected');
            }
        }
    }

    processIntention(intention) {
        // Wyślij intencję przez Socket.IO
        this.socket.emit('process_intention', {
            intention: intention,
            context: {
                selected_nodes: this.selectedNodes.map(n => n.soul),
                timestamp: new Date().toISOString(),
                graph_state: {
                    nodes_count: this.nodes.length,
                    links_count: this.links.length
                }
            }
        });

        console.log('Wysłano intencję:', intention);
        this.showFeedback('Intencja wysłana... 🚀');
    }

    showFeedback(message) {
        // Usuń poprzednie powiadomienie
        const existing = document.querySelector('.feedback-message');
        if (existing) {
            existing.remove();
        }

        // Utwórz nowe powiadomienie
        const feedback = document.createElement('div');
        feedback.className = 'feedback-message';
        feedback.textContent = message;

        document.body.appendChild(feedback);

        // Animacja pojawienia się
        setTimeout(() => {
            feedback.classList.add('show');
        }, 100);

        // Automatyczne usunięcie po 3 sekundach
        setTimeout(() => {
            feedback.classList.remove('show');
            setTimeout(() => {
                feedback.remove();
            }, 300);
        }, 3000);
    }

    handleIntentionResponse(data) {
        console.log('Odpowiedź na intencję:', data);

        if (data.actions && data.actions.length > 0) {
            data.actions.forEach(action => {
                if (action.type === 'create_being') {
                    this.socket.emit('create_being', action.data);
                } else if (action.type === 'create_relationship') {
                    this.socket.emit('create_relationship', action.data);
                }
            });
        }

        this.showFeedback(data.message || 'Intencja przetworzona! ✨');
        this.updateStatus('Połączono', 'connected');
    }

    handleFunctionRegistered(data) {
        console.log('Funkcja zarejestrowana:', data);
        this.showFeedback('Funkcja zarejestrowana! ✅');
    }

    handleFunctionExecuted(data) {
        console.log('Funkcja wykonana:', data);
        this.showFeedback('Funkcja wykonana! 🚀');
    }

    showRegisteredFunctionsList(data) {
        console.log('Lista funkcji:', data);
    }

    showSourceCode(data) {
        console.log('Kod źródłowy:', data);
        alert(`Kod źródłowy:\n\n${data.source}`);
    }
}

// Inicjalizacja - przeniesiona do HTML