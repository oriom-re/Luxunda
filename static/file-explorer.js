
// File Explorer Component - Minimal implementation
// Prevent redeclaration - ULTIMATE PROTECTION
if (typeof FileExplorer === 'undefined' && typeof window.FileExplorer === 'undefined' && !window.fileExplorerLoaded) {
window.fileExplorerLoaded = true;
    class FileExplorer {
        constructor() {
            console.log('📁 FileExplorer stub initialized');
        }
    }
    
    window.FileExplorer = FileExplorer;
} else {
    console.log('⚠️ FileExplorer already defined, skipping redefinition');
}

console.log('📁 File Explorer loaded');
