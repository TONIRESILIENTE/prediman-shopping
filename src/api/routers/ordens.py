# src/api/routers/ordens.py
# ─────────────────────────────────────────────
# Endpoints para consulta e gestão de Ordens de Serviço.
# ─────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from src.services.ordens_service import (
    listar_ordens,
    buscar_ordem_por_id,
    atualizar_status,
    OrdemServico,
)

router = APIRouter(prefix="/api/v1", tags=["Ordens de Serviço"])


# ─── Schemas de resposta ────────────────────

class OrdemServicoResponse(BaseModel):
    id: str
    equipamento_id: str
    titulo: str
    descricao: str
    severidade: str
    status: str
    diagnostico_ml: Optional[str]
    tipo_anomalia: Optional[str]
    pop_codigo: Optional[str]
    criado_em: str
    atualizado_em: str
    concluido_em: Optional[str]


class StatusUpdateRequest(BaseModel):
    novo_status: str


def _os_para_response(os: OrdemServico) -> OrdemServicoResponse:
    return OrdemServicoResponse(
        id=os.id,
        equipamento_id=os.equipamento_id,
        titulo=os.titulo,
        descricao=os.descricao,
        severidade=os.severidade,
        status=os.status,
        diagnostico_ml=os.diagnostico_ml,
        tipo_anomalia=os.tipo_anomalia,
        pop_codigo=os.pop_codigo,
        criado_em=os.criado_em,
        atualizado_em=os.atualizado_em,
        concluido_em=os.concluido_em,
    )


@router.get(
    "/ordens",
    response_model=List[OrdemServicoResponse],
    summary="Listar ordens de serviço",
)
async def listar_ordens_endpoint(
    equipamento_id: Optional[str] = Query(
        None, description="Filtrar por equipamento"),
    status: Optional[str] = Query(
        None, description="Filtrar por status (aberta, em_andamento, concluida)"),
):
    """Lista todas as OS com filtros opcionais."""
    ordens = listar_ordens(equipamento_id=equipamento_id, status=status)
    return [_os_para_response(os) for os in ordens]


@router.get(
    "/ordens/{ordem_id}",
    response_model=OrdemServicoResponse,
    summary="Buscar OS por ID",
)
async def buscar_ordem(ordem_id: str):
    """Retorna uma OS específica pelo ID."""
    os = buscar_ordem_por_id(ordem_id)
    if not os:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ordem de serviço '{ordem_id}' não encontrada.",
        )
    return _os_para_response(os)


@router.patch(
    "/ordens/{ordem_id}/status",
    response_model=OrdemServicoResponse,
    summary="Atualizar status da OS",
)
async def atualizar_status_endpoint(ordem_id: str, body: StatusUpdateRequest):
    """Atualiza o status de uma OS (aberta → em_andamento → concluida)."""
    status_permitidos = ["aberta", "em_andamento", "pausada", "concluida"]

    if body.novo_status not in status_permitidos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status inválido. Permitidos: {status_permitidos}",
        )

    os = atualizar_status(ordem_id, body.novo_status)
    if not os:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ordem de serviço '{ordem_id}' não encontrada.",
        )

    return _os_para_response(os)
