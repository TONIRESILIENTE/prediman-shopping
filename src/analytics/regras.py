# src/analytics/regras.py
# ─────────────────────────────────────────────
# CONCEITO: Regras de engenharia — thresholds baseados
# em normas técnicas (ANEEL, ABNT, fabricantes).
#
# São regras DETERMINÍSTICAS: se X > limite, é anomalia.
# Vantagem: não precisa de dados históricos, decisão rápida.
# Desvantagem: não detecta padrões sutis (por isso temos o ML).
# ─────────────────────────────────────────────

from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Diagnostico:
    """
    Resultado da análise de uma leitura.

    ANALOGIA: É o laudo que o analista de vibração entrega
    depois de inspecionar uma máquina.
    """
    equipamento_id: str
    anomalia_detectada: bool
    tipo_anomalia: Optional[str]
    severidade: str  # "normal", "baixa", "media", "alta", "critica"
    detalhes: str
    regra_disparada: Optional[str] = None


# ─── Limites de engenharia ──────────────────
# POR QUÊ: Cada limite tem uma FONTE (norma, fabricante, experiência).
# Documentar a fonte é essencial em sistemas industriais.

LIMITES = {
    "chiller": {
        # Fonte: fabricante Carrier — manual de manutenção
        "vibracao_max_mm_s": 7.0,       # acima disso = desgaste
        "vibracao_alerta_mm_s": 5.0,    # atenção
        # Fonte: ASHRAE Handbook — HVAC
        "delta_t_min_c": 3.0,           # abaixo = baixa eficiência
        # Fonte: placa do motor + 20% margem
        "corrente_max_a": 80.0,         # sobrecarga
    },
    "subestacao": {
        # Fonte: ANEEL — Resolução Normativa 1000/2021
        "fp_minimo": 0.92,              # abaixo = multa
        # Fonte: NBR 5410 — instalações elétricas
        "tensao_min_v": 342.0,          # -10% do nominal (380V)
        "tensao_max_v": 418.0,          # +10% do nominal
        "corrente_max_a": 300.0,        # 150% da nominal
        "temperatura_max_c": 70.0,      # barramentos
    },
    "bomba": {
        "vibracao_max_mm_s": 6.0,
        "corrente_max_a": 22.0,         # motor 10CV
        "corrente_min_a": 8.0,          # abaixo = cavitação ou vazio
        "nivel_min_m": 0.3,             # poço quase seco
    },
    "iluminacao": {
        # Fonte: projeto luminotécnico do shopping
        "corrente_max_a": 50.0,         # circuito com todas lâmpadas
        "corrente_min_a": 3.0,          # abaixo = muitas queimadas
    },
}


def analisar_chiller(leitura: Dict) -> Diagnostico:
    """
    Aplica regras de engenharia para o chiller.

    Fluxo de decisão:
    1. Vibração > 7.0 mm/s → desgaste de rolamento (severidade alta)
    2. Vibração > 5.0 mm/s → alerta de vibração (severidade média)
    3. ΔT < 3.0°C → baixa eficiência (severidade média)
    4. Corrente > 80A → sobrecarga (severidade alta)
    """
    vib = leitura.get("vibracao_mm_s", 0)
    delta_t = leitura.get("delta_t_c", 0)
    corrente = leitura.get("corrente_a", 0)
    equip = leitura.get("equipamento_id", "Chiller")

    limites = LIMITES["chiller"]

    # Verificações em ordem de criticidade
    if vib > limites["vibracao_max_mm_s"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="desgaste_rolamento",
            severidade="alta",
            detalhes=f"Vibracao {vib:.1f} mm/s acima do limite de {limites['vibracao_max_mm_s']} mm/s. "
            f"Provavel desgaste no rolamento do compressor.",
            regra_disparada="vibracao > 7.0 mm/s",
        )

    if corrente > limites["corrente_max_a"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="sobrecarga",
            severidade="alta",
            detalhes=f"Corrente {corrente:.1f}A acima do limite de {limites['corrente_max_a']}A. "
            f"Verificar carga termica ou problema eletrico.",
            regra_disparada="corrente > 80A",
        )

    if delta_t < limites["delta_t_min_c"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="baixa_eficiencia",
            severidade="media",
            detalhes=f"Delta T {delta_t:.1f}°C abaixo do minimo de {limites['delta_t_min_c']}°C. "
            f"Possivel vazamento de gas refrigerante ou incrustacao.",
            regra_disparada="delta_t < 3.0°C",
        )

    if vib > limites["vibracao_alerta_mm_s"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="alerta_vibracao",
            severidade="baixa",
            detalhes=f"Vibracao {vib:.1f} mm/s acima do alerta de {limites['vibracao_alerta_mm_s']} mm/s. "
            f"Monitorar tendencia.",
            regra_disparada="vibracao > 5.0 mm/s",
        )

    # Tudo normal
    return Diagnostico(
        equipamento_id=equip,
        anomalia_detectada=False,
        tipo_anomalia=None,
        severidade="normal",
        detalhes="Todos os parametros dentro dos limites normais.",
    )


