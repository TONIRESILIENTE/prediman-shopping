# src/api/routers/dados.py
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session

from src.api.schemas.medicao import (
    MedicaoRequest,
    LoteMedicaoRequest,
    MedicaoResponse,
    LoteMedicaoResponse,
    DiagnosticoResponse,
    Severidade,
)
from src.analytics.detector import detectar_anomalia
from src.database.connection import get_db
from src.services.ordens_service import criar_ordem_servico

router = APIRouter(prefix="/api/v1", tags=["Dados"])

# Cache em memória para último diagnóstico (leitura rápida)
ultimos_diagnosticos: dict = {}


def _diagnostico_para_response(diag, timestamp: str) -> DiagnosticoResponse:
    return DiagnosticoResponse(
        equipamento_id=diag.equipamento_id,
        anomalia_detectada=diag.anomalia_detectada,
        tipo_anomalia=diag.tipo_anomalia,
        severidade=Severidade(diag.severidade),
        detalhes=diag.detalhes,
        regra_disparada=diag.regra_disparada,
        timestamp=timestamp,
    )


@router.post("/medicao", response_model=MedicaoResponse, status_code=status.HTTP_201_CREATED)
async def receber_medicao(medicao: MedicaoRequest, db: Session = Depends(get_db)):
    try:
        leitura = {"equipamento_id": medicao.equipamento_id, **medicao.dados}
        diag = detectar_anomalia(leitura)

        timestamp = datetime.now(timezone.utc).isoformat()
        ultimos_diagnosticos[medicao.equipamento_id] = {
            "diagnostico": diag, "timestamp": timestamp}

        os_criada = None
        if diag.anomalia_detectada and diag.tipo_anomalia:
            try:
                os_criada = criar_ordem_servico(
                    db=db,
                    equipamento_id=medicao.equipamento_id,
                    tipo_anomalia=diag.tipo_anomalia,
                    severidade=diag.severidade,
                    detalhes=diag.detalhes,
                )
            except ValueError:
                pass

        resposta = MedicaoResponse(
            status="processado",
            equipamento_id=medicao.equipamento_id,
            diagnostico=_diagnostico_para_response(diag, timestamp),
            timestamp_processamento=timestamp,
        )

        if os_criada:
            resposta.os_id = str(os_criada.id)
            resposta.os_titulo = os_criada.titulo

        return resposta

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/medicao/lote", response_model=LoteMedicaoResponse, status_code=status.HTTP_201_CREATED)
async def receber_lote_medicoes(lote: LoteMedicaoRequest, db: Session = Depends(get_db)):
    diagnosticos = []
    anomalias = 0

    for medicao in lote.medicoes:
        try:
            leitura = {
                "equipamento_id": medicao.equipamento_id, **medicao.dados}
            diag = detectar_anomalia(leitura)

            timestamp = datetime.now(timezone.utc).isoformat()
            ultimos_diagnosticos[medicao.equipamento_id] = {
                "diagnostico": diag, "timestamp": timestamp}

            if diag.anomalia_detectada and diag.tipo_anomalia:
                try:
                    criar_ordem_servico(
                        db=db,
                        equipamento_id=medicao.equipamento_id,
                        tipo_anomalia=diag.tipo_anomalia,
                        severidade=diag.severidade,
                        detalhes=diag.detalhes,
                    )
                except ValueError:
                    pass

            resposta = _diagnostico_para_response(diag, timestamp)
            diagnosticos.append(resposta)
            if diag.anomalia_detectada:
                anomalias += 1
        except ValueError:
            pass

    return LoteMedicaoResponse(
        status="processado",
        total_recebido=len(lote.medicoes),
        total_anomalias=anomalias,
        diagnosticos=diagnosticos,
    )


@router.get("/diagnostico/{equipamento_id}", response_model=DiagnosticoResponse)
async def consultar_diagnostico(equipamento_id: str):
    if equipamento_id not in ultimos_diagnosticos:
        raise HTTPException(
            status_code=404, detail=f"Nenhum diagnóstico para '{equipamento_id}'.")
    cache = ultimos_diagnosticos[equipamento_id]
    return _diagnostico_para_response(cache["diagnostico"], cache["timestamp"])
