# src/services/ordens_service.py
# ─────────────────────────────────────────────
# CONCEITO: Service Layer — camada de lógica de negócio.
#
# Separar a lógica de criação de OS dos routers (API)
# permite reutilizar o código em qualquer lugar
# (API, CLI, testes, scripts).
#
# ANALOGIA: É o "encarregado da manutenção" que recebe
# o diagnóstico e preenche a OS. A API é só o "balcão
# de atendimento" que recebe o chamado.
# ─────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List
from dataclasses import dataclass, field


@dataclass
class OrdemServico:
    """
    Representa uma Ordem de Serviço no sistema.

    Por enquanto é um dataclass em memória.
    No Step 5B (futuro), migraremos para o banco PostgreSQL.
    """
    id: str
    equipamento_id: str
    titulo: str
    descricao: str
    severidade: str
    status: str
    diagnostico_ml: Optional[str]
    tipo_anomalia: Optional[str]
    pop_codigo: Optional[str]  # Será vinculado no Step 6
    criado_em: str
    atualizado_em: str
    concluido_em: Optional[str] = None


# "Banco de dados" em memória (será substituído por PostgreSQL)
_ordens_servico: Dict[str, OrdemServico] = {}


# ─── Mapeamento: anomalia → OS ──────────────
# POR QUÊ: Cada tipo de anomalia gera uma OS
# com título e descrição específicos.
# Isso será expandido no Step 6 com os POPs.

MAPA_ANOMALIA_PARA_OS = {
    # Chiller
    "desgaste_rolamento": {
        "titulo": "Verificar compressor — vibração anômala",
        "descricao": "Vibração acima do limite de 7.0 mm/s detectada no compressor. "
        "Provável desgaste de rolamento. Inspecionar e programar substituição.",
        "pop_codigo": "POP-CHL-001",
    },
    "baixa_eficiencia": {
        "titulo": "Avaliar eficiência do chiller — ΔT baixo",
        "descricao": "Delta T abaixo de 3°C indica baixa troca térmica. "
        "Verificar carga de gás refrigerante e limpeza dos trocadores.",
        "pop_codigo": "POP-CHL-002",
    },
    "sobrecarga": {
        "titulo": "Verificar sobrecarga no compressor",
        "descricao": "Corrente elétrica acima do limite de 80A. "
        "Verificar carga térmica excessiva ou problema elétrico.",
        "pop_codigo": "POP-CHL-003",
    },
    "alerta_vibracao": {
        "titulo": "Monitorar tendência de vibração",
        "descricao": "Vibração acima de 5.0 mm/s — abaixo do crítico mas acima do normal. "
        "Acompanhar tendência nas próximas 48h.",
        "pop_codigo": "POP-CHL-001",
    },
    # Subestação
    "fp_baixo": {
        "titulo": "Corrigir fator de potência — risco de multa ANEEL",
        "descricao": "Fator de potência abaixo de 0.92. "
        "Verificar e ajustar banco de capacitores.",
        "pop_codigo": "POP-SUB-001",
    },
    "sobrecarga_fase": {
        "titulo": "Sobrecarga crítica na subestação",
        "descricao": "Corrente acima do limite máximo. Risco de aquecimento e incêndio. "
        "Balancear cargas entre fases imediatamente.",
        "pop_codigo": "POP-SUB-002",
    },
    "oscilacao_tensao": {
        "titulo": "Oscilação de tensão na subestação",
        "descricao": "Tensão fora da faixa permitida (±10% de 380V). "
        "Verificar regulador de tensão e conexões.",
        "pop_codigo": "POP-SUB-003",
    },
    "sobreaquecimento": {
        "titulo": "Sobreaquecimento nos barramentos",
        "descricao": "Temperatura dos barramentos acima do limite de 70°C. "
        "Verificar conexões e ventilação.",
        "pop_codigo": "POP-SUB-004",
    },
    # Bomba
    "cavitacao": {
        "titulo": "Cavitação detectada na bomba de recalque",
        "descricao": "Assinatura clássica de cavitação: vibração alta + corrente baixa. "
        "Verificar nível do poço, folga do rotor e tubulação de sucção.",
        "pop_codigo": "POP-BOM-001",
    },
    "obstrucao": {
        "titulo": "Possível obstrução na tubulação",
        "descricao": "Corrente alta com vibração normal indica obstrução. "
        "Verificar filtros, válvulas e tubulação.",
        "pop_codigo": "POP-BOM-002",
    },
    "poco_seco": {
        "titulo": "CRÍTICO: Poço de recalque seco",
        "descricao": "Nível do poço abaixo do mínimo. Risco de queima da bomba. "
        "Verificar abastecimento do poço e desligar bomba se necessário.",
        "pop_codigo": "POP-BOM-003",
    },
    "vibracao_excessiva": {
        "titulo": "Vibração excessiva na bomba",
        "descricao": "Vibração acima do limite. Verificar alinhamento, base e rolamentos.",
        "pop_codigo": "POP-BOM-004",
    },
    # Iluminação
    "timer_falho": {
        "titulo": "Falha no timer/fotocélula — luzes fora do horário",
        "descricao": "Circuito de iluminação ligado fora do horário programado. "
        "Verificar timer, fotocélula ou contator.",
        "pop_codigo": "POP-ILU-001",
    },
    "lampadas_queimadas": {
        "titulo": "Lâmpadas queimadas no circuito",
        "descricao": "Corrente abaixo do mínimo esperado. Prováveis lâmpadas queimadas. "
        "Substituir e verificar causa se recorrrente.",
        "pop_codigo": "POP-ILU-002",
    },
    "degradacao": {
        "titulo": "Degradação de lâmpadas — consumo elevado",
        "descricao": "Corrente acima do esperado para o mesmo nível de iluminação. "
        "Lâmpadas antigas consumindo mais energia. Avaliar substituição.",
        "pop_codigo": "POP-ILU-003",
    },
}


