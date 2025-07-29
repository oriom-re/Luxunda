class FileExplorer {
    constructor(graphManager) {
        this.graphManager = graphManager;
        console.log('📁 File Explorer disabled');
    }
}

// Make available globally
window.FileExplorer = FileExplorer;