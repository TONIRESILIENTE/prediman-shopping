# src/simulator/chiller.py
# ─────────────────────────────────────────────
# CONCEITO: Simulação baseada em física do equipamento.
# Um chiller real tem relações conhecidas:
# - Vibração aumenta com desgaste de rolamento
# - ΔT (diferença temperatura entrada/saída) indica eficiência
# - Corrente do compressor é proporcional à carga térmica
# ─────────────────────────────────────────────

from typing import Dict, Any
from src.simulator.base import SensorBase


class ChillerSimulator(SensorBase):
    """
    Simula sensores de um Chiller (resfriador de água).

    Sensores simulados:
    - vibracao_mm_s: vibração do compressor (mm/s RMS)
    - temp_entrada_c: temperatura da água entrando no chiller (°C)
    - temp_saida_c: temperatura da água saindo do chiller (°C)
    - corrente_a: corrente elétrica do compressor (A)

    Parâmetros nominais (baseados em chiller típico de shopping):
    - Vibração normal: 2.0-4.0 mm/s
    - ΔT normal: 4-6°C
    - Corrente: proporcional à carga (40-80A)
    """

    def __init__(self, equipamento_id: str = "Chiller_01", **kwargs):
        super().__init__(equipamento_id=equipamento_id, **kwargs)

        # Parâmetros de operação normal
        self.vibracao_base = 3.0  # mm/s RMS (típico para compressor novo)
        self.temp_entrada_base = 12.0  # °C (água retornando do shopping)
        self.delta_t_base = 5.0  # °C (diferença entrada-saída)
        self.corrente_base = 60.0  # A (carga típica)

    def gerar_leitura_normal(self) -> Dict[str, Any]:
        """
        Gera leitura normal com variação sazonal simulada.

        POR QUÊ: A carga do chiller varia com o horário e estação.
        Simulamos isso com uma senóide suave.
        """
        import math

        # Variação horária (hora do dia simulada pelo contador)
        # Carga maior no meio do dia, menor à noite
        hora_simulada = (self.contador_leituras % 24)
        fator_carga = 0.7 + 0.3 * math.sin(math.pi * hora_simulada / 24)

        # Valores normais com pequena variação aleatória
        temperatura_entrada = self.temp_entrada_base + \
            self.rng.uniform(-0.5, 0.5)
        delta_t = self.delta_t_base * fator_carga + self.rng.uniform(-0.3, 0.3)

        return {
            "vibracao_mm_s": round(self.vibracao_base + self.rng.uniform(-0.5, 0.5), 3),
            "temp_entrada_c": round(temperatura_entrada, 2),
            "temp_saida_c": round(temperatura_entrada - delta_t, 2),
            "delta_t_c": round(delta_t, 2),
            "corrente_a": round(self.corrente_base * fator_carga + self.rng.uniform(-3, 3), 2),
        }

    def injetar_anomalia(self) -> Dict[str, Any]:
        """
        Injeta anomalias típicas de chiller.

        Tipos de anomalia:
        - "desgaste_rolamento": vibração 3x acima do normal
        - "baixa_eficiencia": ΔT abaixo de 2°C (possível vazamento de gás)
        - "sobrecarga": corrente 20% acima do normal
        """
        leitura = self.gerar_leitura_normal()
        tipo = self.tipo_anomalia or "desgaste_rolamento"

        if tipo == "desgaste_rolamento":
            # POR QUÊ: Vibração de rolamento desgastado é 3-5x maior
            # que o normal. É uma assinatura clássica em manutenção preditiva.
            leitura["vibracao_mm_s"] = round(
                self.vibracao_base * self.rng.uniform(3.0, 5.0), 3)

        elif tipo == "baixa_eficiencia":
            # ΔT baixo = chiller não está trocando calor direito
            # Pode ser vazamento de gás refrigerante ou incrustação
            leitura["delta_t_c"] = round(self.rng.uniform(1.0, 2.5), 2)
            leitura["temp_saida_c"] = round(
                leitura["temp_entrada_c"] - leitura["delta_t_c"], 2)

        elif tipo == "sobrecarga":
            leitura["corrente_a"] = round(
                self.corrente_base * self.rng.uniform(1.2, 1.4), 2)

        return leitura
