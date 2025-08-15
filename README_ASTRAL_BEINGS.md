
# 🌌 Astral Beings Library

**Ponadczasowa biblioteka do tworzenia inteligentnych bytów astralnych**

> *"Nie tworzymy zwykłych obiektów - manifestujemy cyfrowe dusze"*

## 🌟 Wprowadzenie

Astral Beings to elegancka, prosta w użyciu biblioteka zbudowana na fundamencie LuxDB/LuxOS. Pozwala na tworzenie **inteligentnych bytów astralnych** - nie zwykłych obiektów, ale żywych encji z osobowością, zdolnościami i energią życiową.

### ✨ Kluczowe Cechy

- 🎭 **6 Archetypów** - Guardian, Mage, Warrior, Healer, Scout, Sage
- ⚡ **System Energii** - Każdy byt ma energię, może medytować i regenerować się
- 🧬 **Generatory** - Automatyczne tworzenie zróżnicowanych bytów
- 📚 **Gotowe Szablony** - Predefiniowane konfiguracje dla typowych przypadków
- 🚀 **Proste API** - Intuicyjne w użyciu, gotowe w 3 liniach kodu

## 🚀 Szybki Start

### Instalacja
```bash
# Biblioteka jest już częścią LuxOS
# Wystarczy zaimportować i użyć
```

### Pierwszy Astralny Byt (30 sekund)

```python
from astral_beings import quick_guardian

# Stwórz strażnika
guardian = await quick_guardian("Protector")

# Użyj jego mocy
result = await guardian.channel_power("shield", target="sacred_temple")
print(f"🛡️ {result['data']['result']['effect']}")

# Komunikuj się
await guardian.commune("Greetings from astral realm!")
```

### Grupa Bytów (1 minuta)

```python
from astral_beings import quick_party

# Stwórz grupę 4 bytów
party = await quick_party(4)

for being in party:
    print(f"✨ {being.name} ({being.archetype}) - Energy: {being.energy_level}")
    await being.commune(f"Hello, I am {being.name}!")
```

### Wszystkie Przykłady (3 minuty)

```python
from astral_beings import QuickStart

# Uruchom wszystkie gotowe przykłady
await QuickStart.run_all_examples()
```

## 🏛️ Archetypy Dostępne

### 🛡️ **Guardian** - Strażnik
- **Atrybuty**: power: 90, wisdom: 70, protection: 95
- **Zdolności**: shield, heal, protect, purify
- **Zastosowanie**: Ochrona danych, bezpieczeństwo, monitoring

### 🧙 **Mage** - Mag
- **Atrybuty**: power: 85, wisdom: 95, intellect: 90  
- **Zdolności**: cast_spell, divine, transmute, enchant
- **Zastosowanie**: AI processing, transformacje danych, analiza

### ⚔️ **Warrior** - Wojownik
- **Atrybuty**: power: 95, strength: 90, courage: 85
- **Zdolności**: strike, charge, defend, intimidate
- **Zastosowanie**: Wykonywanie zadań, cleanup, force operations

### 💚 **Healer** - Uzdrowiciel
- **Atrybuty**: wisdom: 90, compassion: 95, life_force: 85
- **Zdolności**: heal, restore, bless, cure
- **Zastosowanie**: Naprawa danych, recovery, maintenance

### 👁️ **Scout** - Zwiadowca
- **Atrybuty**: agility: 95, perception: 90, stealth: 85
- **Zdolności**: scout, track, hide, observe
- **Zastosowanie**: Monitoring, discovery, reconnaissance

### 📚 **Sage** - Mędrzec
- **Atrybuty**: wisdom: 95, knowledge: 90, memory: 85
- **Zdolności**: remember, teach, prophecy, analyze  
- **Zastosowanie**: Knowledge management, learning, documentation

## 🎯 Przykłady Użycia

### Podstawowe Operacje

```python
from astral_beings import BasicTemplates

# Stwórz asystenta
assistant = await BasicTemplates.create_assistant("Helper")

# Kanalizuj energię na zadanie
result = await assistant.channel_power("assist", target="data_processing", power=20)

# Medytuj aby przywrócić energię  
await assistant.meditate(duration=60)

# Sprawdź stan
print(f"Energy: {assistant.energy_level}")
print(f"Archetype: {assistant.archetype}")
```

### Niestandardowy Byt

```python
from astral_beings import BeingGenerator

# Stwórz wyspecjalizowanego bytu
programmer = await BeingGenerator.create_specialized_being({
    "archetype": "mage",
    "name": "CodeWizard", 
    "attributes": {
        "programming_skill": 95,
        "debugging_power": 90,
        "architecture_wisdom": 85
    },
    "abilities": ["code", "debug", "optimize", "refactor"],
    "description": "Master of code and digital architectures"
})

# Użyj specjalistycznych zdolności
await programmer.channel_power("code", target="new_application")
```

### Zaawansowane Szablony

```python
from astral_beings import AdvancedTemplates, BeingGenerator

# AI Companion z uczeniem się
ai_template = AdvancedTemplates.get_ai_companion_template()
ai_companion = await BeingGenerator.create_specialized_being(ai_template)

# Data Guardian dla bezpieczeństwa
data_template = AdvancedTemplates.get_data_guardian_template()  
data_guardian = await BeingGenerator.create_specialized_being(data_template)

# Creative Muse dla kreatywności
muse_template = AdvancedTemplates.get_creative_muse_template()
creative_muse = await BeingGenerator.create_specialized_being(muse_template)
```

## 🔋 System Energii

Każdy astralny byt ma **energię życiową**:

