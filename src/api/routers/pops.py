# src/api/routers/pops.py
# ─────────────────────────────────────────────
# Endpoints para consulta de POPs.
# ─────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from src.api.middleware.auth import obter_usuario_atual


from src.services.pops_service import buscar_pop, listar_pops, POP

router = APIRouter(prefix="/api/v1", tags=["POPs"])


class POPResponse(BaseModel):
    codigo: str
    titulo: str
    equipamento_tipo: str
    tempo_estimado_minutos: int
    epis: list
    ferramentas: list
    passos: list
    riscos: list
    observacoes: str


def _pop_para_response(pop: POP) -> POPResponse:
    return POPResponse(
        codigo=pop.codigo,
        titulo=pop.titulo,
        equipamento_tipo=pop.equipamento_tipo,
        tempo_estimado_minutos=pop.tempo_estimado_minutos,
        epis=pop.epis,
        ferramentas=pop.ferramentas,
        passos=pop.passos,
        riscos=pop.riscos,
        observacoes=pop.observacoes,
    )


@router.get(
    "/pops",
    response_model=List[POPResponse],
    summary="Listar POPs",
    description="Lista todos os POPs, opcionalmente filtrados por tipo de equipamento.",
)
async def listar_pops_endpoint(
    equipamento_tipo: Optional[str] = Query(
        None,
        description="Filtrar por tipo: chiller, subestacao, bomba, iluminacao",
    ),

):
    pops = listar_pops(equipamento_tipo=equipamento_tipo)
    return [_pop_para_response(p) for p in pops]


@router.get(
    "/pops/{codigo}",
    response_model=POPResponse,
    summary="Buscar POP por código",
    description="Retorna o POP completo (passos, EPIs, ferramentas, riscos) pelo código.",
)
async def buscar_pop_endpoint(codigo: str):
    pop = buscar_pop(codigo)
    if not pop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"POP '{codigo}' não encontrado. Use GET /pops para listar todos.",
        )
    return _pop_para_response(pop)
