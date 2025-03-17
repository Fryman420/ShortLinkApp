import time

# Простой in-memory кэш на базе словаря
cache_store = {}

def set_cache(key: str, value, ttl: int):
    """Сохраняет значение в кэше с временем жизни ttl (в секундах)."""
    expire_at = time.time() + ttl
    cache_store[key] = (value, expire_at)

def get_cache(key: str):
    """Возвращает значение из кэша, если оно не истекло."""
    entry = cache_store.get(key)
    if entry:
        value, expire_at = entry
        if time.time() < expire_at:
            return value
        else:
            # Если срок хранения истёк — удаляем запись
            del cache_store[key]
    return None

def delete_cache(key: str):
    """Удаляет значение из кэша по ключу."""
    if key in cache_store:
        del cache_store[key]