def criar_ordem_servico(
    equipamento_id: str,
    tipo_anomalia: str,
    severidade: str,
    detalhes: str,
) -> OrdemServico:
    """
    Cria uma OS automaticamente a partir de um diagnóstico.

    Args:
        equipamento_id: identificador do equipamento
        tipo_anomalia: tipo da anomalia detectada
        severidade: severidade (normal, baixa, media, alta, critica)
        detalhes: detalhes do diagnóstico

    Returns:
        OrdemServico criada

    Raises:
        ValueError: se tipo_anomalia não for mapeado
    """
    # Busca o template de OS para este tipo de anomalia
    template = MAPA_ANOMALIA_PARA_OS.get(tipo_anomalia)

    if template is None:
        raise ValueError(
            f"Tipo de anomalia '{tipo_anomalia}' não possui OS mapeada. "
            f"Anomalias disponíveis: {list(MAPA_ANOMALIA_PARA_OS.keys())}"
        )

    # Cria a OS
    os = OrdemServico(
        id=str(uuid.uuid4()),
        equipamento_id=equipamento_id,
        titulo=template["titulo"],
        descricao=f"{template['descricao']}\n\nDiagnóstico: {detalhes}",
        severidade=severidade,
        status="aberta",
        diagnostico_ml=tipo_anomalia,
        tipo_anomalia=tipo_anomalia,
        pop_codigo=template["pop_codigo"],
        criado_em=datetime.now(timezone.utc).isoformat(),
        atualizado_em=datetime.now(timezone.utc).isoformat(),
    )

    # Armazena no "banco"
    _ordens_servico[os.id] = os

    return os


def listar_ordens(
    equipamento_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[OrdemServico]:
    """
    Lista ordens de serviço com filtros opcionais.

    Args:
        equipamento_id: filtrar por equipamento (opcional)
        status: filtrar por status (aberta, concluida, etc.)

    Returns:
        Lista de ordens de serviço
    """
    resultado = list(_ordens_servico.values())

    if equipamento_id:
        resultado = [
            os for os in resultado
            if os.equipamento_id == equipamento_id
        ]

    if status:
        resultado = [
            os for os in resultado
            if os.status == status
        ]

    # Mais recentes primeiro
    resultado.sort(key=lambda os: os.criado_em, reverse=True)
    return resultado


def buscar_ordem_por_id(ordem_id: str) -> Optional[OrdemServico]:
    """Busca uma OS pelo ID."""
    return _ordens_servico.get(ordem_id)


def atualizar_status(ordem_id: str, novo_status: str) -> Optional[OrdemServico]:
    """Atualiza o status de uma OS."""
    os = _ordens_servico.get(ordem_id)
    if os:
        os.status = novo_status
        os.atualizado_em = datetime.now(timezone.utc).isoformat()
        if novo_status == "concluida":
            os.concluido_em = datetime.now(timezone.utc).isoformat()
    return os
