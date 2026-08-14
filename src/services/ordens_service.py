# src/services/ordens_service.py
# ─────────────────────────────────────────────
# CONCEITO: Service Layer com persistência real.
# Todas as funções recebem uma Session do SQLAlchemy
# e operam no PostgreSQL (ou SQLite nos testes).
# ─────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session

from src.database.models import (
    OrdemServico as OrdemServicoModel,
    Equipamento,
    POP as POPModel,
)


# ─── Mapeamento anomalia → OS ──────────────
# (mesmo mapeamento de antes, sem alterações)

MAPA_ANOMALIA_PARA_OS = {
    "desgaste_rolamento": {
        "titulo": "Verificar compressor — vibração anômala",
        "descricao": "Vibração acima do limite. Provável desgaste de rolamento.",
        "pop_codigo": "POP-CHL-001",
    },
    "baixa_eficiencia": {
        "titulo": "Avaliar eficiência do chiller — ΔT baixo",
        "descricao": "Delta T abaixo de 3°C. Verificar carga de gás.",
        "pop_codigo": "POP-CHL-002",
    },
    "sobrecarga": {
        "titulo": "Verificar sobrecarga no compressor",
        "descricao": "Corrente acima de 80A. Verificar carga térmica.",
        "pop_codigo": "POP-CHL-003",
    },
    "alerta_vibracao": {
        "titulo": "Monitorar tendência de vibração",
        "descricao": "Vibração acima de 5.0 mm/s. Acompanhar 48h.",
        "pop_codigo": "POP-CHL-001",
    },
    "fp_baixo": {
        "titulo": "Corrigir fator de potência — risco de multa ANEEL",
        "descricao": "FP abaixo de 0.92. Verificar banco de capacitores.",
        "pop_codigo": "POP-SUB-001",
    },
    "sobrecarga_fase": {
        "titulo": "Sobrecarga crítica na subestação",
        "descricao": "Corrente acima do limite. Balancear cargas.",
        "pop_codigo": "POP-SUB-002",
    },
    "oscilacao_tensao": {
        "titulo": "Oscilação de tensão na subestação",
        "descricao": "Tensão fora da faixa ±10%.",
        "pop_codigo": "POP-SUB-003",
    },
    "sobreaquecimento": {
        "titulo": "Sobreaquecimento nos barramentos",
        "descricao": "Temperatura acima de 70°C. Verificar conexões.",
        "pop_codigo": "POP-SUB-004",
    },
    "cavitacao": {
        "titulo": "Cavitação detectada na bomba",
        "descricao": "Vibração alta + corrente baixa.",
        "pop_codigo": "POP-BOM-001",
    },
    "obstrucao": {
        "titulo": "Possível obstrução na tubulação",
        "descricao": "Corrente alta com vibração normal.",
        "pop_codigo": "POP-BOM-002",
    },
    "poco_seco": {
        "titulo": "CRÍTICO: Poço de recalque seco",
        "descricao": "Nível abaixo do mínimo. Risco de queima.",
        "pop_codigo": "POP-BOM-003",
    },
    "vibracao_excessiva": {
        "titulo": "Vibração excessiva na bomba",
        "descricao": "Verificar alinhamento e rolamentos.",
        "pop_codigo": "POP-BOM-004",
    },
    "timer_falho": {
        "titulo": "Falha no timer/fotocélula",
        "descricao": "Circuito ligado fora do horário.",
        "pop_codigo": "POP-ILU-001",
    },
    "lampadas_queimadas": {
        "titulo": "Lâmpadas queimadas no circuito",
        "descricao": "Corrente abaixo do mínimo.",
        "pop_codigo": "POP-ILU-002",
    },
    "degradacao": {
        "titulo": "Degradação de lâmpadas",
        "descricao": "Consumo elevado. Avaliar substituição.",
        "pop_codigo": "POP-ILU-003",
    },
}


def _buscar_ou_criar_equipamento(db: Session, equipamento_id: str, tipo: str) -> Equipamento:
    """Busca equipamento pelo ID ou cria se não existir."""
    equip = db.query(Equipamento).filter(
        Equipamento.nome == equipamento_id).first()
    if not equip:
        equip = Equipamento(
            nome=equipamento_id,
            tipo=tipo,
            localizacao="Não informada",
        )
        db.add(equip)
        db.flush()  # Garante o ID sem commitar
    return equip


def criar_ordem_servico(
    db: Session,
    equipamento_id: str,
    tipo_anomalia: str,
    severidade: str,
    detalhes: str,
) -> OrdemServicoModel:
    """Cria uma OS no banco de dados."""
    template = MAPA_ANOMALIA_PARA_OS.get(tipo_anomalia)
    if template is None:
        raise ValueError(
            f"Tipo de anomalia '{tipo_anomalia}' não possui OS mapeada.")

    # Determina o tipo do equipamento pelo ID
    if "Chiller" in equipamento_id:
        tipo_eq = "chiller"
    elif "Subestacao" in equipamento_id:
        tipo_eq = "subestacao"
    elif "Bomba" in equipamento_id:
        tipo_eq = "bomba"
    elif "Iluminacao" in equipamento_id:
        tipo_eq = "iluminacao"
    else:
        tipo_eq = "chiller"

    equip = _buscar_ou_criar_equipamento(db, equipamento_id, tipo_eq)

    os = OrdemServicoModel(
        equipamento_id=equip.id,
        titulo=template["titulo"],
        descricao=f"{template['descricao']}\n\nDiagnóstico: {detalhes}",
        severidade=severidade,
        status="aberta",
        diagnostico_ml=tipo_anomalia,
        pop_codigo=template["pop_codigo"],
    )

    db.add(os)
    db.commit()
    db.refresh(os)

    return os


def listar_ordens(
    db: Session,
    equipamento_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[OrdemServicoModel]:
    """Lista ordens com filtros opcionais."""
    query = db.query(OrdemServicoModel)

    if equipamento_id:
        equip = db.query(Equipamento).filter(
            Equipamento.nome == equipamento_id).first()
        if equip:
            query = query.filter(OrdemServicoModel.equipamento_id == equip.id)
        else:
            return []

    if status:
        query = query.filter(OrdemServicoModel.status == status)

    return query.order_by(OrdemServicoModel.criado_em.desc()).all()


def buscar_ordem_por_id(db: Session, ordem_id: str) -> Optional[OrdemServicoModel]:
    """Busca OS pelo ID."""
    try:
        uid = uuid.UUID(ordem_id)
        return db.query(OrdemServicoModel).filter(OrdemServicoModel.id == uid).first()
    except ValueError:
        return None


def atualizar_status(db: Session, ordem_id: str, novo_status: str) -> Optional[OrdemServicoModel]:
    """Atualiza status da OS."""
    os = buscar_ordem_por_id(db, ordem_id)
    if os:
        os.status = novo_status
        os.atualizado_em = datetime.now(timezone.utc)
        if novo_status == "concluida":
            os.concluido_em = datetime.now(timezone.utc)
        db.commit()
        db.refresh(os)
    return os
