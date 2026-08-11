# tests/test_auth/test_auth.py
"""Testes de autenticação JWT — usando PostgreSQL real."""
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestRegistro:
    def test_deve_registrar_usuario_valido(self):
        response = client.post("/api/v1/auth/registro", json={
            "email": "tecnico@prediman.com", "senha": "Senha123",
            "nome": "João Técnico", "papel": "tecnico",
        })
        # Pode ser 201 ou 409 se já existir
        assert response.status_code in [201, 409]

    def test_deve_rejeitar_email_duplicado(self):
        client.post("/api/v1/auth/registro", json={
            "email": "dup@prediman.com", "senha": "Senha123", "nome": "Teste",
        })
        response = client.post("/api/v1/auth/registro", json={
            "email": "dup@prediman.com", "senha": "Senha123", "nome": "Teste 2",
        })
        assert response.status_code == 409

    def test_deve_rejeitar_senha_curta(self):
        response = client.post("/api/v1/auth/registro", json={
            "email": "curta@prediman.com", "senha": "12345", "nome": "Teste",
        })
        assert response.status_code == 422


class TestLogin:
    def test_deve_logar_com_credenciais_corretas(self):
        client.post("/api/v1/auth/registro", json={
            "email": "login@prediman.com", "senha": "Senha123", "nome": "Teste",
        })
        response = client.post("/api/v1/auth/login", json={
            "email": "login@prediman.com", "senha": "Senha123",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_deve_rejeitar_senha_incorreta(self):
        client.post("/api/v1/auth/registro", json={
            "email": "login2@prediman.com", "senha": "Senha123", "nome": "Teste",
        })
        response = client.post("/api/v1/auth/login", json={
            "email": "login2@prediman.com", "senha": "SenhaErrada",
        })
        assert response.status_code == 401

    def test_deve_rejeitar_email_inexistente(self):
        response = client.post("/api/v1/auth/login", json={
            "email": "naoexiste@prediman.com", "senha": "Senha123",
        })
        assert response.status_code == 401


class TestRotasProtegidas:
    def test_me_sem_token_deve_retornar_403(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403]

    def test_me_com_token_valido(self):
        client.post("/api/v1/auth/registro", json={
            "email": "protegido@prediman.com", "senha": "Senha123", "nome": "Teste",
        })
        login_resp = client.post("/api/v1/auth/login", json={
            "email": "protegido@prediman.com", "senha": "Senha123",
        })
        token = login_resp.json()["access_token"]
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "protegido@prediman.com"
