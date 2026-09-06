# src/api/routers/passos.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid as uuid_lib
import os
from datetime import datetime

from src.database.connection import get_db
from src.services.passos_service import (
    criar_passos_da_pop,
    listar_passos_da_os,
    marcar_passo_concluido,
    calcular_progresso,
    os_pode_ser_concluida,
)
from src.services.ordens_service import buscar_ordem_por_id
from src.services.pops_service import buscar_pop

router = APIRouter(prefix="/api/v1", tags=["Execução de POP"])


class PassoExecucaoResponse(BaseModel):
    id: str
    numero_passo: int
    descricao: str
    concluido: bool
    foto_url: Optional[str] = None
    timestamp_conclusao: Optional[str] = None


class MarcarPassoRequest(BaseModel):
    foto_url: Optional[str] = None


class ProgressoResponse(BaseModel):
    total: int
    concluidos: int
    percentual: float


def _passo_para_response(passo) -> PassoExecucaoResponse:
    return PassoExecucaoResponse(
        id=str(passo.id),
        numero_passo=passo.numero_passo,
        descricao=passo.descricao,
        concluido=passo.concluido,
        foto_url=passo.foto_url,
        timestamp_conclusao=passo.timestamp_conclusao.isoformat(
        ) if passo.timestamp_conclusao else None,
    )


@router.get("/os/{ordem_id}/passos", response_model=List[PassoExecucaoResponse])
async def listar_passos(ordem_id: str, db: Session = Depends(get_db)):
    """Lista os passos de execução de uma OS."""
    passos = listar_passos_da_os(db, ordem_id)
    return [_passo_para_response(p) for p in passos]


@router.post("/os/{ordem_id}/passos/gerar")
async def gerar_passos(ordem_id: str, db: Session = Depends(get_db)):
    """Gera os passos a partir da POP vinculada à OS."""
    # Busca a OS
    os = buscar_ordem_por_id(db, ordem_id)
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")

    # Busca o POP pelo código
    pop = buscar_pop(os.pop_codigo) if hasattr(
        os, 'pop_codigo') and os.pop_codigo else None
    if not pop:
        raise HTTPException(status_code=400, detail="OS não tem POP vinculado")

    # Cria os passos
    passos = criar_passos_da_pop(db, ordem_id, pop.codigo, pop.passos)
    return {"mensagem": f"{len(passos)} passos criados"}


@router.patch("/passos/{passo_id}", response_model=PassoExecucaoResponse)
async def marcar_passo(passo_id: str, body: MarcarPassoRequest, db: Session = Depends(get_db)):
    """Marca um passo como concluído."""
    passo = marcar_passo_concluido(db, passo_id, body.foto_url)
    if not passo:
        raise HTTPException(status_code=404, detail="Passo não encontrado")
    return _passo_para_response(passo)


@router.get("/os/{ordem_id}/progresso", response_model=ProgressoResponse)
async def progresso(ordem_id: str, db: Session = Depends(get_db)):
    """Retorna o progresso de conclusão da OS."""
    return calcular_progresso(db, ordem_id)


@router.post("/passos/{passo_id}/foto")
async def upload_foto_passos(passo_id: str, foto: UploadFile = File(...)):
    """
    Recebe uma foto do celular e salva na pasta uploads/.
    """
    # Cria a pasta se não existir
    UPLOAD_DIR = "/app/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Gera nome único para a foto
    extensao = foto.filename.split('.')[-1] if '.' in foto.filename else 'jpg'
    nome_arquivo = f"{passo_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}.{extensao}"
    caminho_completo = os.path.join(UPLOAD_DIR, nome_arquivo)

    # Salva a foto
    conteudo = await foto.read()
    with open(caminho_completo, "wb") as f:
        f.write(conteudo)

    # Retorna a URL relativa
    return {"foto_url": f"/uploads/{nome_arquivo}"}
