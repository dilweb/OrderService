"""
Пример тестов для функциональности refresh токенов.
Эти тесты демонстрируют, как тестировать refresh токены.
"""

import pytest
from datetime import timedelta, datetime, timezone
from src.users.auth.auth import (
    create_refresh_token, 
    verify_refresh_token,
    create_access_token,
    TokenType
)


def test_create_refresh_token():
    """Тест создания refresh токена"""
    user_id = 123
    token = create_refresh_token(user_id=user_id)
    
    # Проверяем, что токен создан
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_refresh_token():
    """Тест верификации валидного refresh токена"""
    user_id = 456
    token = create_refresh_token(user_id=user_id)
    
    # Проверяем токен
    token_data = verify_refresh_token(token)
    
    assert token_data is not None
    assert token_data["user_id"] == user_id
    assert token_data["type"] == TokenType.REFRESH.value


def test_verify_invalid_refresh_token():
    """Тест верификации невалидного refresh токена"""
    invalid_token = "invalid.token.here"
    
    token_data = verify_refresh_token(invalid_token)
    
    assert token_data is None


def test_verify_access_token_as_refresh():
    """Тест: access токен не должен проходить верификацию как refresh токен"""
    user_id = 789
    access_token = create_access_token({"sub": str(user_id)})
    
    # Пытаемся проверить access токен как refresh токен
    token_data = verify_refresh_token(access_token)
    
    # Должно вернуть None, т.к. тип токена не совпадает
    assert token_data is None


def test_refresh_token_contains_correct_data():
    """Тест: refresh токен содержит правильные данные"""
    user_id = 999
    token = create_refresh_token(user_id=user_id)
    token_data = verify_refresh_token(token)
    
    assert token_data is not None
    assert "user_id" in token_data
    assert "type" in token_data
    assert token_data["user_id"] == user_id
    assert token_data["type"] == TokenType.REFRESH.value


# Примечание: Для интеграционных тестов эндпоинтов потребуется:
# - TestClient из fastapi.testclient
# - Настроенная тестовая база данных
# - Фикстуры для создания тестовых пользователей

"""
Пример интеграционного теста (требует настройки тестовой БД):

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_login_returns_tokens():
    # Создать тестового пользователя в БД
    response = client.post("/login/", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_endpoint():
    # 1. Залогиниться и получить токены
    login_response = client.post("/login/", json={
        "email": "test@example.com",
        "password": "password123"
    })
    tokens = login_response.json()
    
    # 2. Использовать refresh токен
    refresh_response = client.post("/refresh/", json={
        "refresh_token": tokens["refresh_token"]
    })
    
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    
    # 3. Новые токены должны отличаться от старых
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
"""
 