# tests/test_api/test_dados.py
"""Testes para os endpoints de ingestão de dados."""
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestReceberMedicao:
    def test_deve_receber_leitura_normal_chiller(self):
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
        response = client.post("/api/v1/medicao", json=payload)
        assert response.status_code == 201

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

    def test_deve_rejeitar_tipo_invalido(self):
        response = client.post("/api/v1/medicao", json={
            "equipamento_id": "Chiller_01",
            "tipo": "tipo_inexistente",
            "dados": {"vibracao_mm_s": 3.0},
        })
        assert response.status_code == 422

    def test_deve_rejeitar_campo_obrigatorio_faltando(self):
        response = client.post("/api/v1/medicao", json={
            "equipamento_id": "Chiller_01",
            "tipo": "chiller",
            "dados": {"vibracao_mm_s": 3.0},
        })
        assert response.status_code == 422


class TestReceberLote:
    def test_deve_processar_lote_valido(self):
        payload = {
            "medicoes": [
                {"equipamento_id": "Chiller_01", "tipo": "chiller", "dados": {
                    "vibracao_mm_s": 3.0, "delta_t_c": 5.0, "corrente_a": 60.0,
                    "temp_entrada_c": 12.0, "temp_saida_c": 7.0,
                }},
                {"equipamento_id": "Subestacao_Principal", "tipo": "subestacao", "dados": {
                    "fator_potencia": 0.85, "tensao_v": 380, "corrente_a": 200,
                }},
            ],
        }
        response = client.post("/api/v1/medicao/lote", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["total_recebido"] == 2

    def test_deve_rejeitar_lote_vazio(self):
        response = client.post("/api/v1/medicao/lote", json={"medicoes": []})
        assert response.status_code == 422


class TestConsultarDiagnostico:
    def test_deve_retornar_diagnostico_existente(self):
        client.post("/api/v1/medicao", json={
            "equipamento_id": "Chiller_01", "tipo": "chiller",
            "dados": {"vibracao_mm_s": 3.0, "delta_t_c": 5.0, "corrente_a": 60.0,
                      "temp_entrada_c": 12.0, "temp_saida_c": 7.0},
        })
        response = client.get("/api/v1/diagnostico/Chiller_01")
        assert response.status_code == 200

    def test_deve_retornar_404_para_equipamento_sem_diagnostico(self):
        response = client.get("/api/v1/diagnostico/Inexistente")
        assert response.status_code == 404
