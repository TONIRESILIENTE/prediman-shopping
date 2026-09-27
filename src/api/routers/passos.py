# src/api/routers/passos.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid as uuid_lib
import os
from datetime import datetime
from src.services.verificacao_service import verificar_capacete,  verificar_luva

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

# Diretório de uploads — mesma variável usada em main.py.
# Fallback "uploads" (relativo) permite rodar sem Docker (CI, local).
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


class PassoExecucaoResponse(BaseModel):
    id: str
    numero_passo: int
    descricao: str
    concluido: bool
    foto_url: Optional[str] = None
    timestamp_conclusao: Optional[str] = None
    tipo_passo: Optional[str] = None
    validacao_ia: Optional[str] = None


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
        tipo_passo=passo.tipo_passo,
        validacao_ia=passo.validacao_ia,
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
   # Cria os passos (EPIs primeiro, depois procedimento)
    epis = getattr(pop, 'epis', None) or []
    passos = criar_passos_da_pop(
        db, ordem_id, pop.codigo, pop.passos, epis=epis
    )
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


@router.post("/verificar-capacete")
async def verificar_foto_capacete(foto: UploadFile = File(...)):
    """
    Recebe uma foto e verifica se contém capacete usando IA.
    """

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    extensao = foto.filename.split('.')[-1] if '.' in foto.filename else 'jpg'
    nome_arquivo = f"verificacao-{datetime.now().strftime('%Y%m%d%H%M%S')}.{extensao}"
    caminho = os.path.join(UPLOAD_DIR, nome_arquivo)

    conteudo = await foto.read()
    with open(caminho, "wb") as f:
        f.write(conteudo)

    resultado = verificar_capacete(caminho)
    return resultado


@router.post("/verificar-luva")
async def verificar_foto_luva(foto: UploadFile = File(...)):
    """
    Recebe uma foto e verifica se contém luva de proteção usando IA.
    """

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    extensao = foto.filename.split('.')[-1] if '.' in foto.filename else 'jpg'
    nome_arquivo = f"verificacao-luva-{datetime.now().strftime('%Y%m%d%H%M%S')}.{extensao}"
    caminho = os.path.join(UPLOAD_DIR, nome_arquivo)

    conteudo = await foto.read()
    with open(caminho, "wb") as f:
        f.write(conteudo)

    resultado = verificar_luva(caminho)
    return resultado
