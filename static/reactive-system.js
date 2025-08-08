
// ===== LUX REACTIVE SYSTEM - REGIONAL RENDERING =====

class LuxReactiveSystem {
    constructor() {
        this.state = new Map();
        this.observers = new Map();
        this.memoCache = new Map();
        this.renderQueue = new Set();
        this.isUpdating = false;
        
        console.log('🔄 LuxReactiveSystem initialized');
    }

    // Tworzenie reaktywnego stanu
    createState(key, initialValue) {
        this.state.set(key, initialValue);
        this.observers.set(key, new Set());
        return initialValue;
    }

    // Pobieranie stanu
    getState(key) {
        return this.state.get(key);
    }

    // Ustawianie stanu z powiadomieniami
    setState(key, newValue, force = false) {
        const oldValue = this.state.get(key);
        
        // Sprawdź czy wartość się rzeczywiście zmieniła
        if (!force && this.deepEqual(oldValue, newValue)) {
            return;
        }

        this.state.set(key, newValue);
        this.notifyObservers(key, newValue, oldValue);
    }

    // Subskrypcja na zmiany stanu (like useEffect)
    subscribe(stateKeys, callback, deps = []) {
        const observerId = this.generateId();
        const memoKey = this.generateMemoKey(callback, deps);
        
        // Sprawdź cache memo
        if (this.memoCache.has(memoKey)) {
            return this.memoCache.get(memoKey);
        }

        const observer = {
            id: observerId,
            callback,
            deps,
            lastRender: Date.now(),
            element: null
        };

        // Rejestruj observer dla każdego klucza stanu
        if (Array.isArray(stateKeys)) {
            stateKeys.forEach(key => {
                if (!this.observers.has(key)) {
                    this.observers.set(key, new Set());
                }
                this.observers.get(key).add(observer);
            });
        } else {
            if (!this.observers.has(stateKeys)) {
                this.observers.set(stateKeys, new Set());
            }
            this.observers.get(stateKeys).add(observer);
        }

        // Zapisz w cache memo
        this.memoCache.set(memoKey, observerId);
        
        return observerId;
    }

    // Powiadom obserwatorów o zmianie
    notifyObservers(key, newValue, oldValue) {
        const observers = this.observers.get(key);
        if (!observers) return;

        observers.forEach(observer => {
            this.renderQueue.add(observer);
        });

        this.scheduleRender();
    }

    // Harmonogramuj renderowanie (batch updates)
    scheduleRender() {
        if (this.isUpdating) return;

        this.isUpdating = true;
        requestAnimationFrame(() => {
            this.processRenderQueue();
            this.isUpdating = false;
        });
    }

    // Przetwórz kolejkę renderowania
    processRenderQueue() {
        const sortedObservers = Array.from(this.renderQueue).sort((a, b) => 
            a.lastRender - b.lastRender
        );

        sortedObservers.forEach(observer => {
            try {
                const result = observer.callback();
                observer.lastRender = Date.now();
                
                // Jeśli callback zwraca element DOM, zaktualizuj go
                if (result instanceof HTMLElement) {
                    observer.element = result;
                }
            } catch (error) {
                console.error('🔥 Observer callback error:', error);
            }
        });

        this.renderQueue.clear();
    }

    // Regional component - renderuje tylko jeśli się zmienił
    createRegionalComponent(containerId, stateKeys, renderFunction, dependencies = []) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`❌ Container ${containerId} not found`);
            return;
        }

        let lastHash = null;
        
        const component = {
            render: () => {
                // Zbierz dane dla komponentu
                const data = Array.isArray(stateKeys) 
                    ? stateKeys.map(key => this.getState(key))
                    : [this.getState(stateKeys)];
                
                // Stwórz hash z danych i dependencies
                const currentHash = this.hashData([...data, ...dependencies]);
                
                // Renderuj tylko jeśli hash się zmienił
                if (lastHash !== currentHash) {
                    console.log(`🔄 Re-rendering ${containerId}`);
                    
                    const newContent = renderFunction(data);
                    
                    if (typeof newContent === 'string') {
                        container.innerHTML = newContent;
                    } else if (newContent instanceof HTMLElement) {
                        container.innerHTML = '';
                        container.appendChild(newContent);
                    }
                    
                    lastHash = currentHash;
                    return container;
                }
                
                return null; // Nie renderowano
            }
        };

        // Zarejestruj komponent jako observer
        this.subscribe(stateKeys, component.render, dependencies);
        
        // Początkowe renderowanie
        component.render();
        
        return component;
    }

    // Fragment component - renderuje tylko wybrany fragment
    createFragment(parentId, fragmentId, stateKeys, renderFunction) {
        const parent = document.getElementById(parentId);
        if (!parent) {
            console.error(`❌ Parent ${parentId} not found`);
            return;
        }

        let fragment = document.getElementById(fragmentId);
        if (!fragment) {
            fragment = document.createElement('div');
            fragment.id = fragmentId;
            parent.appendChild(fragment);
        }

        return this.createRegionalComponent(fragmentId, stateKeys, renderFunction);
    }

    // Utilities
    deepEqual(a, b) {
        if (a === b) return true;
        if (a instanceof Date && b instanceof Date) return a.getTime() === b.getTime();
        if (!a || !b || (typeof a !== "object" && typeof b !== "object")) return a === b;
        if (a === null || a === undefined || b === null || b === undefined) return false;
        if (a.prototype !== b.prototype) return false;
        
        let keys = Object.keys(a);
        if (keys.length !== Object.keys(b).length) return false;
        
        return keys.every(k => this.deepEqual(a[k], b[k]));
    }

    hashData(data) {
        return JSON.stringify(data).split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
    }

    generateMemoKey(callback, deps) {
        return `${callback.toString()}_${JSON.stringify(deps)}`;
    }

    generateId() {
        return 'observer_' + Math.random().toString(36).substr(2, 9);
    }

    // Czyszczenie
    cleanup(observerId) {
        this.observers.forEach(observerSet => {
            observerSet.forEach(observer => {
                if (observer.id === observerId) {
                    observerSet.delete(observer);
                }
            });
        });
    }
}

// Global instance
window.luxReactive = new LuxReactiveSystem();

console.log('✅ LuxReactiveSystem loaded globally');
