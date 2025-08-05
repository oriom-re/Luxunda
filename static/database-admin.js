
class LuxDBAdmin {
    constructor() {
        this.socket = null;
        this.souls = [];
        this.beings = [];
        this.relationships = [];
        this.filteredData = [];
        this.selectedNode = null;
        this.svg = null;
        this.zoomBehavior = null;
        this.simulation = null;
        
        console.log('🗄️ LuxDB Admin initialized');
        this.initializeConnection();
        this.setupEventListeners();
        this.setupModals();
    }

    initializeConnection() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true
            });

            this.socket.on('connect', () => {
                console.log('✅ Połączono z bazą danych LuxDB');
                this.requestDatabaseData();
            });

            this.socket.on('disconnect', (reason) => {
                console.log('❌ Rozłączono z bazą:', reason);
                this.showNotification('Utracono połączenie z bazą danych', 'error');
            });

            this.socket.on('graph_data', (data) => {
                console.log('📊 Otrzymano dane bazy:', data);
                this.updateDatabaseData(data);
            });

            this.socket.on('database_stats', (stats) => {
                this.updateStatistics(stats);
            });

        } catch (error) {
            console.error('❌ Błąd połączenia:', error);
            this.showNotification('Błąd połączenia z bazą danych', 'error');
        }
    }

    setupEventListeners() {
        // Filtry
        document.getElementById('searchFilter').addEventListener('input', () => this.applyFilters());
        document.getElementById('quickSearch').addEventListener('input', () => this.applyFilters());
        document.getElementById('filterSouls').addEventListener('change', () => this.applyFilters());
        document.getElementById('filterBeings').addEventListener('change', () => this.applyFilters());
        document.getElementById('filterRelations').addEventListener('change', () => this.applyFilters());
        document.getElementById('dateFrom').addEventListener('change', () => this.applyFilters());
        document.getElementById('dateTo').addEventListener('change', () => this.applyFilters());
        document.getElementById('genotypeFilter').addEventListener('change', () => this.applyFilters());

        // Toolbar buttons
        document.getElementById('refreshBtn').addEventListener('click', () => this.requestDatabaseData());
        document.getElementById('createSoulBtn').addEventListener('click', () => this.openCreateSoulModal());
        document.getElementById('createBeingBtn').addEventListener('click', () => this.openCreateBeingModal());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportData());
        document.getElementById('sqlQueryBtn').addEventListener('click', () => this.openSqlQueryModal());
        document.getElementById('cleanupBtn').addEventListener('click', () => this.cleanupDatabase());

        // Zoom controls
        document.getElementById('zoomIn').addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOut').addEventListener('click', () => this.zoomOut());
        document.getElementById('zoomReset').addEventListener('click', () => this.resetZoom());
        document.getElementById('fitScreen').addEventListener('click', () => this.fitToScreen());

        // Modal buttons
        document.getElementById('saveSoulBtn').addEventListener('click', () => this.saveSoul());
        document.getElementById('saveBeingBtn').addEventListener('click', () => this.saveBeing());
        document.getElementById('executeSqlBtn').addEventListener('click', () => this.executeSqlQuery());
    }

    setupModals() {
        const modals = document.querySelectorAll('.modal');
        const closes = document.querySelectorAll('.close');

        closes.forEach(close => {
            close.addEventListener('click', (e) => {
                e.target.closest('.modal').style.display = 'none';
            });
        });

        window.addEventListener('click', (e) => {
            modals.forEach(modal => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    requestDatabaseData() {
        if (this.socket && this.socket.connected) {
            console.log('📡 Żądanie danych z bazy...');
            this.socket.emit('request_graph_data');
            this.socket.emit('request_database_stats');
        }
    }

    updateDatabaseData(data) {
        try {
            this.souls = [];
            this.beings = data.beings || [];
            this.relationships = data.relationships || [];

            // Rozdziel souls i beings
            this.beings.forEach(being => {
                if (being._soul && being._soul.genesis && being._soul.genesis.type !== 'relation') {
                    // To jest normalny being
                } else if (being._soul && being._soul.genesis && being._soul.genesis.type === 'relation') {
                    // To jest relacja jako being
                }
            });

            this.updateGenotypeFilter();
            this.applyFilters();
            this.updateStatistics();
            
            console.log(`📊 Załadowano: ${this.beings.length} beings, ${this.relationships.length} relationships`);
            
        } catch (error) {
            console.error('❌ Błąd przetwarzania danych:', error);
            this.showNotification('Błąd przetwarzania danych z bazy', 'error');
        }
    }

    updateGenotypeFilter() {
        const genotypeFilter = document.getElementById('genotypeFilter');
        const genotypes = new Set();
        
        this.beings.forEach(being => {
            if (being._soul && being._soul.genesis && being._soul.genesis.name) {
                genotypes.add(being._soul.genesis.name);
            }
        });

        genotypeFilter.innerHTML = '<option value="">Wszystkie genotypy</option>';
        genotypes.forEach(genotype => {
            const option = document.createElement('option');
            option.value = genotype;
            option.textContent = genotype;
            genotypeFilter.appendChild(option);
        });
    }

    applyFilters() {
        const searchFilter = document.getElementById('searchFilter').value.toLowerCase();
        const quickSearch = document.getElementById('quickSearch').value.toLowerCase();
        const showSouls = document.getElementById('filterSouls').checked;
        const showBeings = document.getElementById('filterBeings').checked;
        const showRelations = document.getElementById('filterRelations').checked;
        const dateFrom = document.getElementById('dateFrom').value;
        const dateTo = document.getElementById('dateTo').value;
        const genotypeFilter = document.getElementById('genotypeFilter').value;

        const searchTerm = searchFilter || quickSearch;

        this.filteredData = this.beings.filter(being => {
            // Filtr typu
            const isRelation = being._soul && being._soul.genesis && being._soul.genesis.type === 'relation';
            if (isRelation && !showRelations) return false;
            if (!isRelation && !showBeings) return false;

            // Filtr wyszukiwania
            if (searchTerm) {
                const searchableText = [
                    being.ulid,
                    being._soul?.alias,
                    being._soul?.genesis?.name,
                    being._soul?.genesis?.type,
                    JSON.stringify(being.attributes || {})
                ].join(' ').toLowerCase();
                
                if (!searchableText.includes(searchTerm)) return false;
            }

            // Filtr daty
            if (dateFrom || dateTo) {
                const beingDate = new Date(being.created_at);
                if (dateFrom && beingDate < new Date(dateFrom)) return false;
                if (dateTo && beingDate > new Date(dateTo)) return false;
            }

            // Filtr genotypu
            if (genotypeFilter && being._soul?.genesis?.name !== genotypeFilter) {
                return false;
            }

            return true;
        });

        this.renderDatabaseGraph();
    }

    renderDatabaseGraph() {
        console.log(`🎨 Renderuję graf z ${this.filteredData.length} elementami`);

        // Clear previous graph
        d3.select('#database-graph').selectAll('*').remove();

        const container = document.querySelector('.graph-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        // Create SVG
        this.svg = d3.select('#database-graph')
            .attr('width', width)
            .attr('height', height);

        // Create main group
        const g = this.svg.append('g').attr('class', 'main-group');

        // Zoom behavior
        this.zoomBehavior = d3.zoom()
            .scaleExtent([0.1, 5])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        this.svg.call(this.zoomBehavior);

        // Add gradients
        const defs = this.svg.append('defs');
        
        // Soul gradient
        const soulGradient = defs.append('radialGradient')
            .attr('id', 'soulGradient')
            .attr('cx', '30%').attr('cy', '30%');
        soulGradient.append('stop').attr('offset', '0%').attr('stop-color', '#00ff88').attr('stop-opacity', 1);
        soulGradient.append('stop').attr('offset', '100%').attr('stop-color', '#00cc66').attr('stop-opacity', 0.8);

        // Being gradient
        const beingGradient = defs.append('radialGradient')
            .attr('id', 'beingGradient')
            .attr('cx', '30%').attr('cy', '30%');
        beingGradient.append('stop').attr('offset', '0%').attr('stop-color', '#0088ff').attr('stop-opacity', 1);
        beingGradient.append('stop').attr('offset', '100%').attr('stop-color', '#0066cc').attr('stop-opacity', 0.8);

        // Relation gradient
        const relationGradient = defs.append('radialGradient')
            .attr('id', 'relationGradient')
            .attr('cx', '30%').attr('cy', '30%');
        relationGradient.append('stop').attr('offset', '0%').attr('stop-color', '#ff8800').attr('stop-opacity', 1);
        relationGradient.append('stop').attr('offset', '100%').attr('stop-color', '#cc6600').attr('stop-opacity', 0.8);

        // Arrow marker
        defs.append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 13)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 13)
            .attr('markerHeight', 13)
            .append('path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999');

        // Create nodes data
        const nodes = this.filteredData.map((being, i) => {
            const isRelation = being._soul && being._soul.genesis && being._soul.genesis.type === 'relation';
            return {
                id: being.ulid,
                name: being._soul?.genesis?.name || `Element ${i}`,
                alias: being._soul?.alias || '',
                type: isRelation ? 'relation' : 'being',
                being: being,
                x: width/2 + Math.cos(i * 2 * Math.PI / this.filteredData.length) * 200,
                y: height/2 + Math.sin(i * 2 * Math.PI / this.filteredData.length) * 200
            };
        });

        // Create links from relationships
        const links = [];
        this.relationships.forEach(rel => {
            const sourceNode = nodes.find(n => n.id === rel.source_uid);
            const targetNode = nodes.find(n => n.id === rel.target_uid);
            
            if (sourceNode && targetNode) {
                links.push({
                    source: rel.source_uid,
                    target: rel.target_uid,
                    type: rel.relation_type || 'connection',
                    strength: parseFloat(rel.strength) || 1.0,
                    relationship: rel
                });
            }
        });

        // Force simulation
        this.simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(width/2, height/2))
            .force('collision', d3.forceCollide().radius(30));

        // Draw links
        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'link')
            .style('stroke', d => this.getLinkColor(d.type))
            .style('stroke-width', d => Math.max(1, d.strength * 3))
            .style('opacity', 0.7);

        // Draw nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('class', d => `node ${d.type}`)
            .attr('r', d => d.type === 'relation' ? 15 : 20)
            .style('cursor', 'pointer')
            .call(d3.drag()
                .on('start', (event, d) => {
                    if (!event.active) this.simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                    event.sourceEvent?.stopPropagation();
                })
                .on('drag', (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on('end', (event, d) => {
                    if (!event.active) this.simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }))
            .on('click', (event, d) => {
                this.selectNode(d);
                event.stopPropagation();
            })
            .on('contextmenu', (event, d) => {
                event.preventDefault();
                this.showContextMenu(event, d);
            });

        // Add node labels
        const labels = g.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('class', 'node-label')
            .text(d => d.alias || d.name)
            .style('font-size', d => d.type === 'relation' ? '8px' : '10px');

        // Add relation labels
        const relationLabels = g.append('g')
            .selectAll('text')
            .data(links)
            .enter().append('text')
            .attr('class', 'relation-label')
            .text(d => `${d.type} (${Math.round(d.strength * 100)}%)`);

        // Update positions on simulation tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            labels
                .attr('x', d => d.x)
                .attr('y', d => d.y + 5);

            relationLabels
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2 - 5);
        });

        console.log(`✨ Wyrenderowano graf z ${nodes.length} węzłami i ${links.length} połączeniami`);
    }

    getLinkColor(type) {
        const colors = {
            'connection': '#888',
            'similarity': '#00ff88',
            'relation_being': '#0088ff',
            'communication': '#ff8800',
            'hierarchy': '#ff0088'
        };
        return colors[type] || '#888';
    }

    selectNode(node) {
        // Usuń poprzednie zaznaczenie
        d3.selectAll('.node').classed('selected', false);
        
        // Zaznacz nowy węzeł
        d3.selectAll('.node').filter(d => d.id === node.id).classed('selected', true);
        
        this.selectedNode = node;
        this.showNodeDetails(node);
    }

    showNodeDetails(node) {
        const panel = document.getElementById('detailsPanel');
        const header = document.getElementById('detailsHeader');
        const content = document.getElementById('detailsContent');

        header.textContent = `${node.type === 'relation' ? '🔗' : '🧬'} ${node.name}`;

        let html = '';
        html += `<div class="property"><span class="property-key">ULID:</span><span class="property-value">${node.id}</span></div>`;
        html += `<div class="property"><span class="property-key">Typ:</span><span class="property-value">${node.type}</span></div>`;
        html += `<div class="property"><span class="property-key">Alias:</span><span class="property-value">${node.alias || 'Brak'}</span></div>`;
        
        if (node.being.created_at) {
            html += `<div class="property"><span class="property-key">Utworzono:</span><span class="property-value">${new Date(node.being.created_at).toLocaleString()}</span></div>`;
        }

        if (node.being._soul) {
            html += `<div class="property"><span class="property-key">Soul Hash:</span><span class="property-value">${node.being.soul_uid?.substring(0, 16)}...</span></div>`;
            
            if (node.being._soul.genesis) {
                html += `<div class="property"><span class="property-key">Genesis:</span><span class="property-value">${JSON.stringify(node.being._soul.genesis, null, 2)}</span></div>`;
            }
        }

        if (node.being.attributes && Object.keys(node.being.attributes).length > 0) {
            html += `<div class="property"><span class="property-key">Atrybuty:</span><span class="property-value"><pre>${JSON.stringify(node.being.attributes, null, 2)}</pre></span></div>`;
        }

        content.innerHTML = html;
        panel.style.display = 'block';
    }

    updateStatistics(stats = null) {
        const souls = this.beings.filter(b => b._soul && b._soul.genesis && b._soul.genesis.type !== 'relation').length;
        const beings = this.beings.filter(b => !b._soul || !b._soul.genesis || b._soul.genesis.type !== 'relation').length;
        const relations = this.relationships.length;

        document.getElementById('statSouls').textContent = souls;
        document.getElementById('statBeings').textContent = beings;
        document.getElementById('statRelations').textContent = relations;
        
        if (stats && stats.tables) {
            document.getElementById('statTables').textContent = stats.tables;
        }
    }

    // Modal functions
    openCreateSoulModal() {
        document.getElementById('createSoulModal').style.display = 'block';
    }

    openCreateBeingModal() {
        // Populate soul selector
        const select = document.getElementById('beingSoulSelect');
        select.innerHTML = '<option value="">Wybierz genotyp...</option>';
        
        this.beings.forEach(being => {
            if (being._soul && being._soul.genesis && being._soul.genesis.type !== 'relation') {
                const option = document.createElement('option');
                option.value = being.soul_uid;
                option.textContent = `${being._soul.alias} (${being._soul.genesis.name})`;
                select.appendChild(option);
            }
        });
        
        document.getElementById('createBeingModal').style.display = 'block';
    }

    openSqlQueryModal() {
        document.getElementById('sqlQueryModal').style.display = 'block';
    }

    saveSoul() {
        const alias = document.getElementById('soulAlias').value;
        const genotype = document.getElementById('soulGenotype').value;

        if (!alias || !genotype) {
            this.showNotification('Wypełnij wszystkie pola', 'error');
            return;
        }

        try {
            const genotypeObj = JSON.parse(genotype);
            
            this.socket.emit('create_soul', {
                alias: alias,
                genotype: genotypeObj
            });

            document.getElementById('createSoulModal').style.display = 'none';
            this.showNotification('Soul został utworzony', 'success');
            
        } catch (error) {
            this.showNotification('Błędny format JSON genotypu', 'error');
        }
    }

    saveBeing() {
        const soulHash = document.getElementById('beingSoulSelect').value;
        const alias = document.getElementById('beingAlias').value;
        const data = document.getElementById('beingData').value;

        if (!soulHash || !alias || !data) {
            this.showNotification('Wypełnij wszystkie pola', 'error');
            return;
        }

        try {
            const dataObj = JSON.parse(data);
            
            this.socket.emit('create_being', {
                soul_hash: soulHash,
                alias: alias,
                data: dataObj
            });

            document.getElementById('createBeingModal').style.display = 'none';
            this.showNotification('Being został utworzony', 'success');
            
        } catch (error) {
            this.showNotification('Błędny format JSON danych', 'error');
        }
    }

    executeSqlQuery() {
        const query = document.getElementById('sqlQuery').value;
        if (!query.trim()) {
            this.showNotification('Wprowadź zapytanie SQL', 'error');
            return;
        }

        this.socket.emit('execute_sql', { query: query });
        
        this.socket.once('sql_result', (result) => {
            document.getElementById('sqlResult').value = JSON.stringify(result, null, 2);
        });
    }

    exportData() {
        const data = {
            beings: this.filteredData,
            relationships: this.relationships,
            exported_at: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `luxdb_export_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);

        this.showNotification('Dane wyeksportowane', 'success');
    }

    cleanupDatabase() {
        if (confirm('Czy na pewno chcesz wyczyścić nieużywane dane z bazy? Ta operacja jest nieodwracalna.')) {
            this.socket.emit('cleanup_database');
            this.showNotification('Rozpoczęto czyszczenie bazy danych', 'info');
        }
    }

    // Zoom functions
    zoomIn() {
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().duration(300).call(this.zoomBehavior.scaleBy, 1.5);
        }
    }

    zoomOut() {
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().duration(300).call(this.zoomBehavior.scaleBy, 0.67);
        }
    }

    resetZoom() {
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().duration(500).call(
                this.zoomBehavior.transform,
                d3.zoomIdentity
            );
        }
    }

    fitToScreen() {
        if (!this.svg || !this.simulation) return;

        const nodes = this.simulation.nodes();
        if (nodes.length === 0) return;

        const bounds = nodes.reduce((acc, node) => ({
            minX: Math.min(acc.minX, node.x),
            maxX: Math.max(acc.maxX, node.x),
            minY: Math.min(acc.minY, node.y),
            maxY: Math.max(acc.maxY, node.y)
        }), { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity });

        const width = bounds.maxX - bounds.minX;
        const height = bounds.maxY - bounds.minY;
        const centerX = (bounds.minX + bounds.maxX) / 2;
        const centerY = (bounds.minY + bounds.maxY) / 2;

        const svgWidth = this.svg.node().clientWidth;
        const svgHeight = this.svg.node().clientHeight;

        const scale = Math.min(svgWidth / width, svgHeight / height) * 0.8;
        const translateX = svgWidth / 2 - centerX * scale;
        const translateY = svgHeight / 2 - centerY * scale;

        this.svg.transition().duration(750).call(
            this.zoomBehavior.transform,
            d3.zoomIdentity.translate(translateX, translateY).scale(scale)
        );
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.luxDBAdmin = new LuxDBAdmin();
});
