# src/services/passos_service.py
"""
Serviço para gerenciar execução de passos da POP.

Conceito: Cada OS tem uma lista de passos.
O técnico executa cada passo, anexa uma foto 
e só então pode concluir a OS.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.models import PassoExecucao, OrdemServico


def criar_passos_da_pop(db: Session, ordem_servico_id: str, pop_codigo: str, passos: List[str]) -> List[PassoExecucao]:
    """
    Cria os passos de execução quando a OS é aberta.
    Cada passo da POP vira um PassoExecucao no banco.
    """
    criados = []
    for i, descricao in enumerate(passos, 1):
        passo = PassoExecucao(
            ordem_servico_id=uuid.UUID(ordem_servico_id) if isinstance(
                ordem_servico_id, str) else ordem_servico_id,
            pop_codigo=pop_codigo,
            numero_passo=i,
            descricao=descricao,
            concluido=False,
        )
        db.add(passo)
        criados.append(passo)

    db.commit()
    return criados


def listar_passos_da_os(db: Session, ordem_servico_id: str) -> List[PassoExecucao]:
    """Lista todos os passos de uma OS."""
    try:
        uid = uuid.UUID(ordem_servico_id) if isinstance(
            ordem_servico_id, str) else ordem_servico_id
    except ValueError:
        return []
    return db.query(PassoExecucao).filter(PassoExecucao.ordem_servico_id == uid).order_by(PassoExecucao.numero_passo).all()


def marcar_passo_concluido(db: Session, passo_id: str, foto_url: Optional[str] = None) -> Optional[PassoExecucao]:
    """Marca um passo como concluído e anexa foto."""
    try:
        uid = uuid.UUID(passo_id)
    except ValueError:
        return None

    passo = db.query(PassoExecucao).filter(PassoExecucao.id == uid).first()
    if not passo:
        return None

    passo.concluido = True
    passo.foto_url = foto_url
    passo.timestamp_conclusao = datetime.now(timezone.utc)
    db.commit()
    db.refresh(passo)
    return passo


def calcular_progresso(db: Session, ordem_servico_id: str) -> dict:
    """Calcula o percentual de conclusão da OS."""
    passos = listar_passos_da_os(db, ordem_servico_id)

    if not passos:
        return {"total": 0, "concluidos": 0, "percentual": 0.0}

    total = len(passos)
    concluidos = len([p for p in passos if p.concluido])
    percentual = round((concluidos / total) * 100, 1)

    return {
        "total": total,
        "concluidos": concluidos,
        "percentual": percentual,
    }


def os_pode_ser_concluida(db: Session, ordem_servico_id: str) -> bool:
    """Verifica se TODOS os passos estão concluídos."""
    progresso = calcular_progresso(db, ordem_servico_id)
    return progresso["percentual"] == 100.0
