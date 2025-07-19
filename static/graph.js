
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
            this.socket.emit('get_graph_data');
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
            // Graf zostanie automatycznie odświeżony przez broadcast_graph_update
        });

        this.socket.on('relationship_created', (relationship) => {
            console.log('Nowa relacja utworzona:', relationship);
            // Graf zostanie automatycznie odświeżony przez broadcast_graph_update
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

        // Dodaj zoom i pan
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {
                this.container.attr("transform", event.transform);
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
            .append("line")
            .attr("class", "link");

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

        nodeUpdate.on("click", (event, d) => {
            this.handleNodeClick(event, d);
        });

        this.simulation.nodes(this.nodes);
        this.simulation.force("link").links(this.links.map(d => ({
            source: d.source_soul,
            target: d.target_soul
        })));

        this.simulation.on("tick", () => {
            this.linkGroup.selectAll(".link")
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

    handleNodeClick(event, node) {
        event.stopPropagation();

        if (this.selectedNodes.includes(node.soul)) {
            this.selectedNodes = this.selectedNodes.filter(s => s !== node.soul);
        } else {
            this.selectedNodes.push(node.soul);
        }

        this.nodeGroup.selectAll(".node")
            .classed("selected", d => this.selectedNodes.includes(d.soul));

        console.log('Selected nodes:', this.selectedNodes);
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
        
        // Odśwież graf raz po wykonaniu wszystkich akcji
        setTimeout(() => {
            this.socket.emit('get_graph_data');
        }, 100);
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
