
"""
Przykładowy genotyp z genami oznaczonymi dekoratorami
Ten plik będzie automatycznie przetworzony przez system genetyczny
"""

from app.genetics.gene_registry import gene
from datetime import datetime
import json

@gene(name="advanced_log", description="Zaawansowany system logowania z poziomami")
async def advanced_log(message: str, level: str = "INFO", context: dict = None):
    """Gen zaawansowanego logowania"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'level': level.upper(),
        'message': message,
        'context': context or {},
        'gene': 'advanced_log',
        'genotype': 'example_logger_genotype'
    }
    
    print(f"📝 [{level.upper()}] {timestamp}: {message}")
    if context:
        print(f"   📋 Kontekst: {json.dumps(context, indent=2, ensure_ascii=False)}")
    
    return log_entry

@gene(name="format_message", description="Formatuje wiadomości z różnymi stylami")
def format_message(message: str, style: str = "standard"):
    """Gen formatowania wiadomości"""
    styles = {
        'standard': f"📄 {message}",
        'success': f"✅ {message}",
        'error': f"❌ {message}",
        'warning': f"⚠️ {message}",
        'info': f"ℹ️ {message}",
        'debug': f"🐛 {message}"
    }
    
    formatted = styles.get(style, f"📄 {message}")
    return {
        'original': message,
        'formatted': formatted,
        'style': style,
        'gene': 'format_message'
    }

@gene(name="log_with_tags", description="Logowanie z tagami i kategoryzacją")
async def log_with_tags(message: str, tags: list = None, category: str = "general"):
    """Gen logowania z tagami"""
    tags = tags or []
    timestamp = datetime.now().isoformat()
    
    tags_str = " ".join([f"#{tag}" for tag in tags]) if tags else ""
    category_str = f"[{category.upper()}]"
    
    formatted_message = f"{category_str} {message} {tags_str}"
    print(f"🏷️ {timestamp}: {formatted_message}")
    
    return {
        'timestamp': timestamp,
        'message': message,
        'tags': tags,
        'category': category,
        'formatted': formatted_message,
        'gene': 'log_with_tags'
    }

# Funkcja inicjalizacyjna genotypu (nie jest genem)
async def init():
    """Inicjalizacja genotypu - ładowana automatycznie"""
    print("🧬 Inicjalizacja genotypu: Example Logger")
    print("📝 Dostępne geny: advanced_log, format_message, log_with_tags")
    return {
        'genotype': 'example_logger_genotype',
        'genes_count': 3,
        'initialized': True,
        'timestamp': datetime.now().isoformat()
    }

# Metadata genotypu
__genotype_info__ = {
    'name': 'Example Logger Genotype',
    'version': '1.0.0',
    'description': 'Przykładowy genotyp z genami do logowania',
    'author': 'LuxOS Genetic System',
    'genes': ['advanced_log', 'format_message', 'log_with_tags']
}
