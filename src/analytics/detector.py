# src/analytics/detector.py
# ─────────────────────────────────────────────
# CONCEITO: Detector híbrido — combina regras de engenharia
# com machine learning (futuro) para diagnóstico de anomalias.
#
# Fluxo:
# 1. Recebe leitura do simulador
# 2. Identifica o tipo de equipamento
# 3. Aplica as regras de engenharia específicas
# 4. (futuro) Se regras não detectaram, consulta modelo ML
# 5. Retorna diagnóstico
# ─────────────────────────────────────────────

from typing import Dict
from src.analytics.regras import (
    Diagnostico,
    analisar_chiller,
    analisar_subestacao,
    analisar_bomba,
    analisar_iluminacao,
)


def detectar_anomalia(leitura: Dict) -> Diagnostico:
    """
    Detecta anomalias em uma leitura de sensor.

    Args:
        leitura: dict com dados do sensor (formato do simulador)

    Returns:
        Diagnostico com severidade, tipo e detalhes

    Raises:
        ValueError: se tipo de equipamento não reconhecido
    """
    equipamento_id = leitura.get("equipamento_id", "")

    # POR QUÊ: Identificar o tipo pelo nome do equipamento.
    # Em produção, isso viria do banco de dados (tabela equipamentos).
    if "Chiller" in equipamento_id:
        return analisar_chiller(leitura)

    elif "Subestacao" in equipamento_id:
        return analisar_subestacao(leitura)

    elif "Bomba" in equipamento_id:
        return analisar_bomba(leitura)

    elif "Iluminacao" in equipamento_id:
        return analisar_iluminacao(leitura)

    else:
        raise ValueError(
            f"Equipamento '{equipamento_id}' nao reconhecido. "
            f"Tipos validos: Chiller, Subestacao, Bomba, Iluminacao."
        )


def analisar_lote(leituras: list[Dict]) -> list[Diagnostico]:
    """
    Analisa um lote de leituras (vários equipamentos).

    Args:
        leituras: lista de leituras do Orchestrator

    Returns:
        Lista de Diagnosticos, um por leitura
    """
    diagnosticos = []
    for leitura in leituras:
        try:
            diag = detectar_anomalia(leitura)
            diagnosticos.append(diag)
        except ValueError as e:
            # POR QUÊ: Em produção, logaríamos o erro e continuaríamos.
            # Uma leitura inválida não pode parar o sistema.
            diagnosticos.append(
                Diagnostico(
                    equipamento_id=leitura.get(
                        "equipamento_id", "desconhecido"),
                    anomalia_detectada=False,
                    tipo_anomalia=None,
                    severidade="erro",
                    detalhes=f"Erro ao analisar: {str(e)}",
                )
            )
    return diagnosticos
