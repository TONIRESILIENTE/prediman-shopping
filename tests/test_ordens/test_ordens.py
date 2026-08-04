# tests/test_ordens/test_ordens.py
"""Testes do serviço de Ordens de Serviço com SQLite."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from src.services.ordens_service import (
    criar_ordem_servico,
    listar_ordens,
    buscar_ordem_por_id,
    atualizar_status,
    MAPA_ANOMALIA_PARA_OS,
)


@pytest.fixture
def db():
    """Cria banco SQLite em memória para testes."""
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestCriarOrdemServico:
    def test_deve_criar_os_para_anomalia_mapeada(self, db):
        os = criar_ordem_servico(
            db=db,
            equipamento_id="Chiller_01",
            tipo_anomalia="desgaste_rolamento",
            severidade="alta",
            detalhes="Vibracao 9.5 mm/s",
        )
        assert os.titulo == "Verificar compressor — vibração anômala"
        assert os.severidade == "alta"
        assert os.status == "aberta"

    def test_deve_lancar_erro_para_anomalia_nao_mapeada(self, db):
        with pytest.raises(ValueError, match="não possui OS mapeada"):
            criar_ordem_servico(
                db=db,
                equipamento_id="Chiller_01",
                tipo_anomalia="anomalia_inexistente",
                severidade="baixa",
                detalhes="teste",
            )

    def test_cada_os_tem_id_unico(self, db):
        os1 = criar_ordem_servico(
            db, "Chiller_01", "desgaste_rolamento", "alta", "t1")
        os2 = criar_ordem_servico(
            db, "Chiller_01", "baixa_eficiencia", "media", "t2")
        assert os1.id != os2.id

    def test_todas_anomalias_mapeadas_tem_pop(self, db):
        for tipo, template in MAPA_ANOMALIA_PARA_OS.items():
            assert "pop_codigo" in template, f"'{tipo}' sem pop_codigo"


class TestListarOrdens:
    def test_deve_listar_todas_ordens(self, db):
        criar_ordem_servico(
            db, "Chiller_01", "desgaste_rolamento", "alta", "t1")
        criar_ordem_servico(db, "Bomba_Recalque_G1", "cavitacao", "alta", "t2")
        ordens = listar_ordens(db)
        assert len(ordens) == 2

    def test_deve_filtrar_por_equipamento(self, db):
        criar_ordem_servico(
            db, "Chiller_01", "desgaste_rolamento", "alta", "t1")
        criar_ordem_servico(db, "Bomba_Recalque_G1", "cavitacao", "alta", "t2")
        ordens = listar_ordens(db, equipamento_id="Chiller_01")
        assert len(ordens) == 1

    def test_deve_filtrar_por_status(self, db):
        os = criar_ordem_servico(
            db, "Chiller_01", "desgaste_rolamento", "alta", "t1")
        atualizar_status(db, str(os.id), "concluida")
        abertas = listar_ordens(db, status="aberta")
        concluidas = listar_ordens(db, status="concluida")
        assert len(concluidas) == 1


class TestAtualizarStatus:
    def test_deve_atualizar_status(self, db):
        os = criar_ordem_servico(
            db, "Chiller_01", "desgaste_rolamento", "alta", "t1")
        atualizado = atualizar_status(db, str(os.id), "em_andamento")
        assert atualizado.status == "em_andamento"

    def test_deve_registrar_conclusao(self, db):
        os = criar_ordem_servico(
            db, "Chiller_01", "desgaste_rolamento", "alta", "t1")
        atualizado = atualizar_status(db, str(os.id), "concluida")
        assert atualizado.status == "concluida"
        assert atualizado.concluido_em is not None

    def test_deve_retornar_none_para_id_inexistente(self, db):
        resultado = atualizar_status(
            db, "00000000-0000-0000-0000-000000000000", "concluida")
        assert resultado is None
