# src/simulator/subestacao.py
# ─────────────────────────────────────────────
# Simula sensores da subestação elétrica principal.
#
# Parâmetros monitorados:
# - tensao_v: tensão entre fases (V) — nominal 380V
# - corrente_a: corrente por fase (A)
# - fator_potencia: FP (0 a 1) — limite ANEEL: 0.92
# - temperatura_c: temperatura dos barramentos (°C)
# ─────────────────────────────────────────────

from typing import Dict, Any
from src.simulator.base import SensorBase


class SubestacaoSimulator(SensorBase):
    """
    Simula a subestação elétrica do shopping.

    Limites regulatórios (ANEEL):
    - Fator de potência mínimo: 0.92 (indutivo)
    - Abaixo disso: multa na fatura de energia

    ANALOGIA: A subestação é o "coração elétrico" do shopping.
    Se ela para, TUDO para.
    """

    def __init__(self, equipamento_id: str = "Subestacao_Principal", **kwargs):
        super().__init__(equipamento_id=equipamento_id, **kwargs)

        self.tensao_nominal = 380.0  # V
        self.corrente_base = 200.0  # A (carga típica do shopping)
        self.fp_base = 0.95  # dentro do limite ANEEL
        self.temperatura_base = 45.0  # °C (barramentos)

    def gerar_leitura_normal(self) -> Dict[str, Any]:
        import math

        # Variação de carga ao longo do dia
        hora = (self.contador_leituras % 24)
        fator_carga = 0.6 + 0.4 * \
            math.sin(math.pi * (hora - 6) / 12 if 6 <= hora <= 18 else 0)

        return {
            "tensao_v": round(self.tensao_nominal + self.rng.uniform(-5, 5), 1),
            "corrente_a": round(self.corrente_base * fator_carga + self.rng.uniform(-10, 10), 1),
            "fator_potencia": round(self.fp_base + self.rng.uniform(-0.02, 0.01), 3),
            "temperatura_c": round(self.temperatura_base + self.rng.uniform(-3, 3), 1),
        }

    def injetar_anomalia(self) -> Dict[str, Any]:
        leitura = self.gerar_leitura_normal()
        tipo = self.tipo_anomalia or "fp_baixo"

        if tipo == "fp_baixo":
            # Fator de potência abaixo de 0.92 → multa ANEEL
            leitura["fator_potencia"] = round(self.rng.uniform(0.80, 0.91), 3)

        elif tipo == "sobrecarga_fase":
            # Uma fase com corrente muito acima das outras
            leitura["corrente_a"] = round(
                self.corrente_base * self.rng.uniform(1.3, 1.5), 1)
            leitura["temperatura_c"] = round(
                self.temperatura_base + self.rng.uniform(10, 20), 1)

        elif tipo == "oscilacao_tensao":
            leitura["tensao_v"] = round(
                self.tensao_nominal * self.rng.uniform(0.85, 0.90), 1)

        return leitura
