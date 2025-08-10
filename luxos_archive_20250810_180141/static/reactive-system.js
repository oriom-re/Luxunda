
// ===== LUX REACTIVE SYSTEM CORE =====

class LuxReactiveSystem {
    constructor() {
        this.observers = new Map();
        this.state = new Proxy({}, {
            set: (target, property, value) => {
                const oldValue = target[property];
                target[property] = value;
                this.notifyObservers(property, value, oldValue);
                return true;
            }
        });
        
        console.log('🔄 LuxReactiveSystem initialized');
    }

    observe(property, callback) {
        if (!this.observers.has(property)) {
            this.observers.set(property, new Set());
        }
        this.observers.get(property).add(callback);
        
        // Return unsubscribe function
        return () => {
            this.observers.get(property)?.delete(callback);
        };
    }

    notifyObservers(property, newValue, oldValue) {
        const callbacks = this.observers.get(property);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(newValue, oldValue, property);
                } catch (error) {
                    console.error('❌ Observer callback error:', error);
                }
            });
        }
    }

    setState(updates) {
        Object.assign(this.state, updates);
    }

    getState() {
        return { ...this.state };
    }
}

// Global reactive system
window.luxReactiveSystem = new LuxReactiveSystem();
console.log('✅ LuxReactiveSystem loaded globally');
