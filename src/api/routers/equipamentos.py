# src/api/routers/equipamentos.py
# ─────────────────────────────────────────────
# Rotas para consulta de equipamentos monitorados.
# ─────────────────────────────────────────────

from fastapi import APIRouter, Depends
from typing import List
from src.api.schemas.medicao import EquipamentoResponse
from src.api.middleware.auth import obter_usuario_atual

router = APIRouter(prefix="/api/v1", tags=["Equipamentos"])

# POR QUÊ: Por enquanto, lista fixa. No Step 5, vem do banco de dados.
EQUIPAMENTOS_CADASTRO = [
    {
        "id": "Chiller_01",
        "nome": "Chiller Principal",
        "tipo": "chiller",
        "localizacao": "Cobertura — Casa de Máquinas 2",
        "ativo": True,
    },
    {
        "id": "Subestacao_Principal",
        "nome": "Subestação Principal",
        "tipo": "subestacao",
        "localizacao": "Subsolo 1 — Sala Elétrica",
        "ativo": True,
    },
    {
        "id": "Bomba_Recalque_G1",
        "nome": "Bomba de Recalque Garagem G1",
        "tipo": "bomba",
        "localizacao": "Subsolo 2 — Poço de Recalque",
        "ativo": True,
    },
    {
        "id": "Iluminacao_Praca_Alimentacao",
        "nome": "Iluminação Praça de Alimentação",
        "tipo": "iluminacao",
        "localizacao": "Piso Térreo — QDL-03",
        "ativo": True,
    },
    {
        "id": "Iluminacao_Estacionamento_G1",
        "nome": "Iluminação Estacionamento G1",
        "tipo": "iluminacao",
        "localizacao": "Subsolo 1 — QDL-05",
        "ativo": True,
    },
    {
        "id": "Iluminacao_Fachada",
        "nome": "Iluminação Fachada",
        "tipo": "iluminacao",
        "localizacao": "Área Externa — QDL-07",
        "ativo": True,
    },
]


@router.get(
    "/equipamentos",
    response_model=List[EquipamentoResponse],
    summary="Listar equipamentos",
    description="Retorna a lista de todos os equipamentos monitorados pelo sistema.",
)
async def listar_equipamentos():
    """Retorna todos os equipamentos cadastrados."""
    return [EquipamentoResponse(**eq) for eq in EQUIPAMENTOS_CADASTRO]
