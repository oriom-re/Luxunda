
class UserIdentificationSystem {
    constructor() {
        this.userFingerprint = null;
        this.userId = null;
        this.conversationHistory = [];
        this.identificationData = {};
        this.init();
    }

    async init() {
        await this.generateFingerprint();
        await this.loadUserData();
    }

    async generateFingerprint() {
        // Zbieranie danych o przeglądarce do utworzenia fingerprint
        const fp = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            languages: navigator.languages?.join(',') || '',
            platform: navigator.platform,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screenResolution: `${screen.width}x${screen.height}`,
            colorDepth: screen.colorDepth,
            pixelRatio: window.devicePixelRatio,
            hardwareConcurrency: navigator.hardwareConcurrency,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack,
            webgl: this.getWebGLInfo(),
            canvas: this.getCanvasFingerprint(),
            fonts: await this.detectFonts(),
            localStorage: this.testLocalStorage(),
            sessionStorage: this.testSessionStorage()
        };

        // Tworzenie hash z fingerprint
        this.userFingerprint = await this.hashFingerprint(fp);
        
        // Zapisanie fingerprint w localStorage
        localStorage.setItem('lux_fingerprint', this.userFingerprint);
        
        console.log('🔍 Generated user fingerprint:', this.userFingerprint.substring(0, 12) + '...');
        return this.userFingerprint;
    }

    getWebGLInfo() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) return 'not-supported';
            
            return {
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER),
                version: gl.getParameter(gl.VERSION)
            };
        } catch (e) {
            return 'error';
        }
    }

    getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillText('LuxOS Fingerprint Test 🔍', 2, 2);
            return canvas.toDataURL().substring(0, 50);
        } catch (e) {
            return 'error';
        }
    }

    async detectFonts() {
        const testString = 'mmmmmmmmmmlli';
        const testSize = '72px';
        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const fontList = [
            'Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana',
            'Georgia', 'Palatino', 'Garamond', 'Bookman', 'Tahoma',
            'Comic Sans MS', 'Impact', 'Arial Black', 'Trebuchet MS'
        ];

        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        const baselines = {};
        for (const baseFont of baseFonts) {
            context.font = testSize + ' ' + baseFont;
            baselines[baseFont] = context.measureText(testString).width;
        }

        const detectedFonts = [];
        for (const font of fontList) {
            for (const baseFont of baseFonts) {
                context.font = testSize + ' ' + font + ', ' + baseFont;
                const width = context.measureText(testString).width;
                if (width !== baselines[baseFont]) {
                    detectedFonts.push(font);
                    break;
                }
            }
        }

        return detectedFonts.join(',');
    }

    testLocalStorage() {
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
            return true;
        } catch (e) {
            return false;
        }
    }

    testSessionStorage() {
        try {
            sessionStorage.setItem('test', 'test');
            sessionStorage.removeItem('test');
            return true;
        } catch (e) {
            return false;
        }
    }

    async hashFingerprint(data) {
        const str = JSON.stringify(data);
        const encoder = new TextEncoder();
        const dataBytes = encoder.encode(str);
        const hashBuffer = await crypto.subtle.digest('SHA-256', dataBytes);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    async loadUserData() {
        try {
            const response = await fetch('/api/user/identify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    fingerprint: this.userFingerprint,
                    timestamp: new Date().toISOString()
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.userId = data.user_id;
                this.identificationData = data.identification_data || {};
                this.conversationHistory = data.conversation_history || [];
                
                console.log('👤 User identified:', {
                    userId: this.userId,
                    previousMessages: this.conversationHistory.length,
                    knownNames: this.identificationData.names || []
                });

                // Wyświetl powitanie jeśli użytkownik jest rozpoznany
                if (data.returning_user && this.identificationData.names?.length > 0) {
                    this.showWelcomeMessage();
                }
            }
        } catch (error) {
            console.error('❌ Error loading user data:', error);
        }
    }

    async analyzeMessage(message) {
        // Analiza wiadomości pod kątem identyfikacji użytkownika
        const analysis = {
            names_mentioned: this.extractNames(message),
            self_introduction: this.detectSelfIntroduction(message),
            returning_user_indicators: this.detectReturningUserIndicators(message),
            conversation_style: this.analyzeConversationStyle(message)
        };

        // Wysłanie analizy do serwera
        try {
            const response = await fetch('/api/user/analyze_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    fingerprint: this.userFingerprint,
                    message: message,
                    analysis: analysis,
                    timestamp: new Date().toISOString()
                })
            });

            const data = await response.json();
            
            if (data.identity_updated) {
                this.identificationData = data.identification_data;
                console.log('🔄 User identity updated:', this.identificationData);
            }

            return data;
        } catch (error) {
            console.error('❌ Error analyzing message:', error);
            return null;
        }
    }

    extractNames(message) {
        // Proste wykrywanie imion we wzorcach przedstawiania się
        const patterns = [
            /nazywam się\s+(\w+)/i,
            /jestem\s+(\w+)/i,
            /to\s+(\w+)/i,
            /mam na imię\s+(\w+)/i,
            /to ja,?\s+(\w+)/i,
            /^(\w+)\s+(tutaj|tu)/i,
            /cześć,?\s+to\s+(\w+)/i
        ];

        const names = [];
        for (const pattern of patterns) {
            const match = message.match(pattern);
            if (match && match[1]) {
                names.push(match[1].toLowerCase());
            }
        }

        return names;
    }

    detectSelfIntroduction(message) {
        const introPatterns = [
            /nazywam się/i,
            /jestem/i,
            /mam na imię/i,
            /to ja/i,
            /przedstawiam się/i,
            /cześć.*to/i
        ];

        return introPatterns.some(pattern => pattern.test(message));
    }

    detectReturningUserIndicators(message) {
        const returningPatterns = [
            /wracam/i,
            /jestem z powrotem/i,
            /pamiętasz mnie/i,
            /rozmawialiśmy już/i,
            /kontynuujmy/i,
            /poprzednio/i,
            /wcześniej/i
        ];

        return returningPatterns.some(pattern => pattern.test(message));
    }

    analyzeConversationStyle(message) {
        return {
            length: message.length,
            question_marks: (message.match(/\?/g) || []).length,
            exclamation_marks: (message.match(/!/g) || []).length,
            informal_indicators: /\b(siema|czołem|hej|cześć|witam)\b/i.test(message),
            formal_indicators: /\b(dzień dobry|miło mi|szanowny|proszę)\b/i.test(message),
            emoji_count: (message.match(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu) || []).length
        };
    }

    showWelcomeMessage() {
        const names = this.identificationData.names || [];
        const lastSeen = this.identificationData.last_seen;
        
        let welcomeText = "Witaj ponownie! ";
        
        if (names.length > 0) {
            welcomeText += `Rozpoznaję cię jako ${names[0]}. `;
        }
        
        if (lastSeen) {
            const lastSeenDate = new Date(lastSeen);
            const timeDiff = Date.now() - lastSeenDate.getTime();
            const daysDiff = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
            
            if (daysDiff === 0) {
                welcomeText += "Widzieliśmy się dzisiaj. ";
            } else if (daysDiff === 1) {
                welcomeText += "Widzieliśmy się wczoraj. ";
            } else {
                welcomeText += `Widzieliśmy się ${daysDiff} dni temu. `;
            }
        }
        
        if (this.conversationHistory.length > 0) {
            welcomeText += `Mamy już ${this.conversationHistory.length} wiadomości w naszej historii. Chcesz kontynuować poprzednią rozmowę?`;
        }

        // Wyświetl powitanie w interfejsie
        this.displaySystemMessage(welcomeText, 'welcome');
    }

    displaySystemMessage(message, type = 'info') {
        const chatContainer = document.getElementById('chat-messages') || document.querySelector('.chat-messages');
        if (!chatContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `system-message ${type}`;
        messageElement.style.cssText = `
            background: rgba(0, 255, 136, 0.1);
            border-left: 3px solid #00ff88;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 5px;
            font-style: italic;
            color: #00ff88;
        `;
        messageElement.textContent = message;

        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    getUserInfo() {
        return {
            userId: this.userId,
            fingerprint: this.userFingerprint,
            identificationData: this.identificationData,
            conversationHistory: this.conversationHistory
        };
    }
}

// Globalna instancja systemu identyfikacji
window.userIdentification = new UserIdentificationSystem();
