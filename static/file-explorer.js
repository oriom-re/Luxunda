
class FileExplorer {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.isVisible = true;
        this.currentPath = '.';
        this.expandedFolders = new Set();
        
        this.createFileExplorer();
        this.setupEventListeners();
        this.loadFiles();

        console.log('FileExplorer initialized');
    }

    createFileExplorer() {
        // Główny kontener eksploratora
        this.explorerContainer = document.createElement('div');
        this.explorerContainer.className = 'file-explorer-container';
        this.explorerContainer.style.cssText = `
            position: fixed;
            left: 0;
            top: 70px;
            width: 280px;
            height: calc(100vh - 70px - 120px);
            background: rgba(26, 26, 26, 0.95);
            border-right: 2px solid #00ff88;
            backdrop-filter: blur(10px);
            z-index: 1500;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 5px 0 20px rgba(0, 255, 136, 0.2);
        `;

        // Header eksploratora
        const explorerHeader = document.createElement('div');
        explorerHeader.className = 'explorer-header';
        explorerHeader.style.cssText = `
            background: linear-gradient(45deg, #00ff88, #00cc66);
            color: #1a1a1a;
            padding: 12px 15px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(0, 255, 136, 0.3);
        `;

        explorerHeader.innerHTML = `
            <div class="explorer-title">
                <span>📁 Eksplorator Plików</span>
            </div>
            <button class="toggle-explorer-btn" style="
                background: none;
                border: none;
                font-size: 16px;
                color: #1a1a1a;
                cursor: pointer;
                padding: 4px;
                border-radius: 3px;
            " title="Zwiń/Rozwiń">◀</button>
        `;

        // Toolbar z przyciskami
        const explorerToolbar = document.createElement('div');
        explorerToolbar.className = 'explorer-toolbar';
        explorerToolbar.style.cssText = `
            background: rgba(0, 255, 136, 0.1);
            padding: 8px 12px;
            display: flex;
            gap: 8px;
            border-bottom: 1px solid rgba(0, 255, 136, 0.2);
        `;

        explorerToolbar.innerHTML = `
            <button class="toolbar-btn refresh-btn" title="Odśwież">🔄</button>
            <button class="toolbar-btn new-file-btn" title="Nowy plik">📄+</button>
            <button class="toolbar-btn new-folder-btn" title="Nowy folder">📁+</button>
        `;

        // Kontener na drzewo plików
        this.fileTreeContainer = document.createElement('div');
        this.fileTreeContainer.className = 'file-tree-container';
        this.fileTreeContainer.style.cssText = `
            flex: 1;
            overflow-y: auto;
            padding: 8px;
            color: #ffffff;
        `;

        // Dodaj komponenty do kontenera
        this.explorerContainer.appendChild(explorerHeader);
        this.explorerContainer.appendChild(explorerToolbar);
        this.explorerContainer.appendChild(this.fileTreeContainer);
        
        // Dodaj do body
        document.body.appendChild(this.explorerContainer);

        // Dodaj style dla przycisków toolbar
        const toolbarStyle = document.createElement('style');
        toolbarStyle.innerHTML = `
            .toolbar-btn {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(0, 255, 136, 0.3);
                color: #ffffff;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s ease;
            }
            
            .toolbar-btn:hover {
                background: rgba(0, 255, 136, 0.2);
                border-color: rgba(0, 255, 136, 0.6);
            }

            .file-item {
                padding: 4px 8px;
                margin: 2px 0;
                border-radius: 4px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                user-select: none;
                font-size: 13px;
                transition: background-color 0.2s ease;
            }

            .file-item:hover {
                background: rgba(0, 255, 136, 0.15);
            }

            .file-item.selected {
                background: rgba(0, 255, 136, 0.3);
                color: #ffffff;
            }

            .file-item .expand-icon {
                font-size: 10px;
                transition: transform 0.2s ease;
                width: 12px;
                text-align: center;
            }

            .file-item.expanded .expand-icon {
                transform: rotate(90deg);
            }

            .file-item .file-icon {
                font-size: 14px;
                width: 16px;
                text-align: center;
            }

            .file-item .file-name {
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .file-children {
                margin-left: 16px;
                border-left: 1px solid rgba(0, 255, 136, 0.2);
                padding-left: 8px;
            }

            .file-explorer-container.collapsed {
                width: 40px;
                min-width: 40px;
            }

            .file-explorer-container.collapsed .explorer-title,
            .file-explorer-container.collapsed .explorer-toolbar,
            .file-explorer-container.collapsed .file-tree-container {
                display: none !important;
            }
            
            .file-explorer-container.collapsed .toggle-explorer-btn {
                writing-mode: vertical-lr;
                text-orientation: mixed;
                padding: 8px 4px;
                margin: 10px auto;
                display: block;
            }
        `;
        document.head.appendChild(toolbarStyle);
    }

    setupEventListeners() {
        // Toggle eksploratora
        const toggleBtn = this.explorerContainer.querySelector('.toggle-explorer-btn');
        toggleBtn.addEventListener('click', () => {
            this.toggleExplorer();
        });

        // Odśwież pliki
        const refreshBtn = this.explorerContainer.querySelector('.refresh-btn');
        refreshBtn.addEventListener('click', () => {
            this.loadFiles();
        });

        // Nowy plik
        const newFileBtn = this.explorerContainer.querySelector('.new-file-btn');
        newFileBtn.addEventListener('click', () => {
            this.createNewFile();
        });

        // Nowy folder
        const newFolderBtn = this.explorerContainer.querySelector('.new-folder-btn');
        newFolderBtn.addEventListener('click', () => {
            this.createNewFolder();
        });

        // Nasłuchuj na kliknięcia w drzewie plików
        this.fileTreeContainer.addEventListener('click', (e) => {
            const fileItem = e.target.closest('.file-item');
            if (fileItem) {
                this.handleFileItemClick(fileItem, e);
            }
        });

        // Nasłuchuj odpowiedzi z backendu
        if (this.graphManager && this.graphManager.socket) {
            this.graphManager.socket.on('file_structure', (data) => {
                this.renderFileTree(data);
            });
            
            this.graphManager.socket.on('file_content', (data) => {
                this.displayFileContent(data);
            });
        }
    }

    async loadFiles() {
        try {
            // Wyślij zapytanie do backendu o listę plików
            if (this.graphManager && this.graphManager.socket && this.graphManager.socket.connected) {
                this.graphManager.socket.emit('get_file_structure', {
                    path: this.currentPath
                });
            } else {
                // Tymczasowo załaduj podstawową strukturę jeśli nie ma połączenia
                const mockFileStructure = await this.getMockFileStructure();
                this.renderFileTree(mockFileStructure);
            }

        } catch (error) {
            console.error('Błąd ładowania plików:', error);
            this.showError('Nie można załadować struktury plików');
        }
    }

    async getMockFileStructure() {
        // Tymczasowa struktura plików na podstawie tego co widzimy w projekcie
        return {
            name: 'LuxOS',
            type: 'folder',
            path: '.',
            children: [
                {
                    name: 'static',
                    type: 'folder',
                    path: './static',
                    children: [
                        { name: 'index.html', type: 'file', path: './static/index.html', icon: '🌐' },
                        { name: 'landing.html', type: 'file', path: './static/landing.html', icon: '🌐' },
                        { name: 'graph.js', type: 'file', path: './static/graph.js', icon: '📜' },
                        { name: 'chat-component.js', type: 'file', path: './static/chat-component.js', icon: '📜' },
                        { name: 'intention-component.js', type: 'file', path: './static/intention-component.js', icon: '📜' }
                    ]
                },
                { name: 'main.py', type: 'file', path: './main.py', icon: '🐍' },
                { name: 'lux_tools.py', type: 'file', path: './lux_tools.py', icon: '🐍' },
                { name: 'tool_parser.py', type: 'file', path: './tool_parser.py', icon: '🐍' },
                { name: 'test_parser.py', type: 'file', path: './test_parser.py', icon: '🐍' },
                { name: 'luxos.db', type: 'file', path: './luxos.db', icon: '🗄️' },
                { name: 'pyproject.toml', type: 'file', path: './pyproject.toml', icon: '⚙️' },
                { name: 'uv.lock', type: 'file', path: './uv.lock', icon: '🔒' },
                { name: '.gitignore', type: 'file', path: './.gitignore', icon: '🚫' },
                { name: '.replit', type: 'file', path: './.replit', icon: '⚙️' }
            ]
        };
    }

    renderFileTree(fileStructure, container = null) {
        if (!container) {
            this.fileTreeContainer.innerHTML = '';
            container = this.fileTreeContainer;
        }

        const items = Array.isArray(fileStructure) ? fileStructure : [fileStructure];

        items.forEach(item => {
            const fileElement = document.createElement('div');
            fileElement.className = 'file-item';
            fileElement.dataset.path = item.path;
            fileElement.dataset.type = item.type;

            const icon = this.getFileIcon(item);
            const expandIcon = item.type === 'folder' ? 
                (this.expandedFolders.has(item.path) ? '▼' : '▶') : '';

            fileElement.innerHTML = `
                ${expandIcon ? `<span class="expand-icon">${expandIcon}</span>` : '<span class="expand-icon"></span>'}
                <span class="file-icon">${icon}</span>
                <span class="file-name">${item.name}</span>
            `;

            if (this.expandedFolders.has(item.path)) {
                fileElement.classList.add('expanded');
            }

            container.appendChild(fileElement);

            // Dodaj children jeśli folder jest rozwinięty
            if (item.type === 'folder' && item.children && this.expandedFolders.has(item.path)) {
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'file-children';
                container.appendChild(childrenContainer);
                this.renderFileTree(item.children, childrenContainer);
            }
        });
    }

    getFileIcon(item) {
        if (item.icon) return item.icon;
        
        if (item.type === 'folder') return '📁';
        
        const extension = item.name.split('.').pop()?.toLowerCase();
        const iconMap = {
            'py': '🐍',
            'js': '📜',
            'html': '🌐',
            'css': '🎨',
            'json': '📋',
            'md': '📝',
            'txt': '📄',
            'db': '🗄️',
            'toml': '⚙️',
            'lock': '🔒',
            'gitignore': '🚫'
        };
        
        return iconMap[extension] || '📄';
    }

    handleFileItemClick(fileItem, event) {
        const path = fileItem.dataset.path;
        const type = fileItem.dataset.type;

        // Usuń poprzednie zaznaczenie
        this.fileTreeContainer.querySelectorAll('.file-item.selected').forEach(item => {
            item.classList.remove('selected');
        });

        // Zaznacz kliknięty element
        fileItem.classList.add('selected');

        if (type === 'folder') {
            // Toggle rozwinięcie folderu
            if (this.expandedFolders.has(path)) {
                this.expandedFolders.delete(path);
            } else {
                this.expandedFolders.add(path);
            }
            this.loadFiles(); // Przerenderuj drzewo
        } else {
            // Otwórz plik
            this.openFile(path);
        }
    }

    async openFile(filePath) {
        try {
            console.log('Otwieranie pliku:', filePath);
            
            // Wyślij żądanie do backendu o zawartość pliku
            if (this.graphManager && this.graphManager.socket) {
                this.graphManager.socket.emit('read_file', {
                    file_path: filePath
                });
            }

            // Tymczasowo pokaż powiadomienie
            this.showNotification(`Otwieranie: ${filePath}`);

        } catch (error) {
            console.error('Błąd otwierania pliku:', error);
            this.showError(`Nie można otworzyć pliku: ${filePath}`);
        }
    }

    createNewFile() {
        const fileName = prompt('Nazwa nowego pliku:');
        if (fileName) {
            console.log('Tworzenie nowego pliku:', fileName);
            this.showNotification(`Utworzono plik: ${fileName}`);
            // TODO: Implementacja tworzenia pliku przez backend
        }
    }

    createNewFolder() {
        const folderName = prompt('Nazwa nowego folderu:');
        if (folderName) {
            console.log('Tworzenie nowego folderu:', folderName);
            this.showNotification(`Utworzono folder: ${folderName}`);
            // TODO: Implementacja tworzenia folderu przez backend
        }
    }

    toggleExplorer() {
        this.isVisible = !this.isVisible;
        const toggleBtn = this.explorerContainer.querySelector('.toggle-explorer-btn');
        
        if (this.isVisible) {
            this.explorerContainer.classList.remove('collapsed');
            toggleBtn.innerHTML = '◀';
            toggleBtn.title = 'Zwiń';
        } else {
            this.explorerContainer.classList.add('collapsed');
            toggleBtn.innerHTML = '▶';
            toggleBtn.title = 'Rozwiń';
        }

        // Przesuń graf w prawo jeśli eksplorator jest widoczny
        this.adjustGraphPosition();
    }

    adjustGraphPosition() {
        const graphElement = document.getElementById('graph');
        if (graphElement) {
            if (this.isVisible) {
                graphElement.classList.remove('explorer-collapsed');
                graphElement.style.marginLeft = '280px';
                graphElement.style.width = 'calc(100% - 280px)';
            } else {
                graphElement.classList.add('explorer-collapsed');
                graphElement.style.marginLeft = '40px';
                graphElement.style.width = 'calc(100% - 40px)';
            }
        }

        // Poinformuj wszechświat o zmianie rozmiaru
        if (window.luxOSUniverse) {
            // Daj chwilę na zakończenie animacji CSS
            setTimeout(() => {
                if (window.luxOSUniverse.resizeGraph) {
                    window.luxOSUniverse.resizeGraph();
                }
                // Restart symulacji dla lepszego układu
                if (window.luxOSUniverse.simulation) {
                    window.luxOSUniverse.simulation.alpha(0.3).restart();
                }
            }, 300);
        }
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            left: 300px;
            background: rgba(0, 255, 136, 0.9);
            color: #1a1a1a;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 3000;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0, 255, 136, 0.3);
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    showError(message) {
        const error = document.createElement('div');
        error.style.cssText = `
            position: fixed;
            top: 100px;
            left: 300px;
            background: rgba(255, 68, 68, 0.9);
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 3000;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(255, 68, 68, 0.3);
        `;
        error.textContent = message;
        
        document.body.appendChild(error);
        
        setTimeout(() => {
            if (error.parentNode) {
                error.parentNode.removeChild(error);
            }
        }, 5000);
    }

    displayFileContent(fileData) {
        // Utwórz okno z zawartością pliku
        const fileWindow = document.createElement('div');
        fileWindow.className = 'file-content-window';
        fileWindow.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80%;
            height: 80%;
            max-width: 1000px;
            max-height: 800px;
            background: rgba(26, 26, 26, 0.98);
            border: 2px solid #00ff88;
            border-radius: 10px;
            z-index: 2500;
            display: flex;
            flex-direction: column;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 40px rgba(0, 255, 136, 0.3);
        `;

        fileWindow.innerHTML = `
            <div style="
                background: linear-gradient(45deg, #00ff88, #00cc66);
                color: #1a1a1a;
                padding: 12px 20px;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-radius: 8px 8px 0 0;
            ">
                <span>📄 ${fileData.file_path} (${fileData.size} bytes)</span>
                <button onclick="this.closest('.file-content-window').remove()" style="
                    background: none;
                    border: none;
                    font-size: 18px;
                    color: #1a1a1a;
                    cursor: pointer;
                    padding: 4px;
                ">✕</button>
            </div>
            <div style="
                flex: 1;
                padding: 20px;
                overflow: auto;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.4;
                background: rgba(0, 0, 0, 0.3);
                white-space: pre-wrap;
                word-wrap: break-word;
            ">${this.escapeHtml(fileData.content)}</div>
        `;

        document.body.appendChild(fileWindow);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export dla użycia w innych modulach
window.FileExplorer = FileExplorer;
