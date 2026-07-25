# tests/test_api/test_dados.py
"""
Testes para os endpoints de ingestão de dados.
Usamos TestClient do FastAPI — não precisa de servidor rodando.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestReceberMedicao:
    """Testes para POST /api/v1/medicao"""

    def test_deve_receber_leitura_normal_chiller(self):
        # Arrange
        payload = {
            "equipamento_id": "Chiller_01",
            "tipo": "chiller",
            "dados": {
                "vibracao_mm_s": 3.0,
                "delta_t_c": 5.0,
                "corrente_a": 60.0,
                "temp_entrada_c": 12.0,
                "temp_saida_c": 7.0,
            },
        }
        
        # Act
        response = client.post("/api/v1/medicao", json=payload)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "processado"
        assert data["equipamento_id"] == "Chiller_01"
        assert data["diagnostico"]["anomalia_detectada"] is False

    def test_deve_detectar_anomalia_vibracao_alta(self):
        payload = {
            "equipamento_id": "Chiller_01",
            "tipo": "chiller",
            "dados": {
                "vibracao_mm_s": 9.5,
                "delta_t_c": 5.0,
                "corrente_a": 60.0,
                "temp_entrada_c": 12.0,
                "temp_saida_c": 7.0,
            },
        }
        
        response = client.post("/api/v1/medicao", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["diagnostico"]["anomalia_detectada"] is True
        assert data["diagnostico"]["tipo_anomalia"] == "desgaste_rolamento"
        assert data["diagnostico"]["severidade"] == "alta"

    def test_deve_rejeitar_tipo_invalido(self):
        payload = {
            "equipamento_id": "Chiller_01",
            "tipo": "tipo_inexistente",
            "dados": {"vibracao_mm_s": 3.0},
        }
        
        response = client.post("/api/v1/medicao", json=payload)
        
        # 422 = Unprocessable Entity (erro de validação)
        assert response.status_code == 422

    def test_deve_rejeitar_campo_obrigatorio_faltando(self):
        payload = {
            "equipamento_id": "Chiller_01",
            "tipo": "chiller",
            "dados": {
                "vibracao_mm_s": 3.0,
                # falta delta_t_c e corrente_a
            },
        }
        
        response = client.post("/api/v1/medicao", json=payload)
        assert response.status_code == 422


class TestReceberLote:
    """Testes para POST /api/v1/medicao/lote"""

    def test_deve_processar_lote_valido(self):
        payload = {
            "medicoes": [
                {
                    "equipamento_id": "Chiller_01",
                    "tipo": "chiller",
                    "dados": {
                        "vibracao_mm_s": 3.0,
                        "delta_t_c": 5.0,
                        "corrente_a": 60.0,
                        "temp_entrada_c": 12.0,
                        "temp_saida_c": 7.0,
                    },
                },
                {
                    "equipamento_id": "Subestacao_Principal",
                    "tipo": "subestacao",
                    "dados": {
                        "fator_potencia": 0.85,
                        "tensao_v": 380,
                        "corrente_a": 200,
                    },
                },
            ],
        }
        
        response = client.post("/api/v1/medicao/lote", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["total_recebido"] == 2
        assert data["total_anomalias"] >= 1  # FP 0.85 é anomalia

    def test_deve_rejeitar_lote_vazio(self):
        payload = {"medicoes": []}
        
        response = client.post("/api/v1/medicao/lote", json=payload)
        assert response.status_code == 422


class TestConsultarDiagnostico:
    """Testes para GET /api/v1/diagnostico/{id}"""

    def test_deve_retornar_diagnostico_existente(self):
        # Primeiro, enviamos uma leitura
        client.post("/api/v1/medicao", json={
            "equipamento_id": "Chiller_01",
            "tipo": "chiller",
            "dados": {
                "vibracao_mm_s": 3.0,
                "delta_t_c": 5.0,
                "corrente_a": 60.0,
                "temp_entrada_c": 12.0,
                "temp_saida_c": 7.0,
            },
        })
        
        # Depois, consultamos
        response = client.get("/api/v1/diagnostico/Chiller_01")
        
        assert response.status_code == 200
        data = response.json()
        assert data["equipamento_id"] == "Chiller_01"

    def test_deve_retornar_404_para_equipamento_sem_diagnostico(self):
        response = client.get("/api/v1/diagnostico/Inexistente")
        assert response.status_code == 404