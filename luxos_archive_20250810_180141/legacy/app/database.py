
# Globalna pula połączeń do bazy danych
db_pool = None

async def get_db_pool():
    """Zwraca aktualną pulę połączeń do bazy danych"""
    global db_pool
    return db_pool

def set_db_pool(pool):
    """Ustawia pulę połączeń do bazy danych"""
    global db_pool
    db_pool = pool
