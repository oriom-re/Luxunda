
class SimilarityComponent {
    constructor() {
        this.threshold = 0.7;
        this.init();
    }

    init() {
        this.createSimilarityPanel();
        this.attachEventListeners();
    }

    createSimilarityPanel() {
        const similarityPanel = document.createElement('div');
        similarityPanel.id = 'similarity-panel';
        similarityPanel.style.cssText = `
            position: fixed;
            top: 120px;
            right: 20px;
            width: 300px;
            background: rgba(20, 25, 35, 0.95);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 15px;
            color: #00ff88;
            font-family: 'Courier New', monospace;
            z-index: 1000;
            max-height: 400px;
            overflow-y: auto;
        `;

        similarityPanel.innerHTML = `
            <h3 style="margin: 0 0 15px 0; color: #00ff88;">🔍 Similarity Analyzer</h3>
            
            <div style="margin-bottom: 15px;">
                <label>Próg podobieństwa: <span id="threshold-value">${this.threshold}</span></label>
                <input type="range" id="similarity-threshold" 
                       min="0.1" max="1.0" step="0.1" value="${this.threshold}"
                       style="width: 100%; margin-top: 5px;">
            </div>
            
            <button id="analyze-similarities" style="
                background: #00ff88;
                color: #0a0f1a;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
                margin-bottom: 15px;
                font-weight: bold;
            ">Analizuj Podobieństwa</button>
            
            <div id="similarity-results" style="
                max-height: 200px;
                overflow-y: auto;
                border-top: 1px solid #00ff88;
                padding-top: 10px;
            "></div>
        `;

        document.body.appendChild(similarityPanel);
    }

    attachEventListeners() {
        const thresholdSlider = document.getElementById('similarity-threshold');
        const thresholdValue = document.getElementById('threshold-value');
        const analyzeBtn = document.getElementById('analyze-similarities');

        thresholdSlider.addEventListener('input', (e) => {
            this.threshold = parseFloat(e.target.value);
            thresholdValue.textContent = this.threshold;
        });

        analyzeBtn.addEventListener('click', () => {
            this.analyzeSimilarities();
        });
    }

    async analyzeSimilarities() {
        const resultsDiv = document.getElementById('similarity-results');
        resultsDiv.innerHTML = '<div style="color: #ffaa00;">🔄 Analizowanie...</div>';

        try {
            // Pobierz hash wiadomości (przykład - można to dostosować)
            const messageSoulHash = await this.getMessageSoulHash();
            
            if (!messageSoulHash) {
                resultsDiv.innerHTML = '<div style="color: #ff4444;">❌ Nie znaleziono wiadomości do analizy</div>';
                return;
            }

            const response = await fetch('/api/compare_messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    soul_hash: messageSoulHash,
                    threshold: this.threshold
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.displayResults(data.result);
            } else {
                resultsDiv.innerHTML = `<div style="color: #ff4444;">❌ ${data.error}</div>`;
            }
        } catch (error) {
            console.error('Error analyzing similarities:', error);
            resultsDiv.innerHTML = '<div style="color: #ff4444;">❌ Błąd analizy</div>';
        }
    }

    displayResults(result) {
        const resultsDiv = document.getElementById('similarity-results');
        
        if (result.created_relations === 0) {
            resultsDiv.innerHTML = `
                <div style="color: #ffaa00;">
                    📊 ${result.message}<br>
                    🔍 Brak relacji spełniających próg ${result.similarity_threshold}
                </div>
            `;
            return;
        }

        let html = `
            <div style="color: #00ff88; margin-bottom: 10px;">
                ✅ ${result.message}<br>
                🔗 Utworzono relacji: ${result.created_relations}
            </div>
        `;

        if (result.relations_details && result.relations_details.length > 0) {
            html += '<div style="font-size: 0.9em;">';
            result.relations_details.forEach((relation, index) => {
                html += `
                    <div style="margin: 5px 0; padding: 5px; border-left: 2px solid #00ff88; padding-left: 8px;">
                        <strong>Relacja ${index + 1}:</strong><br>
                        Podobieństwo: ${(relation.similarity_score * 100).toFixed(1)}%<br>
                        <small>ID: ${relation.relation_id.substring(0, 8)}...</small>
                    </div>
                `;
            });
            html += '</div>';
        }

        resultsDiv.innerHTML = html;
    }

    async getMessageSoulHash() {
        // Pobierz hash soul dla wiadomości - można to dostosować do konkretnej implementacji
        try {
            const response = await fetch('/api/graph_data');
            const data = await response.json();
            
            // Znajdź soul wiadomości
            const messageSoul = data.beings.find(being => 
                being._soul && being._soul.alias === 'message'
            );
            
            return messageSoul ? messageSoul.soul_uid : null;
        } catch (error) {
            console.error('Error getting message soul hash:', error);
            return null;
        }
    }
}

// Inicjalizuj komponent po załadowaniu strony
document.addEventListener('DOMContentLoaded', () => {
    window.similarityComponent = new SimilarityComponent();
});
