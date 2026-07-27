# src/api/routers/dados.py
# ─────────────────────────────────────────────
# CONCEITO: Router do FastAPI = agrupa endpoints relacionados.
# Separar por domínio (dados, equipamentos, auth) mantém o código organizado.
# ─────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
from typing import List

from src.api.schemas.medicao import (
    MedicaoRequest,
    LoteMedicaoRequest,
    MedicaoResponse,
    LoteMedicaoResponse,
    DiagnosticoResponse,
    Severidade,
)
from src.analytics.detector import detectar_anomalia

# POR QUÊ: prefix e tags = organização automática no Swagger.
# Todos os endpoints deste router aparecem na seção "Dados".
router = APIRouter(prefix="/api/v1", tags=["Dados"])

# Simulamos um "banco" em memória para o último diagnóstico.
# No Step 5, isso será substituído pelo PostgreSQL.
ultimos_diagnosticos: dict = {}


def _diagnostico_para_response(diag, timestamp: str) -> DiagnosticoResponse:
    """Converte o Diagnostico interno para o schema de resposta."""
    return DiagnosticoResponse(
        equipamento_id=diag.equipamento_id,
        anomalia_detectada=diag.anomalia_detectada,
        tipo_anomalia=diag.tipo_anomalia,
        severidade=Severidade(diag.severidade),
        detalhes=diag.detalhes,
        regra_disparada=diag.regra_disparada,
        timestamp=timestamp,
    )


@router.post(
    "/medicao",
    response_model=MedicaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receber leitura de sensor",
    description="Recebe uma leitura de um equipamento, aplica o motor analítico e retorna o diagnóstico.",
)
async def receber_medicao(medicao: MedicaoRequest):
    """
    Endpoint principal de ingestão de dados.

    Fluxo:
    1. Valida o input (Pydantic faz isso automaticamente)
    2. Converte para o formato que o motor analítico espera
    3. Aplica as regras de engenharia
    4. Armazena o diagnóstico
    5. Retorna o resultado

    ANALOGIA: É a "portaria" do sistema — tudo que entra passa por aqui.
    """
    try:
        # Monta leitura no formato que o detector espera
        leitura = {
            "equipamento_id": medicao.equipamento_id,
            **medicao.dados,
        }

        # Aplica o motor analítico
        diag = detectar_anomalia(leitura)

        # Armazena no cache
        timestamp = datetime.now(timezone.utc).isoformat()
        ultimos_diagnosticos[medicao.equipamento_id] = {
            "diagnostico": diag,
            "timestamp": timestamp,
        }

        # NOVO: Se anomalia detectada, gera OS automaticamente
        os_criada = None
        if diag.anomalia_detectada and diag.tipo_anomalia:
            from src.services.ordens_service import criar_ordem_servico
            try:
                os_criada = criar_ordem_servico(
                    equipamento_id=medicao.equipamento_id,
                    tipo_anomalia=diag.tipo_anomalia,
                    severidade=diag.severidade,
                    detalhes=diag.detalhes,
                )
            except ValueError:
                # Tipo de anomalia não mapeado — registra mas não quebra
                pass

        resposta = MedicaoResponse(
            status="processado",
            equipamento_id=medicao.equipamento_id,
            diagnostico=_diagnostico_para_response(diag, timestamp),
            timestamp_processamento=timestamp,
        )

        # Adiciona info da OS se foi criada
        if os_criada:
            resposta.os_id = os_criada.id
            resposta.os_titulo = os_criada.titulo

        return resposta

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar leitura: {str(e)}",
        )


@router.post(
    "/medicao/lote",
    response_model=LoteMedicaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Receber lote de leituras",
    description="Recebe múltiplas leituras de uma vez e retorna todos os diagnósticos.",
)
async def receber_lote_medicoes(lote: LoteMedicaoRequest):
    """
    Processa um lote de leituras.

    POR QUÊ: Em produção, sensores enviam dados em rajada (batch).
    Um endpoint de lote reduz latência e carga na rede.
    """
    diagnosticos = []
    anomalias = 0

    for medicao in lote.medicoes:
        try:
            leitura = {
                "equipamento_id": medicao.equipamento_id,
                **medicao.dados,
            }
            diag = detectar_anomalia(leitura)

            timestamp = datetime.now(timezone.utc).isoformat()
            ultimos_diagnosticos[medicao.equipamento_id] = {
                "diagnostico": diag,
                "timestamp": timestamp,
            }

            resposta = _diagnostico_para_response(diag, timestamp)
            diagnosticos.append(resposta)

            if diag.anomalia_detectada:
                anomalias += 1

        except ValueError:
            # Leitura inválida não para o processamento do lote
            pass

    return LoteMedicaoResponse(
        status="processado",
        total_recebido=len(lote.medicoes),
        total_anomalias=anomalias,
        diagnosticos=diagnosticos,
    )


@router.get(
    "/diagnostico/{equipamento_id}",
    response_model=DiagnosticoResponse,
    summary="Consultar último diagnóstico",
    description="Retorna o último diagnóstico gerado para um equipamento específico.",
)
async def consultar_diagnostico(equipamento_id: str):
    """
    Consulta o último diagnóstico de um equipamento.

    POR QUÊ: O dashboard e o PWA precisam consultar o estado atual
    sem esperar uma nova leitura.
    """
    if equipamento_id not in ultimos_diagnosticos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum diagnóstico encontrado para '{equipamento_id}'. Envie uma leitura primeiro.",
        )

    cache = ultimos_diagnosticos[equipamento_id]
    return _diagnostico_para_response(cache["diagnostico"], cache["timestamp"])
