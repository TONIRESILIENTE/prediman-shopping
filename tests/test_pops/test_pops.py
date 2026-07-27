# tests/test_pops/test_pops.py
"""Testes do sistema de POPs."""
import pytest
from src.services.pops_service import buscar_pop, listar_pops, total_pops, POPS


class TestBuscarPOP:
    def test_deve_buscar_pop_existente(self):
        pop = buscar_pop("POP-CHL-001")
        assert pop is not None
        assert pop.codigo == "POP-CHL-001"
        assert "Compressor" in pop.titulo
        assert len(pop.epis) >= 3
        assert len(pop.passos) >= 5
        assert len(pop.riscos) >= 2

    def test_deve_retornar_none_para_inexistente(self):
        assert buscar_pop("POP-XYZ-999") is None

    def test_busca_case_insensitive(self):
        assert buscar_pop("pop-chl-001") is not None


class TestListarPOPs:
    def test_deve_listar_todos(self):
        todos = listar_pops()
        assert len(todos) == total_pops()

    def test_deve_filtrar_por_tipo(self):
        chiller = listar_pops(equipamento_tipo="chiller")
        assert all(p.equipamento_tipo == "chiller" for p in chiller)
        assert len(chiller) == 3


class TestQualidadePOPs:
    """Garante que todos os POPs estão completos."""

    @pytest.mark.parametrize("codigo", list(POPS.keys()))
    def test_pop_tem_todos_os_campos_obrigatorios(self, codigo):
        pop = POPS[codigo]
        assert pop.codigo, f"{codigo}: codigo vazio"
        assert pop.titulo, f"{codigo}: titulo vazio"
        assert pop.tempo_estimado_minutos > 0, f"{codigo}: tempo inválido"
        assert len(pop.epis) > 0, f"{codigo}: sem EPIs"
        assert len(pop.ferramentas) > 0, f"{codigo}: sem ferramentas"
        assert len(pop.passos) > 0, f"{codigo}: sem passos"
        assert len(pop.riscos) > 0, f"{codigo}: sem riscos"

    @pytest.mark.parametrize("codigo", list(POPS.keys()))
    def test_pop_tem_passos_numerados(self, codigo):
        pop = POPS[codigo]
        for i, passo in enumerate(pop.passos, 1):
            assert str(i) in passo, \
                f"{codigo}: passo {i} não numerado: {passo[:50]}"
