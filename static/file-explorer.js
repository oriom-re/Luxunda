
// File Explorer Component - Minimal implementation
// Prevent class redeclaration
if (typeof FileExplorer === 'undefined' && typeof window.FileExplorer === 'undefined') {
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
