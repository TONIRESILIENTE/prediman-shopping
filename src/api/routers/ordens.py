# src/api/routers/ordens.py
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.api.middleware.auth import obter_usuario_atual, exigir_papel

from src.database.connection import get_db
from src.services.ordens_service import (
    listar_ordens,
    buscar_ordem_por_id,
    atualizar_status,
)
from src.database.models import OrdemServico as OrdemServicoModel, Equipamento

router = APIRouter(prefix="/api/v1", tags=["Ordens de Serviço"])


class OrdemServicoResponse(BaseModel):
    id: str
    equipamento_id: str
    titulo: str
    descricao: str
    severidade: str
    status: str
    diagnostico_ml: Optional[str] = None
    tipo_anomalia: Optional[str] = None
    pop_codigo: Optional[str] = None
    criado_em: Optional[str] = None
    atualizado_em: Optional[str] = None
    concluido_em: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    novo_status: str


def _os_para_response(os: OrdemServicoModel, db: Session) -> OrdemServicoResponse:
    equip = db.query(Equipamento).filter(
        Equipamento.id == os.equipamento_id).first()
    equip_nome = equip.nome if equip else str(os.equipamento_id)

    return OrdemServicoResponse(
        id=str(os.id),
        equipamento_id=equip_nome,
        titulo=os.titulo,
        descricao=os.descricao,
        severidade=os.severidade,
        status=os.status,
        diagnostico_ml=os.diagnostico_ml,
        tipo_anomalia=os.diagnostico_ml,
        pop_codigo=os.pop_codigo if hasattr(os, 'pop_codigo') else None,
        criado_em=os.criado_em.isoformat() if os.criado_em else None,
        atualizado_em=os.atualizado_em.isoformat() if os.atualizado_em else None,
        concluido_em=os.concluido_em.isoformat() if os.concluido_em else None,
    )


@router.get("/ordens", response_model=List[OrdemServicoResponse])
async def listar_ordens_endpoint(
    equipamento_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    usuario: dict = Depends(obter_usuario_atual),
):
    ordens = listar_ordens(db, equipamento_id=equipamento_id, status=status)
    return [_os_para_response(os, db) for os in ordens]


@router.get("/ordens/{ordem_id}", response_model=OrdemServicoResponse)
async def buscar_ordem(ordem_id: str, db: Session = Depends(get_db), usuario: dict = Depends(obter_usuario_atual)):
    os = buscar_ordem_por_id(db, ordem_id)
    if not os:
        raise HTTPException(
            status_code=404, detail=f"OS '{ordem_id}' não encontrada.")
    return _os_para_response(os, db)


@router.patch("/ordens/{ordem_id}/status", response_model=OrdemServicoResponse)
async def atualizar_status_endpoint(ordem_id: str, body: StatusUpdateRequest, db: Session = Depends(get_db), usuario: dict = Depends(exigir_papel("tecnico", "gestor", "admin"))):
    status_permitidos = ["aberta", "em_andamento", "pausada", "concluida"]
    if body.novo_status not in status_permitidos:
        raise HTTPException(
            status_code=422, detail=f"Status inválido. Permitidos: {status_permitidos}")

    os = atualizar_status(db, ordem_id, body.novo_status)
    if not os:
        raise HTTPException(
            status_code=404, detail=f"OS '{ordem_id}' não encontrada.")

    return _os_para_response(os, db)
