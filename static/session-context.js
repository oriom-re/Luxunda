
/**
 * Session Context Manager - Frontend dla Session Assistant
 */

class SessionContext {
    constructor() {
        this.sessionId = null;
        this.websocket = null;
        this.userFingerprint = null;
        this.activeProjects = new Set();
        this.recentActivity = [];
        this.isConnected = false;
    }

    async initializeSession() {
        // Zbierz informacje o użytkowniku
        const userInfo = {
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            timestamp: new Date().toISOString()
        };

        // Połącz z WebSocket
        this.websocket = new WebSocket(`ws://${window.location.host}/ws`);
        
        this.websocket.onopen = () => {
            console.log('🔌 WebSocket connected');
            
            // Wyślij inicjalizację sesji
            this.websocket.send(JSON.stringify({
                type: 'init_session',
                user_info: userInfo
            }));
        };

        this.websocket.onmessage = (event) => {
            this.handleMessage(JSON.parse(event.data));
        };

        this.websocket.onclose = () => {
            console.log('❌ WebSocket disconnected');
            this.isConnected = false;
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'system':
                this.handleSystemMessage(data);
                break;
            case 'lux_response':
                this.handleLuxResponse(data);
                break;
            case 'action_tracked':
                this.handleActionTracked(data);
                break;
            case 'thinking':
                this.showThinking(data.message);
                break;
        }
    }

    handleSystemMessage(data) {
        this.isConnected = true;
        if (data.session_context) {
            this.updateSessionContext(data.session_context);
        }
        this.displayMessage('system', data.message);
    }

    handleLuxResponse(data) {
        // Aktualizuj kontekst sesji
        if (data.session_context) {
            this.updateSessionContext(data.session_context);
        }
        
        if (data.active_projects) {
            this.activeProjects = new Set(data.active_projects);
            this.updateProjectTags();
        }

        if (data.recent_activity) {
            this.updateActivityDisplay(data.recent_activity);
        }

        this.displayMessage('assistant', data.message);
        this.hideThinking();
    }

    updateSessionContext(context) {
        // Aktualizuj wyświetlanie kontekstu
        const contextElement = document.getElementById('session-context');
        if (contextElement) {
            contextElement.innerHTML = `
                <div class="context-info">
                    <h4>📊 Kontekst Sesji</h4>
                    <p>⏱️ Czas: ${context.session_info?.duration_minutes || 0} min</p>
                    <p>🎯 Działania: ${context.session_info?.activity_count || 0}</p>
                    <p>⚡ Aktywne eventy: ${context.active_events_count || 0}</p>
                </div>
            `;
        }
    }

    updateProjectTags() {
        const tagsElement = document.getElementById('project-tags');
        if (tagsElement && this.activeProjects.size > 0) {
            tagsElement.innerHTML = `
                <div class="project-tags">
                    <h4>🏷️ Aktywne Projekty</h4>
                    ${Array.from(this.activeProjects).map(tag => 
                        `<span class="tag tag-${tag}">${tag}</span>`
                    ).join('')}
                </div>
            `;
        }
    }

    updateActivityDisplay(activity) {
        const activityElement = document.getElementById('recent-activity');
        if (activityElement) {
            activityElement.innerHTML = `
                <div class="recent-activity">
                    <h4>📋 Ostatnie Działania</h4>
                    <pre>${activity}</pre>
                </div>
            `;
        }
    }

    sendMessage(message) {
        if (!this.isConnected) {
            console.log('❌ Brak połączenia z sesją');
            return;
        }

        this.websocket.send(JSON.stringify({
            type: 'user_message',
            message: message,
            timestamp: new Date().toISOString()
        }));

        this.displayMessage('user', message);
        this.showThinking('🤔 Lux analizuje...');
    }

    trackUserAction(actionType, actionData = {}) {
        if (!this.isConnected) return;

        const action = {
            type: actionType,
            data: actionData,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };

        this.websocket.send(JSON.stringify({
            type: 'user_action',
            action: action
        }));

        console.log('📊 Tracked action:', actionType);
    }

    displayMessage(sender, message) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${sender}`;
        
        const timestamp = new Date().toLocaleTimeString();
        const senderIcon = {
            'user': '👤',
            'assistant': '🤖',
            'system': '🌟'
        };

        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="sender">${senderIcon[sender]} ${sender}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
            <div class="message-content">${message}</div>
        `;

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    showThinking(message = '🤔 Myślę...') {
        const thinkingElement = document.getElementById('thinking-indicator');
        if (thinkingElement) {
            thinkingElement.textContent = message;
            thinkingElement.style.display = 'block';
        }
    }

    hideThinking() {
        const thinkingElement = document.getElementById('thinking-indicator');
        if (thinkingElement) {
            thinkingElement.style.display = 'none';
        }
    }

    handleActionTracked(data) {
        console.log('✅ Action tracked:', data.message);
        
        // Pokaż subtelną notyfikację
        const notification = document.createElement('div');
        notification.className = 'action-notification';
        notification.textContent = data.message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Auto-tracking user actions
class ActionTracker {
    constructor(sessionContext) {
        this.session = sessionContext;
        this.setupTracking();
    }

    setupTracking() {
        // Track page changes
        let lastUrl = location.href;
        new MutationObserver(() => {
            const url = location.href;
            if (url !== lastUrl) {
                lastUrl = url;
                this.session.trackUserAction('page_change', { url });
            }
        }).observe(document, { subtree: true, childList: true });

        // Track form submissions
        document.addEventListener('submit', (e) => {
            this.session.trackUserAction('form_submit', {
                form_id: e.target.id,
                form_action: e.target.action
            });
        });

        // Track button clicks on important elements
        document.addEventListener('click', (e) => {
            if (e.target.matches('button, .btn, [role="button"]')) {
                this.session.trackUserAction('button_click', {
                    button_text: e.target.textContent?.trim(),
                    button_id: e.target.id,
                    button_class: e.target.className
                });
            }
        });

        // Track file uploads
        document.addEventListener('change', (e) => {
            if (e.target.type === 'file' && e.target.files.length > 0) {
                this.session.trackUserAction('file_upload', {
                    file_count: e.target.files.length,
                    file_types: Array.from(e.target.files).map(f => f.type)
                });
            }
        });
    }
}

// Global session instance
window.luxSession = new SessionContext();
window.actionTracker = new ActionTracker(window.luxSession);

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.luxSession.initializeSession();
});
