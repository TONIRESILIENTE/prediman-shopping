# tests/test_analytics/test_regras.py
"""
Testes para as regras de engenharia do motor analítico.
"""
import pytest
from src.analytics.regras import (
    analisar_chiller,
    analisar_subestacao,
    analisar_bomba,
    analisar_iluminacao,
    Diagnostico,
)


class TestChillerRegras:
    """Regras para o chiller."""

    def test_chiller_normal_nao_detecta_anomalia(self):
        leitura = {
            "equipamento_id": "Chiller_01",
            "vibracao_mm_s": 3.0,
            "delta_t_c": 5.0,
            "corrente_a": 60.0,
        }
        diag = analisar_chiller(leitura)
        assert diag.anomalia_detectada is False
        assert diag.severidade == "normal"

    def test_vibracao_alta_detecta_desgaste_rolamento(self):
        leitura = {
            "equipamento_id": "Chiller_01",
            "vibracao_mm_s": 9.0,
            "delta_t_c": 5.0,
            "corrente_a": 60.0,
        }
        diag = analisar_chiller(leitura)
        assert diag.anomalia_detectada is True
        assert diag.tipo_anomalia == "desgaste_rolamento"
        assert diag.severidade == "alta"

    def test_delta_t_baixo_detecta_baixa_eficiencia(self):
        leitura = {
            "equipamento_id": "Chiller_01",
            "vibracao_mm_s": 3.0,
            "delta_t_c": 1.5,
            "corrente_a": 60.0,
        }
        diag = analisar_chiller(leitura)
        assert diag.anomalia_detectada is True
        assert diag.tipo_anomalia == "baixa_eficiencia"

    def test_corrente_alta_detecta_sobrecarga(self):
        leitura = {
            "equipamento_id": "Chiller_01",
            "vibracao_mm_s": 3.0,
            "delta_t_c": 5.0,
            "corrente_a": 90.0,
        }
        diag = analisar_chiller(leitura)
        assert diag.anomalia_detectada is True
        assert diag.tipo_anomalia == "sobrecarga"


class TestSubestacaoRegras:
    """Regras para a subestação."""

    def test_fp_abaixo_limite_detecta_anomalia(self):
        leitura = {
            "equipamento_id": "Subestacao_Principal",
            "fator_potencia": 0.85,
            "tensao_v": 380,
            "corrente_a": 200,
            "temperatura_c": 45,
        }
        diag = analisar_subestacao(leitura)
        assert diag.anomalia_detectada is True
        assert diag.tipo_anomalia == "fp_baixo"

    def test_subestacao_normal(self):
        leitura = {
            "equipamento_id": "Subestacao_Principal",
            "fator_potencia": 0.95,
            "tensao_v": 380,
            "corrente_a": 200,
            "temperatura_c": 45,
        }
        diag = analisar_subestacao(leitura)
        assert diag.anomalia_detectada is False

    def test_corrente_critica_detecta_sobrecarga(self):
        leitura = {
            "equipamento_id": "Subestacao_Principal",
            "fator_potencia": 0.95,
            "tensao_v": 380,
            "corrente_a": 350,
            "temperatura_c": 45,
        }
        diag = analisar_subestacao(leitura)
        assert diag.tipo_anomalia == "sobrecarga_fase"
        assert diag.severidade == "critica"


class TestBombaRegras:
    """Regras para a bomba de recalque."""

    def test_bomba_desligada_normal(self):
        leitura = {
            "equipamento_id": "Bomba_Recalque_G1",
            "vibracao_mm_s": 0,
            "corrente_a": 0,
            "nivel_poco_m": 2.5,
            "status_bomba": "desligada",
        }
        diag = analisar_bomba(leitura)
        assert diag.anomalia_detectada is False

    def test_poco_seco_detecta_critico(self):
        leitura = {
            "equipamento_id": "Bomba_Recalque_G1",
            "vibracao_mm_s": 5.0,
            "corrente_a": 6.0,
            "nivel_poco_m": 0.1,
            "status_bomba": "ligada",
        }
        diag = analisar_bomba(leitura)
        assert diag.tipo_anomalia == "poco_seco"
        assert diag.severidade == "critica"

    def test_cavitacao_detectada_por_assinatura(self):
        leitura = {
            "equipamento_id": "Bomba_Recalque_G1",
            "vibracao_mm_s": 8.0,
            "corrente_a": 6.0,
            "nivel_poco_m": 2.0,
            "status_bomba": "ligada",
        }
        diag = analisar_bomba(leitura)
        assert diag.tipo_anomalia == "cavitacao"


class TestIluminacaoRegras:
    """Regras para iluminação."""

    def test_timer_falho_detectado(self):
        leitura = {
            "equipamento_id": "Iluminacao_Praca",
            "corrente_a": 45,
            "estado": "ligado_fora_horario",
            "hora_simulada": 3,
        }
        diag = analisar_iluminacao(leitura)
        assert diag.tipo_anomalia == "timer_falho"

    def test_lampadas_queimadas_detectado(self):
        leitura = {
            "equipamento_id": "Iluminacao_Praca",
            "corrente_a": 1.0,
            "estado": "ligado",
            "hora_simulada": 14,
        }
        diag = analisar_iluminacao(leitura)
        assert diag.tipo_anomalia == "lampadas_queimadas"
