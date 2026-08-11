# tests/test_ordens/test_ordens.py
"""Testes do serviço de Ordens de Serviço com PostgreSQL real."""
import pytest
from src.services.ordens_service import (
    criar_ordem_servico,
    listar_ordens,
    buscar_ordem_por_id,
    atualizar_status,
    MAPA_ANOMALIA_PARA_OS,
)
from src.database.connection import SessionLocal


def _db():
    """Cria uma sessão de banco para um teste."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestCriarOrdemServico:
    def test_deve_criar_os_para_anomalia_mapeada(self):
        db = next(_db())
        os = criar_ordem_servico(
            db=db, equipamento_id="Chiller_01", tipo_anomalia="desgaste_rolamento",
            severidade="alta", detalhes="Vibracao 9.5 mm/s",
        )
        assert os.titulo == "Verificar compressor — vibração anômala"
        assert os.severidade == "alta"
        assert os.status == "aberta"

    def test_deve_lancar_erro_para_anomalia_nao_mapeada(self):
        db = next(_db())
        with pytest.raises(ValueError, match="não possui OS mapeada"):
            criar_ordem_servico(
                db=db, equipamento_id="Chiller_01", tipo_anomalia="anomalia_inexistente",
                severidade="baixa", detalhes="teste",
            )

    def test_todas_anomalias_mapeadas_tem_pop(self):
        for tipo, template in MAPA_ANOMALIA_PARA_OS.items():
            assert "pop_codigo" in template
