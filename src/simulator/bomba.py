# src/simulator/bomba.py
# ─────────────────────────────────────────────
# Simula sensores da bomba de recalque.
#
# Bombas de recalque: jogam água do poço para a rede.
# Críticas em shoppings com garagem subterrânea.
# ─────────────────────────────────────────────

from typing import Dict, Any
from src.simulator.base import SensorBase


class BombaSimulator(SensorBase):
    """
    Simula bomba de recalque do poço da garagem.

    Sensores:
    - vibracao_mm_s: vibração do motor (mm/s)
    - corrente_a: corrente do motor (A)
    - nivel_poco_m: nível de água no poço (m) — 0 = seco
    - status_bomba: "ligada" ou "desligada"
    """

    def __init__(self, equipamento_id: str = "Bomba_Recalque_G1", **kwargs):
        super().__init__(equipamento_id=equipamento_id, **kwargs)

        self.vibracao_base = 2.5  # mm/s
        self.corrente_base = 15.0  # A (motor trifásico 10CV)
        self.nivel_base = 2.0  # metros (poço com água)

    def gerar_leitura_normal(self) -> Dict[str, Any]:
        # Simula ciclo de liga/desliga da bomba
        ciclo = self.contador_leituras % 20
        bomba_ligada = ciclo < 12  # 60% do tempo ligada

        if bomba_ligada:
            return {
                "vibracao_mm_s": round(self.vibracao_base + self.rng.uniform(-0.3, 0.3), 3),
                "corrente_a": round(self.corrente_base + self.rng.uniform(-1, 1), 2),
                "nivel_poco_m": round(self.nivel_base + self.rng.uniform(-0.5, 0.5), 2),
                "status_bomba": "ligada",
            }
        else:
            # Bomba desligada: nível sobe (enchendo)
            return {
                "vibracao_mm_s": 0.0,
                "corrente_a": 0.0,
                "nivel_poco_m": round(self.nivel_base + self.rng.uniform(1.0, 2.0), 2),
                "status_bomba": "desligada",
            }

    def injetar_anomalia(self) -> Dict[str, Any]:
        leitura = self.gerar_leitura_normal()
        tipo = self.tipo_anomalia or "cavitacao"

        if tipo == "cavitacao":
            # Cavitação: vibração alta + corrente baixa
            # (bolhas de ar colapsam e causam vibração)
            leitura["vibracao_mm_s"] = round(
                self.vibracao_base * self.rng.uniform(3, 5), 3)
            leitura["corrente_a"] = round(
                self.corrente_base * self.rng.uniform(0.5, 0.7), 2)
            leitura["status_bomba"] = "ligada"

        elif tipo == "obstrucao":
            # Obstrução na tubulação: corrente alta + vibração normal
            leitura["corrente_a"] = round(
                self.corrente_base * self.rng.uniform(1.3, 1.6), 2)
            leitura["status_bomba"] = "ligada"

        elif tipo == "poco_seco":
            # Poço seco: bomba ligada mas sem água
            leitura["nivel_poco_m"] = round(self.rng.uniform(0.0, 0.2), 2)
            leitura["corrente_a"] = round(
                self.corrente_base * self.rng.uniform(0.3, 0.5), 2)
            leitura["vibracao_mm_s"] = round(self.vibracao_base * 2, 3)
            leitura["status_bomba"] = "ligada"

        return leitura
