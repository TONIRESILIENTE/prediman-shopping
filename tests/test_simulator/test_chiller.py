# tests/test_simulator/test_chiller.py
"""
Testes do simulador de Chiller.
"""
import pytest
from src.simulator.chiller import ChillerSimulator


class TestChillerNormal:
    """Testes para operação NORMAL do chiller."""

    def test_deve_gerar_leitura_com_todos_os_campos(self):
        # Arrange
        chiller = ChillerSimulator(seed=42)

        # Act
        leitura = chiller.gerar_leitura()

        # Assert — verifica que todos os campos existem
        assert "vibracao_mm_s" in leitura
        assert "temp_entrada_c" in leitura
        assert "temp_saida_c" in leitura
        assert "delta_t_c" in leitura
        assert "corrente_a" in leitura
        assert "equipamento_id" in leitura
        assert "timestamp" in leitura

    def test_deve_gerar_vibracao_dentro_do_range_normal(self):
        chiller = ChillerSimulator(seed=42)
        leituras = [chiller.gerar_leitura() for _ in range(20)]

        for leitura in leituras:
            # Vibração normal: entre 1.5 e 5.0 mm/s (com ruído)
            assert 1.0 <= leitura["vibracao_mm_s"] <= 6.0, \
                f"Vibracao fora do range: {leitura['vibracao_mm_s']}"

    def test_delta_t_deve_ser_positivo(self):
        chiller = ChillerSimulator(seed=42)
        leituras = [chiller.gerar_leitura() for _ in range(20)]

        for leitura in leituras:
            # ΔT = temp_entrada - temp_saida deve ser > 0
            delta = leitura["temp_entrada_c"] - leitura["temp_saida_c"]
            assert delta > 0, f"Delta T negativo: {delta}"

    def test_sem_anomalia_flag_deve_ser_false(self):
        chiller = ChillerSimulator(seed=42)
        leitura = chiller.gerar_leitura()
        assert leitura["anomalia_detectada"] is False
        assert leitura["tipo_anomalia"] is None


class TestChillerAnomalia:
    """Testes para injeção de ANOMALIAS."""

    def test_desgaste_rolamento_deve_aumentar_vibracao(self):
        # Arrange
        chiller = ChillerSimulator(seed=42)
        chiller.ativar_anomalia("desgaste_rolamento")

        # Act
        leitura = chiller.gerar_leitura()

        # Assert — vibração deve ser > 3x a base
        assert leitura["vibracao_mm_s"] > 8.0, \
            f"Vibracao esperada > 8.0, obtida: {leitura['vibracao_mm_s']}"
        assert leitura["anomalia_detectada"] is True
        assert leitura["tipo_anomalia"] == "desgaste_rolamento"

    def test_baixa_eficiencia_deve_reduzir_delta_t(self):
        chiller = ChillerSimulator(seed=42)
        chiller.ativar_anomalia("baixa_eficiencia")

        leitura = chiller.gerar_leitura()

        # ΔT abaixo de 3°C indica baixa eficiência
        assert leitura["delta_t_c"] < 3.0, \
            f"Delta T esperado < 3.0, obtido: {leitura['delta_t_c']}"

    def test_sobrecarga_deve_aumentar_corrente(self):
        chiller = ChillerSimulator(seed=42)
        chiller.ativar_anomalia("sobrecarga")

        leitura = chiller.gerar_leitura()

        # Corrente > 70A indica sobrecarga
        assert leitura["corrente_a"] > 70.0, \
            f"Corrente esperada > 70, obtida: {leitura['corrente_a']}"

    def test_desativar_anomalia_volta_ao_normal(self):
        chiller = ChillerSimulator(seed=42)
        chiller.ativar_anomalia("desgaste_rolamento")
        chiller.desativar_anomalia()

        leitura = chiller.gerar_leitura()

        assert leitura["anomalia_detectada"] is False
        assert leitura["vibracao_mm_s"] < 6.0


class TestChillerEdgeCases:
    """Testes de borda."""

    def test_mesma_seed_gera_mesma_sequencia(self):
        c1 = ChillerSimulator(seed=99)
        c2 = ChillerSimulator(seed=99)

        l1 = c1.gerar_leitura()
        l2 = c2.gerar_leitura()

        # Com mesma seed, primeira leitura deve ser idêntica
        assert l1["vibracao_mm_s"] == l2["vibracao_mm_s"]
        assert l1["delta_t_c"] == l2["delta_t_c"]
