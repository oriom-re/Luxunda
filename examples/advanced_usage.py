
"""
Zaawansowany przykład użycia LuxDB z embeddings i złożonymi strukturami.
"""

import asyncio
import random
from luxdb import LuxDB, Soul, Being, Relationship

async def main():
    """
    Zaawansowany przykład z embeddings i złożonymi genotypami.
    """
    
    print("🧬 Zaawansowany przykład LuxDB...")
    
    # Inicjalizacja (użyj swoich danych)
    db = LuxDB(
        host='your-host',
        port=5432,
        user='your_user', 
        password='your_password',
        database='your_database'
    )
    
    async with db:
        
        # 1. Genotyp artykułu z embeddings
        print("📰 Tworzenie genotypu artykułu...")
        
        article_genotype = {
            "genesis": {
                "name": "article",
                "version": "2.0", 
                "description": "Artykuł z embeddings semantycznymi"
            },
            "attributes": {
                "title": {"py_type": "str", "max_length": 200},
                "content": {"py_type": "str"},
                "author_id": {"py_type": "str"},
                "tags": {"py_type": "List[str]"},
                "category": {"py_type": "str"},
                "publish_date": {"py_type": "str"},
                "view_count": {"py_type": "int", "default": 0},
                "rating": {"py_type": "float", "min_value": 0.0, "max_value": 5.0},
                "metadata": {"py_type": "dict"},
                "title_embedding": {"py_type": "List[float]", "vector_size": 1536},
                "content_embedding": {"py_type": "List[float]", "vector_size": 1536}
            }
        }
        
        article_soul = await Soul.create(article_genotype, alias="article_v2")
        print(f"✅ Article Soul: {article_soul.soul_hash[:16]}...")
        
        # 2. Genotyp kategorii
        print("📁 Tworzenie genotypu kategorii...")
        
        category_genotype = {
            "genesis": {
                "name": "category",
                "version": "1.0",
                "description": "Kategoria artykułów"
            },
            "attributes": {
                "name": {"py_type": "str", "unique": True},
                "description": {"py_type": "str"},
                "color": {"py_type": "str"},
                "icon": {"py_type": "str"},
                "settings": {"py_type": "dict"},
                "article_count": {"py_type": "int", "default": 0}
            }
        }
        
        category_soul = await Soul.create(category_genotype, alias="category")
        
        # 3. Tworzenie kategorii
        print("📂 Tworzenie kategorii...")
        
        categories_data = [
            {
                "name": "Technologia",
                "description": "Artykuły o najnowszych technologiach",
                "color": "#4A90E2", 
                "icon": "🔧",
                "settings": {"featured": True, "allow_comments": True}
            },
            {
                "name": "Nauka", 
                "description": "Odkrycia naukowe i badania",
                "color": "#50C878",
                "icon": "🔬", 
                "settings": {"featured": False, "allow_comments": True}
            }
        ]
        
        categories = []
        for cat_data in categories_data:
            category = await Being.create(category_soul, cat_data)
            categories.append(category)
            print(f"✅ Kategoria: {category.name}")
        
        # 4. Tworzenie artykułów z embeddings
        print("✍️ Tworzenie artykułów...")
        
        def generate_fake_embedding(size=1536):
            """Generuje fake embedding dla przykładu."""
            return [random.uniform(-1, 1) for _ in range(size)]
        
        articles_data = [
            {
                "title": "Przyszłość sztucznej inteligencji",
                "content": "Sztuczna inteligencja rozwija się w niewyobrażalnym tempie...",
                "author_id": "user_123",
                "tags": ["AI", "ML", "przyszłość", "technologia"],
                "category": "Technologia",
                "publish_date": "2025-01-29",
                "rating": 4.5,
                "metadata": {
                    "reading_time": 5,
                    "difficulty": "medium",
                    "sources": ["MIT", "Stanford"]
                },
                "title_embedding": generate_fake_embedding(),
                "content_embedding": generate_fake_embedding()
            },
            {
                "title": "Kwantowe komputery - rewolucja czy ewolucja?",
                "content": "Komputery kwantowe obiecują przełom w obliczeniach...",
                "author_id": "user_456", 
                "tags": ["quantum", "computing", "fizyka"],
                "category": "Nauka",
                "publish_date": "2025-01-28",
                "rating": 4.2,
                "metadata": {
                    "reading_time": 8,
                    "difficulty": "hard", 
                    "sources": ["Nature", "Science"]
                },
                "title_embedding": generate_fake_embedding(),
                "content_embedding": generate_fake_embedding()
            }
        ]
        
        articles = []
        for art_data in articles_data:
            article = await Being.create(article_soul, art_data)
            articles.append(article)
            print(f"✅ Artykuł: {article.title}")
        
        # 5. Tworzenie relacji między artykułami i kategoriami
        print("🔗 Tworzenie relacji...")
        
        # Relacja artykuł -> kategoria
        for article in articles:
            for category in categories:
                if article.category == category.name:
                    relation = await Relationship.create(
                        source_ulid=article.ulid,
                        target_ulid=category.ulid,
                        relation_type="belongs_to_category",
                        strength=1.0,
                        metadata={"assigned_at": "2025-01-29"}
                    )
                    print(f"🔗 {article.title} -> {category.name}")
        
        # Relacja podobieństwa między artykułami (na podstawie tagów)
        if len(articles) >= 2:
            # Znajdź wspólne tagi
            common_tags = set(articles[0].tags) & set(articles[1].tags)
            if common_tags:
                similarity = len(common_tags) / max(len(articles[0].tags), len(articles[1].tags))
                
                similar_relation = await Relationship.create(
                    source_ulid=articles[0].ulid,
                    target_ulid=articles[1].ulid,
                    relation_type="similar_content",
                    strength=similarity,
                    metadata={
                        "common_tags": list(common_tags),
                        "similarity_method": "tag_overlap"
                    }
                )
                print(f"🔗 Podobieństwo artykułów: {similarity:.2f}")
        
        # 6. Zaawansowane zapytania
        print("🔍 Wykonywanie zapytań...")
        
        # Wszystkie artykuły
        all_articles = await Being.load_all_by_soul_hash(article_soul.soul_hash)
        print(f"📊 Znaleziono {len(all_articles)} artykułów")
        
        # Wszystkie kategorie
        all_categories = await Being.load_all_by_soul_hash(category_soul.soul_hash)
        print(f"📊 Znaleziono {len(all_categories)} kategorii")
        
        # Sprawdź stan systemu
        health = await db.health_check()
        print(f"🏥 Stan systemu:")
        print(f"   - Souls: {health['souls_count']}")
        print(f"   - Beings: {health['beings_count']}")
        print(f"   - Relationships: {health['relationships_count']}")
        print(f"   - Pool size: {health['pool_size']}")
        
        print("✨ Zaawansowany przykład zakończony!")

if __name__ == "__main__":
    asyncio.run(main())
