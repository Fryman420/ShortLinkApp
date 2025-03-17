import time
import pytest
from fastapi.testclient import TestClient

from main import app
from cache import set_cache, get_cache, delete_cache, cache_store

# client = TestClient(app)

client = TestClient(app)

def authenticate_user(username: str, password: str) -> dict:
    # Регистрируем пользователя (если уже существует, регистрация проигнорируется)
    client.post("/users/register", json={"username": username, "password": password})
    login_response = client.post("/users/login", data={"username": username, "password": password})
    token = login_response.json().get("token")
    return {"Authorization": f"Bearer {token}"}

def test_create_link_api_anonymous():
    """
    Проверяем создание ссылки без авторизации.
    """
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "custom_alias": None,
            "expires_at": None
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    # Удаляем завершающий слэш для сравнения
    assert data["original_url"].rstrip("/") == "https://example.com"

def test_get_stats_caching():
    """
    Проверяем кэширование статистики ссылки.
    """
    headers = authenticate_user("test_user", "test_password")
    # Формируем уникальный alias для ссылки
    unique_alias = f"testlinkstats_{int(time.time()*1000)}"
    # Создаем ссылку с заданным alias для однозначности.
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://stats.com",
            "custom_alias": unique_alias,
            "expires_at": None
        },
        headers=headers
    )
    assert response.status_code == 201
    short_code = response.json()["short_code"]

    # Первый запрос статистики (без кэша).
    response_stats = client.get(f"/links/{short_code}/stats")
    assert response_stats.status_code == 200
    stats_data = response_stats.json()
    clicks_initial = stats_data["clicks"]

    # Имитируем клик по ссылке. Отключаем автоматическое следование редиректам.
    response_redirect = client.get(f"/links/{short_code}", follow_redirects=False)
    assert response_redirect.status_code == 302

    # Проверяем, что кэшированное значение не изменилось.
    response_stats_cached = client.get(f"/links/{short_code}/stats")
    stats_cached = response_stats_cached.json()
    assert stats_cached["clicks"] == clicks_initial

    # Обновляем ссылку, что должно привести к инвалидации кэша.
    update_response = client.put(
        f"/links/{short_code}",
        json={"original_url": "https://newstats.com"},
        headers=headers
    )
    assert update_response.status_code == 200

    # Проверяем обновлённую статистику.
    response_stats_updated = client.get(f"/links/{short_code}/stats")
    stats_updated = response_stats_updated.json()
    assert stats_updated["original_url"].rstrip("/") == "https://newstats.com"

def test_update_link_api_authenticated():
    """
    Проверяем обновление ссылки с авторизацией.
    """
    headers = authenticate_user("update_user", "update_password")
    # Формируем уникальный alias для ссылки
    unique_alias = f"updatelink_{int(time.time()*1000)}"
    # Создаем ссылку.
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://update.com",
            "custom_alias": unique_alias,
            "expires_at": None
        },
        headers=headers
    )
    assert response.status_code == 201
    short_code = response.json()["short_code"]

    # Обновляем ссылку через PUT-эндпоинт.
    update_response = client.put(
        f"/links/{short_code}",
        json={"original_url": "https://updated.com"},
        headers=headers
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["message"] == "Ссылка обновлена"

    # Проверяем, что обновление прошло успешно.
    stats_response = client.get(f"/links/{short_code}/stats")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert stats_data["original_url"].rstrip("/") == "https://updated.com"

def test_delete_link_api_authenticated():
    """
    Проверяем удаление ссылки с авторизацией.
    """
    headers = authenticate_user("delete_user", "delete_password")
    # Формируем уникальный alias для ссылки
    unique_alias = f"deletelink_{int(time.time()*1000)}"
    # Создаем ссылку.
    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://delete.com",
            "custom_alias": unique_alias,
            "expires_at": None
        },
        headers=headers
    )
    assert response.status_code == 201
    short_code = response.json()["short_code"]

    # Удаляем ссылку через DELETE-эндпоинт.
    delete_response = client.delete(f"/links/{short_code}", headers=headers)
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["message"] == "Ссылка удалена"

    # Проверяем, что статистика для удаленной ссылки недоступна.
    stats_response = client.get(f"/links/{short_code}/stats")
    assert stats_response.status_code == 404

def test_cache_functions():
    """
    Тестируем работу in-memory кэша.
    """
    cache_store.clear()
    set_cache("key1", "value1", ttl=2)
    assert get_cache("key1") == "value1"
    time.sleep(3)
    assert get_cache("key1") is None

    set_cache("key2", "value2", ttl=10)
    assert get_cache("key2") == "value2"
    delete_cache("key2")
    assert get_cache("key2") is None