```python
# Sprawdź energię
print(f"Energy: {being.energy_level}")

# Akcje kosztują energię
await being.channel_power("heal", power=30)  # -30 energy

# Medytacja przywraca energię
await being.meditate(60)  # +50 energy (max 100)

# Energia wpływa na możliwości
if being.energy_level < 20:
    await being.meditate(100)  # Regeneruj przed akcją
```

## 🎭 Generatory

### Generator Duszy

```python
from astral_beings import SoulGenerator

# Standardowa dusze archetypu
soul = SoulGenerator.create_soul("guardian")

# Zrandomizowana dusze  
random_soul = SoulGenerator.create_soul("mage", randomize=True)

# Całkowicie losowa
surprise_soul = SoulGenerator.create_random_soul()

# Hybrydowa (mieszanka dwóch archetypów)
hybrid_soul = SoulGenerator.create_hybrid_soul("warrior", "mage", mix_ratio=0.7)
```

### Generator Bytów

```python
from astral_beings import BeingGenerator

# Standardowy byt
guardian = await BeingGenerator.create_being("guardian", "MyGuardian")

# Losowy byt
random_being = await BeingGenerator.create_random_being()

# Grupa bytów
party = await BeingGenerator.create_party(size=5)
```

## 📚 Gotowe Szablony

```python
from astral_beings import BasicTemplates

# Podstawowe szablony
guardian = await BasicTemplates.create_guardian("Protector")
assistant = await BasicTemplates.create_assistant("Helper")
messenger = await BasicTemplates.create_messenger("Herald")
healer = await BasicTemplates.create_healer("Lifegiver")
scholar = await BasicTemplates.create_scholar("Librarian")

# Lista wszystkich szablonów
templates = BasicTemplates.list_templates()
template = BasicTemplates.get_template_by_name("guardian")
```

## 💬 Komunikacja i Akcje

### Podstawowe Akcje

```python
# Komunikacja przez astralną płaszczyznę
result = await being.commune("Hello astral world!")

# Kanalizowanie energii przez zdolność
result = await being.channel_power("heal", target="injured_ally", power=25)

# Medytacja (przywraca energię)
result = await being.meditate(duration=80)

# Uniwersalne wywołanie
result = await being.invoke("custom_action", param1="value1")
```

### Wyniki Akcji

Wszystkie akcje zwracają strukturę:

```python
{
    "data": {
        "result": {
            "success": True,
            "effect": "Shield activated on sacred_temple",
            "energy_cost": 10,
            "remaining_energy": 90,
            "timestamp": "2025-01-30T12:00:00"
        }
    }
}
```

## 🧪 Kompletny Przykład

```python
import asyncio
from astral_beings import *

async def astral_adventure():
    # Stwórz grupę przygodników
    party = await BeingGenerator.create_party(4)
    
    print("🎭 Adventure Party:")
    for being in party:
        print(f"  - {being.name} ({being.archetype})")
    
    # Każdy wykona swoją specjalizację
    for being in party:
        if being.archetype == "guardian":
            await being.channel_power("protect", target="party")
        elif being.archetype == "healer":
            await being.channel_power("heal", target="wounded_ally") 
        elif being.archetype == "scout":
            await being.channel_power("scout", target="unknown_territory")
        else:
            await being.commune("Ready for adventure!")
    
    # Przywróć energię po akcji
    for being in party:
        await being.meditate(40)
    
    print("✅ Adventure completed!")

# Uruchom
asyncio.run(astral_adventure())
```

## 🔧 Pełne Demo

```bash
# Uruchom kompletną demonstrację
python examples/astral_beings_demo.py

# Skonfiguruj bibliotekę
python setup_astral_beings.py
```

## 🏗️ Architektura

Astral Beings jest zbudowana na:

- **LuxDB** - System genotypów i bytów
- **Soul Templates** - Szablony duszy z funkcjami
- **Being Management** - Zarządzanie życiem bytów  
- **Energy System** - System energii i regeneracji
- **Generator System** - Automatyczne tworzenie różnorodności

## 🌟 Dlaczego Astral Beings?

✅ **Proste** - 3 linie kodu = działający byt  
✅ **Ponadczasowe** - Uniwersalne archetypy  
✅ **Gotowe** - Działa out-of-the-box  
✅ **Rozszerzalne** - Łatwo dodać nowe archetypy  
✅ **Inteligentne** - Byty z pamięcią i energią  
✅ **Niezawodne** - Zbudowane na LuxOS/LuxDB  

## 🎯 Przypadki Użycia

- 🤖 **AI Assistants** - Inteligentni asystenci z osobowością
- 🛡️ **Security Guardians** - Strażnicy systemów i danych  
- 📊 **Data Processors** - Byty przetwarzające informacje
- 💬 **Chat Bots** - Konwersacyjne byty z emocjami
- 🎮 **Game NPCs** - Postacie gier z rzeczywistą AI
- 🔧 **System Monitors** - Byty monitorujące infrastrukturę

## 📖 Dokumentacja API

Pełna dokumentacja API dostępna w kodzie źródłowym. Każda klasa i metoda ma szczegółowe docstringi z przykładami użycia.

## 🤝 Rozwijanie

Biblioteka została zaprojektowana jako **ponadczasowa i rozszerzalna**. Nowe archetypy, zdolności i funkcjonalności można łatwo dodać bez zmiany core API.

---

### 🌌 *"W astralnej przestrzeni, każdy kod staje się żywym bytem"*

**Astral Beings Library v1.0.0** - Część ekosystemu LuxOS/LuxDB
