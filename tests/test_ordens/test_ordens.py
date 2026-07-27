# tests/test_ordens/test_ordens.py
"""
Testes para o serviço de Ordens de Serviço.
"""
import pytest
from src.services.ordens_service import (
    criar_ordem_servico,
    listar_ordens,
    buscar_ordem_por_id,
    atualizar_status,
    MAPA_ANOMALIA_PARA_OS,
    OrdemServico,
)


class TestCriarOrdemServico:
    """Testes de criação de OS."""

    def test_deve_criar_os_para_anomalia_mapeada(self):
        os = criar_ordem_servico(
            equipamento_id="Chiller_01",
            tipo_anomalia="desgaste_rolamento",
            severidade="alta",
            detalhes="Vibracao 9.5 mm/s",
        )

        assert os.equipamento_id == "Chiller_01"
        assert os.tipo_anomalia == "desgaste_rolamento"
        assert os.severidade == "alta"
        assert os.status == "aberta"
        assert os.pop_codigo == "POP-CHL-001"
        assert "Vibracao 9.5 mm/s" in os.descricao

    def test_deve_lancar_erro_para_anomalia_nao_mapeada(self):
        with pytest.raises(ValueError, match="não possui OS mapeada"):
            criar_ordem_servico(
                equipamento_id="Chiller_01",
                tipo_anomalia="anomalia_inexistente",
                severidade="baixa",
                detalhes="teste",
            )

    def test_cada_os_tem_id_unico(self):
        os1 = criar_ordem_servico(
            "Chiller_01", "desgaste_rolamento", "alta", "teste"
        )
        os2 = criar_ordem_servico(
            "Chiller_01", "baixa_eficiencia", "media", "teste"
        )

        assert os1.id != os2.id

    def test_todas_anomalias_mapeadas_tem_pop(self):
        """Garante que toda anomalia no mapa tem pop_codigo."""
        for tipo, template in MAPA_ANOMALIA_PARA_OS.items():
            assert "pop_codigo" in template, \
                f"Anomalia '{tipo}' não tem pop_codigo"
            assert template["pop_codigo"].startswith("POP-"), \
                f"pop_codigo inválido para '{tipo}'"


class TestListarOrdens:
    """Testes de listagem."""

    def test_deve_listar_todas_ordens(self):
        # Cria algumas OS
        criar_ordem_servico("Chiller_01", "desgaste_rolamento", "alta", "t1")
        criar_ordem_servico("Bomba_Recalque_G1", "cavitacao", "alta", "t2")

        ordens = listar_ordens()
        assert len(ordens) >= 2

    def test_deve_filtrar_por_equipamento(self):
        criar_ordem_servico("Chiller_01", "desgaste_rolamento", "alta", "t1")
        criar_ordem_servico("Bomba_Recalque_G1", "cavitacao", "alta", "t2")

        ordens_chiller = listar_ordens(equipamento_id="Chiller_01")
        assert all(os.equipamento_id == "Chiller_01" for os in ordens_chiller)

    def test_deve_filtrar_por_status(self):
        os = criar_ordem_servico(
            "Chiller_01", "desgaste_rolamento", "alta", "t1")
        atualizar_status(os.id, "concluida")

        abertas = listar_ordens(status="aberta")
        concluidas = listar_ordens(status="concluida")

        assert all(os.status == "aberta" for os in abertas)
        assert all(os.status == "concluida" for os in concluidas)


class TestAtualizarStatus:
    """Testes de atualização de status."""

    def test_deve_atualizar_status(self):
        os = criar_ordem_servico(
            "Chiller_01", "desgaste_rolamento", "alta", "t1")

        atualizado = atualizar_status(os.id, "em_andamento")
        assert atualizado.status == "em_andamento"

    def test_deve_registrar_conclusao(self):
        os = criar_ordem_servico(
            "Chiller_01", "desgaste_rolamento", "alta", "t1")

        atualizado = atualizar_status(os.id, "concluida")
        assert atualizado.status == "concluida"
        assert atualizado.concluido_em is not None

    def test_deve_retornar_none_para_id_inexistente(self):
        resultado = atualizar_status("id_inexistente", "concluida")
        assert resultado is None
