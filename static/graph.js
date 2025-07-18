
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
    }
    
    initGraph() {
        const container = d3.select('#graph-container');
        const width = container.node().getBoundingClientRect().width;
        const height = container.node().getBoundingClientRect().height;
        
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
            .attr('r', d => Math.max(15, d.energy_level / 2))
            .attr('fill', d => this.getNodeColor(d))
            .call(this.drag());
        
        const nodeUpdate = nodeEnter.merge(node)
            .attr('r', d => Math.max(15, d.energy_level / 2))
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
            .text(d => d.genesis.name || d.soul.substring(0, 8));
        
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
        const type = node.genesis.type || 'unknown';
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
        
        console.log('Wybrane węzły:', this.selectedNodes.map(n => n.genesis.name || n.soul));
    }
    
    showNodeDetails(node) {
        const panel = document.getElementById('selectedInfo');
        const details = document.getElementById('beingDetails');
        
        let html = `
            <strong>Soul:</strong> ${node.soul}<br>
            <strong>Nazwa:</strong> ${node.genesis.name || 'Brak'}<br>
            <strong>Typ:</strong> ${node.genesis.type || 'Nieznany'}<br>
            <strong>Energia:</strong> 
            <div class="energy-bar">
                <div class="energy-fill" style="width: ${node.energy_level}%"></div>
            </div>
            ${node.energy_level}/100<br>
            <strong>Tagi:</strong><br>
        `;
        
        node.tags.forEach(tag => {
            html += `<span class="tag">${tag}</span>`;
        });
        
        html += `<br><br><strong>Atrybuty:</strong><br>
            <pre style="font-size: 10px; background: #333; padding: 5px; border-radius: 3px; overflow-x: auto;">
${JSON.stringify(node.attributes, null, 2)}</pre>`;
        
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
            const container = d3.select('#graph-container');
            const width = container.node().getBoundingClientRect().width;
            const height = container.node().getBoundingClientRect().height;
            
            this.svg.attr('width', width).attr('height', height);
            this.simulation.force('center', d3.forceCenter(width / 2, height / 2));
            this.simulation.alpha(1).restart();
        });
    }
    
    updateStatus(message, type) {
        const status = document.getElementById('status');
        status.textContent = message;
        status.className = `status-${type}`;
    }
}

// Funkcje globalne dla UI
function createBeing() {
    const name = document.getElementById('newBeingName').value;
    const type = document.getElementById('newBeingType').value;
    const energy = parseInt(document.getElementById('newBeingEnergy').value);
    const tagsStr = document.getElementById('newBeingTags').value;
    
    if (!name) {
        alert('Podaj nazwę bytu');
        return;
    }
    
    const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()) : [];
    
    const beingData = {
        genesis: {
            name: name,
            type: type,
            source: `# Wygenerowany byt: ${name}\nclass ${name}:\n    pass`,
            created_by: 'frontend'
        },
        tags: tags,
        energy_level: energy,
        attributes: {
            created_via: 'frontend',
            initial_energy: energy
        },
        memories: [],
        self_awareness: {
            trust_level: 0.5,
            confidence: 0.7
        }
    };
    
    graph.socket.emit('create_being', beingData);
    
    // Wyczyść formularz
    document.getElementById('newBeingName').value = '';
    document.getElementById('newBeingTags').value = '';
    document.getElementById('newBeingEnergy').value = '50';
}

function createRelationship() {
    if (graph.selectedNodes.length !== 2) {
        alert('Wybierz dokładnie dwa byty w grafie');
        return;
    }
    
    const type = document.getElementById('relationshipType').value;
    const [source, target] = graph.selectedNodes;
    
    const relationshipData = {
        source_soul: source.soul,
        target_soul: target.soul,
        genesis: {
            type: type,
            created_via: 'frontend',
            description: `${source.genesis.name || 'Byt'} ${type} ${target.genesis.name || 'Byt'}`
        },
        tags: [type, 'frontend'],
        energy_level: 50,
        attributes: {
            created_via: 'frontend'
        }
    };
    
    graph.socket.emit('create_relationship', relationshipData);
    
    // Wyczyść wybrane węzły
    graph.selectedNodes = [];
    graph.nodeGroup.selectAll('.node').classed('selected', false);
}

function applyFilter() {
    const filterType = document.getElementById('filterType').value;
    const filterValue = document.getElementById('filterValue').value.toLowerCase();
    
    if (filterType === 'all') {
        graph.nodeGroup.selectAll('.node').style('opacity', 1);
        graph.linkGroup.selectAll('.link').style('opacity', 0.6);
        return;
    }
    
    graph.nodeGroup.selectAll('.node').style('opacity', d => {
        if (filterType === 'energy') {
            const threshold = parseInt(filterValue) || 0;
            return d.energy_level >= threshold ? 1 : 0.2;
        } else if (filterType === 'tag') {
            return d.tags.some(tag => tag.toLowerCase().includes(filterValue)) ? 1 : 0.2;
        }
        return 1;
    });
    
    // Ukryj linki do niewidocznych węzłów
    graph.linkGroup.selectAll('.link').style('opacity', d => {
        const sourceVisible = graph.nodeGroup.select(`[data-soul="${d.source.soul}"]`).style('opacity') === '1';
        const targetVisible = graph.nodeGroup.select(`[data-soul="${d.target.soul}"]`).style('opacity') === '1';
        return sourceVisible && targetVisible ? 0.6 : 0.1;
    });
}

function clearFilter() {
    document.getElementById('filterValue').value = '';
    document.getElementById('filterType').value = 'all';
    applyFilter();
}

// Inicjalizacja
let graph;
document.addEventListener('DOMContentLoaded', () => {
    graph = new LuxOSGraph();
});