def analisar_subestacao(leitura: Dict) -> Diagnostico:
    """Aplica regras para a subestação elétrica."""
    fp = leitura.get("fator_potencia", 1.0)
    tensao = leitura.get("tensao_v", 380)
    corrente = leitura.get("corrente_a", 0)
    temp = leitura.get("temperatura_c", 0)
    equip = leitura.get("equipamento_id", "Subestacao")

    limites = LIMITES["subestacao"]

    if fp < limites["fp_minimo"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="fp_baixo",
            severidade="alta",
            detalhes=f"Fator de potencia {fp:.3f} abaixo do minimo de {limites['fp_minimo']} (ANEEL). "
            f"Risco de multa na fatura. Verificar banco de capacitores.",
            regra_disparada=f"FP < {limites['fp_minimo']}",
        )

    if corrente > limites["corrente_max_a"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="sobrecarga_fase",
            severidade="critica",
            detalhes=f"Corrente {corrente:.0f}A acima do limite de {limites['corrente_max_a']}A. "
            f"Risco de aquecimento e incendio!",
            regra_disparada=f"corrente > {limites['corrente_max_a']}A",
        )

    if tensao < limites["tensao_min_v"] or tensao > limites["tensao_max_v"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="oscilacao_tensao",
            severidade="alta",
            detalhes=f"Tensao {tensao:.0f}V fora da faixa {limites['tensao_min_v']}-{limites['tensao_max_v']}V.",
            regra_disparada="tensao fora da faixa ±10%",
        )

    if temp > limites["temperatura_max_c"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="sobreaquecimento",
            severidade="alta",
            detalhes=f"Temperatura dos barramentos {temp:.0f}°C acima do limite de {limites['temperatura_max_c']}°C.",
            regra_disparada=f"temperatura > {limites['temperatura_max_c']}°C",
        )

    return Diagnostico(
        equipamento_id=equip,
        anomalia_detectada=False,
        tipo_anomalia=None,
        severidade="normal",
        detalhes="Parametros eletricos normais.",
    )


def analisar_bomba(leitura: Dict) -> Diagnostico:
    """Aplica regras para a bomba de recalque."""
    vib = leitura.get("vibracao_mm_s", 0)
    corrente = leitura.get("corrente_a", 0)
    nivel = leitura.get("nivel_poco_m", 99)
    status = leitura.get("status_bomba", "desligada")
    equip = leitura.get("equipamento_id", "Bomba")

    limites = LIMITES["bomba"]

    if status == "desligada":
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=False,
            tipo_anomalia=None,
            severidade="normal",
            detalhes="Bomba desligada — ciclo normal.",
        )

    if nivel < limites["nivel_min_m"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="poco_seco",
            severidade="critica",
            detalhes=f"Nivel do poco {nivel:.2f}m abaixo do minimo de {limites['nivel_min_m']}m. "
            f"Risco de cavitacao e queima da bomba!",
            regra_disparada=f"nivel < {limites['nivel_min_m']}m",
        )

    # Cavitação: vibração alta + corrente baixa
    if vib > limites["vibracao_max_mm_s"] and corrente < limites["corrente_min_a"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="cavitacao",
            severidade="alta",
            detalhes=f"Vibracao alta ({vib:.1f} mm/s) + corrente baixa ({corrente:.1f}A) = "
            f"assinatura classica de cavitacao.",
            regra_disparada="vibracao alta + corrente baixa",
        )

    # Obstrução: corrente alta + vibração normal
    if corrente > limites["corrente_max_a"] and vib < limites["vibracao_max_mm_s"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="obstrucao",
            severidade="media",
            detalhes=f"Corrente alta ({corrente:.1f}A) com vibracao normal = "
            f"possivel obstrucao na tubulacao.",
            regra_disparada=f"corrente > {limites['corrente_max_a']}A",
        )

    if vib > limites["vibracao_max_mm_s"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="vibracao_excessiva",
            severidade="media",
            detalhes=f"Vibracao {vib:.1f} mm/s acima do limite de {limites['vibracao_max_mm_s']} mm/s.",
            regra_disparada=f"vibracao > {limites['vibracao_max_mm_s']} mm/s",
        )

    return Diagnostico(
        equipamento_id=equip,
        anomalia_detectada=False,
        tipo_anomalia=None,
        severidade="normal",
        detalhes="Bomba operando normalmente.",
    )


def analisar_iluminacao(leitura: Dict) -> Diagnostico:
    """Aplica regras para circuitos de iluminação."""
    corrente = leitura.get("corrente_a", 0)
    estado = leitura.get("estado", "")
    hora = leitura.get("hora_simulada", 12)
    equip = leitura.get("equipamento_id", "Iluminacao")

    limites = LIMITES["iluminacao"]

    # Timer falho: luzes acesas fora do horário
    if estado == "ligado_fora_horario":
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="timer_falho",
            severidade="media",
            detalhes=f"Circuito ligado as {hora:.0f}h — fora do horario programado. "
            f"Verificar timer ou fotocelula.",
            regra_disparada="circuito ligado fora do horario",
        )

    # Lâmpadas queimadas: corrente muito baixa
    if corrente < limites["corrente_min_a"] and estado != "desligado":
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="lampadas_queimadas",
            severidade="baixa",
            detalhes=f"Corrente {corrente:.1f}A abaixo do minimo de {limites['corrente_min_a']}A. "
            f"Provaveis lampadas queimadas no circuito.",
            regra_disparada=f"corrente < {limites['corrente_min_a']}A",
        )

    # Degradação: corrente alta (lâmpadas velhas consomem mais)
    if corrente > limites["corrente_max_a"]:
        return Diagnostico(
            equipamento_id=equip,
            anomalia_detectada=True,
            tipo_anomalia="degradacao",
            severidade="baixa",
            detalhes=f"Corrente {corrente:.1f}A acima do esperado. "
            f"Possivel degradacao das lampadas — consumindo mais energia.",
            regra_disparada=f"corrente > {limites['corrente_max_a']}A",
        )

    return Diagnostico(
        equipamento_id=equip,
        anomalia_detectada=False,
        tipo_anomalia=None,
        severidade="normal",
        detalhes="Iluminacao operando normalmente.",
    )
