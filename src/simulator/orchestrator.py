# src/simulator/orchestrator.py
# ─────────────────────────────────────────────
# CONCEITO: Orchestrator (maestro) — coordena todos os simuladores.
#
# Responsável por:
# - Inicializar todos os simuladores
# - Gerar leituras em lote
# - Injetar anomalias sob demanda
# - Publicar dados (via MQTT no futuro, stdout por enquanto)
# ─────────────────────────────────────────────

import json
import time
from typing import Dict, List, Optional
from src.simulator.chiller import ChillerSimulator
from src.simulator.subestacao import SubestacaoSimulator
from src.simulator.bomba import BombaSimulator
from src.simulator.iluminacao import IluminacaoSimulator


class Orchestrator:
    """
    Coordena todos os simuladores do shopping.

    ANALOGIA: É o "CLP mestre" que lê todos os sensores
    e envia para o sistema supervisório.
    """

    def __init__(self, seed: int = 42):
        # Inicializa todos os simuladores
        self.simuladores = {
            "Chiller_01": ChillerSimulator(
                equipamento_id="Chiller_01",
                seed=seed,
            ),
            "Subestacao_Principal": SubestacaoSimulator(
                equipamento_id="Subestacao_Principal",
                seed=seed + 1,
            ),
            "Bomba_Recalque_G1": BombaSimulator(
                equipamento_id="Bomba_Recalque_G1",
                seed=seed + 2,
            ),
            "Iluminacao_Praca": IluminacaoSimulator(
                equipamento_id="Iluminacao_Praca_Alimentacao",
                horario_abertura=8,
                horario_fechamento=22,
                seed=seed + 3,
            ),
            "Iluminacao_Estacionamento": IluminacaoSimulator(
                equipamento_id="Iluminacao_Estacionamento_G1",
                horario_abertura=6,
                horario_fechamento=23,
                seed=seed + 4,
            ),
            "Iluminacao_Fachada": IluminacaoSimulator(
                equipamento_id="Iluminacao_Fachada",
                horario_abertura=18,  # acende ao anoitecer
                horario_fechamento=6,  # apaga ao amanhecer
                seed=seed + 5,
            ),
        }
        self.seed = seed
        self.contador_ciclos = 0

    def gerar_leituras(self) -> List[Dict]:
        """
        Gera uma leitura de TODOS os equipamentos.

        Returns:
            Lista de leituras, uma por equipamento.
        """
        leituras = []
        for nome, simulador in self.simuladores.items():
            leitura = simulador.gerar_leitura()
            leituras.append(leitura)

        self.contador_ciclos += 1
        return leituras

    def ativar_anomalia(self, equipamento: str, tipo: str):
        """
        Ativa uma anomalia específica em um equipamento.

        Args:
            equipamento: nome do equipamento (ex: "Chiller_01")
            tipo: tipo da anomalia (ex: "desgaste_rolamento")

        Raises:
            ValueError: se equipamento não existe
        """
        if equipamento not in self.simuladores:
            raise ValueError(
                f"Equipamento '{equipamento}' nao encontrado. "
                f"Disponiveis: {list(self.simuladores.keys())}"
            )
        self.simuladores[equipamento].ativar_anomalia(tipo)

    def desativar_anomalia(self, equipamento: str):
        """Remove anomalia de um equipamento."""
        if equipamento not in self.simuladores:
            raise ValueError(f"Equipamento '{equipamento}' nao encontrado.")
        self.simuladores[equipamento].desativar_anomalia()

    def listar_equipamentos(self) -> List[str]:
        """Retorna lista de equipamentos monitorados."""
        return list(self.simuladores.keys())

    def listar_anomalias_disponiveis(self, equipamento: str) -> List[str]:
        """
        Lista os tipos de anomalia disponíveis para um equipamento.
        Não lista todos possíveis, mas os principais documentados.
        """
        anomalias_por_equipamento = {
            "Chiller_01": ["desgaste_rolamento", "baixa_eficiencia", "sobrecarga"],
            "Subestacao_Principal": ["fp_baixo", "sobrecarga_fase", "oscilacao_tensao"],
            "Bomba_Recalque_G1": ["cavitacao", "obstrucao", "poco_seco"],
            "Iluminacao_Praca": ["timer_falho", "lampadas_queimadas", "degradacao"],
            "Iluminacao_Estacionamento": ["timer_falho", "lampadas_queimadas", "degradacao"],
            "Iluminacao_Fachada": ["timer_falho", "lampadas_queimadas", "degradacao"],
        }
        return anomalias_por_equipamento.get(equipamento, [])

    def executar_ciclo(self, intervalo_segundos: float = 2.0):
        """
        Loop infinito de geração de leituras.
        Para demonstração e testes.

        Args:
            intervalo_segundos: tempo entre leituras
        """
        print("🏢 PrediMan Shopping — Simulador Iniciado")
        print(f"📡 {len(self.simuladores)} equipamentos monitorados")
        print("=" * 50)

        try:
            while True:
                leituras = self.gerar_leituras()
                for leitura in leituras:
                    status = "⚠️ ANOMALIA" if leitura.get(
                        "anomalia_detectada") else "✅"
                    print(
                        f"{status} [{leitura['equipamento_id']}] "
                        f"{json.dumps(leitura, indent=None, ensure_ascii=False)}"
                    )
                print("-" * 50)
                time.sleep(intervalo_segundos)
        except KeyboardInterrupt:
            print("\n🛑 Simulador encerrado.")
