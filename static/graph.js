// ===== LUX OS GRAPH - KOMPLETNY RESET =====
// Zero błędów składni, czysta implementacja

class LuxOSGraph {
    constructor() {
        this.socket = null;
        this.beings = [];
        this.relationships = [];
        this.selectedNodes = [];
        this.isConnected = false;

        console.log('🌀 LuxDB Graph initialized');
        this.initializeConnection();
    }

    initializeConnection() {
        try {
            this.socket = io();

            this.socket.on('connect', () => {
                this.isConnected = true;
                console.log('✅ Połączono z wszechświatem LuxOS');
                this.requestGraphData();
            });

            this.socket.on('disconnect', (reason) => {
                this.isConnected = false;
                console.log('Rozłączono ze wszechświatem:', reason);
                this.attemptReconnect();
            });

            this.socket.on('graph_data', (data) => {
                console.log('📊 Otrzymano dane grafu:', data);
                this.updateGraphData(data);
            });

        } catch (error) {
            console.error('❌ Błąd inicjalizacji połączenia:', error);
        }
    }

    requestGraphData() {
        if (this.socket && this.isConnected) {
            console.log('📡 Żądanie danych grafu...');
            this.socket.emit('get_graph_data');
        }
    }

    updateGraphData(data) {
        try {
            this.beings = data.beings || [];
            this.relationships = data.relationships || [];
            this.renderUniverse();
        } catch (error) {
            console.error('❌ Błąd aktualizacji danych:', error);
        }
    }

    renderUniverse() {
        console.log(`🌌 Renderuję wszechświat z ${this.beings.length} bytami`);
        // Implementacja renderowania będzie tutaj
    }

    attemptReconnect() {
        let attempts = 0;
        const maxAttempts = 5;

        const reconnect = () => {
            attempts++;
            if (attempts <= maxAttempts) {
                console.log(`Próba reconnect ${attempts}/${maxAttempts} za ${1000 * attempts}ms`);
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.socket.connect();
                    }
                }, 1000 * attempts);
            }
        };

        reconnect();
    }

    zoomIn() {
        console.log('🔍 Zoom in');
    }

    zoomOut() {
        console.log('🔍 Zoom out');
    }

    resetZoom() {
        console.log('🔍 Reset zoom');
    }

    resizeGraph() {
        console.log('📏 Resize graph');
    }
}

console.log('✅ LuxOSGraph class defined and available globally');
window.LuxOSGraph = LuxOSGraph;