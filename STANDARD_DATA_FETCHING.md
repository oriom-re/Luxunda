
# Standardyzacja Pobierania Danych - LuxDB

## Schemat Pobierania Węzłów z Backendu

### 1. Struktura Odpowiedzi API

Wszystkie endpointy zwracające dane węzłów używają jednolitego formatu:

```json
{
    "success": true,
    "data": {
        "souls": [],
        "beings": [],
        "relations": []
    },
    "stats": {
        "souls_count": 0,
        "beings_count": 0,
        "relations_count": 0
    },
    "timestamp": "2025-01-01T00:00:00.000Z"
}
```

### 2. Format Węzłów

#### Soul (Dusza/Genotyp)
```json
{
    "id": "soul_hash",
    "type": "soul",
    "soul_hash": "abc123...",
    "global_ulid": "01H...",
    "alias": "sample_entity",
    "genotype": {...},
    "created_at": "2025-01-01T00:00:00.000Z",
    "table_type": "souls"
}
```

#### Being (Byt)
```json
{
    "id": "ulid",
    "type": "being", 
    "ulid": "01H...",
    "global_ulid": "01H...",
    "soul_hash": "abc123...",
    "alias": "Entity_1",
    "genotype": {...},
    "created_at": "2025-01-01T00:00:00.000Z",
    "table_type": "beings"
}
```

#### Relation (Relacja)
```json
{
    "id": "ulid",
    "type": "relation",
    "ulid": "01H...",
    "global_ulid": "01H...", 
    "soul_hash": "abc123...",
    "source_ulid": "01H...",
    "target_ulid": "01H...",
    "attributes": {...},
    "created_at": "2025-01-01T00:00:00.000Z",
    "table_type": "relations"
}
```

### 3. Endpointy API

#### GET /api/graph/data
Pobiera wszystkie węzły dla grafu:
```python
@app.get("/api/graph/data")
async def get_graph_data():
    return {
        "success": True,
        "data": {
            "souls": [soul.to_dict() for soul in souls],
            "beings": [being.to_dict() for being in beings], 
            "relations": [relation.to_dict() for relation in relations]
        }
    }
```

#### GET /api/souls
Pobiera tylko dusze:
```python
@app.get("/api/souls")
async def get_souls():
    return {
        "success": True,
        "data": {"souls": [soul.to_dict() for soul in souls]}
    }
```

### 4. Przetwarzanie w JavaScript

```javascript
// Standardowa funkcja pobierania danych
async function fetchGraphData() {
    try {
        const response = await fetch('/api/graph/data');
        const result = await response.json();
        
        if (!result.success) {
            throw new Error('Failed to fetch data');
        }
        
        return {
            souls: result.data.souls || [],
            beings: result.data.beings || [],
            relations: result.data.relations || []
        };
    } catch (error) {
        console.error('Error fetching graph data:', error);
        return { souls: [], beings: [], relations: [] };
    }
}

// Konwersja na węzły D3.js
function convertToNodes(data) {
    const nodes = [];
    
    // Souls
    data.souls.forEach(soul => {
        nodes.push({
            id: soul.soul_hash,
            type: 'soul',
            label: soul.alias || 'Soul',
            group: 'souls',
            ...soul
        });
    });
    
    // Beings  
    data.beings.forEach(being => {
        nodes.push({
            id: being.ulid,
            type: 'being',
            label: being.alias || `Being_${being.ulid.slice(0,8)}`,
            group: 'beings', 
            ...being
        });
    });
    
    // Relations
    data.relations.forEach(relation => {
        nodes.push({
            id: relation.ulid,
            type: 'relation',
            label: `Relation_${relation.ulid.slice(0,8)}`,
            group: 'relations',
            ...relation
        });
    });
    
    return nodes;
}
```

### 5. Zasady Implementacji

1. **Zawsze używaj `to_dict()`** - każda klasa musi mieć metodę `to_dict()` zwracającą standardowy format
2. **Pole `table_type`** - każdy węzeł musi mieć pole określające źródło (`souls`, `beings`, `relations`)
3. **Unikalność ID** - każdy węzeł ma unikalne `id` (`soul_hash` dla souls, `ulid` dla pozostałych)
4. **Typ węzła** - pole `type` określa rodzaj węzła (`soul`, `being`, `relation`)
5. **Error handling** - zawsze obsługuj błędy w fetchingu danych

### 6. Migracja Istniejącego Kodu

1. Upewnij się że wszystkie klasy mają metodę `to_dict()` jako metodę instancyjną (nie statyczną)
2. Dodaj pole `table_type` do wszystkich zwracanych objektów
3. Używaj standardowego formatu odpowiedzi API
4. Aktualizuj frontend aby używał nowego schematu

### 7. Przykład Pełnej Implementacji

```python
# Backend - demo_landing.py
@app.get("/api/graph/data")
async def get_graph_data():
    try:
        souls = await Soul.load_all()
        beings = await Being.load_all() 
        relations = await Relation.load_all()
        
        souls_data = []
        for soul in souls:
            soul_dict = soul.to_dict()
            soul_dict['table_type'] = 'souls'
            soul_dict['type'] = 'soul'
            soul_dict['id'] = soul.soul_hash
            souls_data.append(soul_dict)
            
        # Similar for beings and relations...
        
        return {
            "success": True,
            "data": {
                "souls": souls_data,
                "beings": beings_data, 
                "relations": relations_data
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

Ten standard zapewnia spójność i łatwość utrzymania kodu oraz rozszerzania funkcjonalności.
