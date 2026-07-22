# src/simulator/iluminacao.py
# ─────────────────────────────────────────────
# Simula circuitos de iluminação do shopping.
#
# Monitoramos:
# - corrente por circuito (A)
# - estado (ligado/desligado)
# - consumo estimado (kWh)
# ─────────────────────────────────────────────

from typing import Dict, Any
from src.simulator.base import SensorBase


class IluminacaoSimulator(SensorBase):
    """
    Simula circuito de iluminação.

    Cada instância representa UM circuito (ex: "Praça Alimentação").

    ANALOGIA: Cada circuito é como um disjuntor no QDL.
    Monitoramos a corrente para detectar lâmpadas queimadas
    ou circuitos ligados fora do horário.
    """

    def __init__(
        self,
        equipamento_id: str = "Iluminacao_Praca_Alimentacao",
        horario_abertura: int = 8,
        horario_fechamento: int = 22,
        **kwargs
    ):
        super().__init__(equipamento_id=equipamento_id, **kwargs)

        self.horario_abertura = horario_abertura
        self.horario_fechamento = horario_fechamento
        self.corrente_base = 45.0  # A (circuito típico LED)
        self.numero_lampadas = 200
        self.potencia_por_lampada = 50  # W (LED)

    def gerar_leitura_normal(self) -> Dict[str, Any]:
        hora = self.contador_leituras % 24

        # Shopping aberto = luzes ligadas
        shopping_aberto = self.horario_abertura <= hora < self.horario_fechamento

        if shopping_aberto:
            corrente = self.corrente_base
            estado = "ligado"
        else:
            # Fora do horário: algumas luzes de serviço
            corrente = self.corrente_base * 0.15  # 15% para limpeza/segurança
            estado = "ligado_reduzido"

        return {
            "corrente_a": round(corrente + self.rng.uniform(-2, 2), 2),
            "estado": estado,
            "potencia_estimada_kw": round(corrente * 0.22, 2),  # 220V
            "hora_simulada": hora,
        }

    def injetar_anomalia(self) -> Dict[str, Any]:
        leitura = self.gerar_leitura_normal()
        tipo = self.tipo_anomalia or "timer_falho"

        if tipo == "timer_falho":
            # Luzes ligadas fora do horário
            hora = self.contador_leituras % 24
            if hora >= self.horario_fechamento or hora < self.horario_abertura:
                leitura["corrente_a"] = round(
                    self.corrente_base + self.rng.uniform(-2, 2), 2)
                leitura["estado"] = "ligado_fora_horario"
                leitura["hora_simulada"] = hora

        elif tipo == "lampadas_queimadas":
            # 30% das lâmpadas queimadas → corrente cai
            leitura["corrente_a"] = round(
                self.corrente_base * self.rng.uniform(0.6, 0.7), 2)

        elif tipo == "degradacao":
            # Lâmpadas antigas consomem mais para mesma luz
            leitura["corrente_a"] = round(
                self.corrente_base * self.rng.uniform(1.15, 1.25), 2)

        return leitura
