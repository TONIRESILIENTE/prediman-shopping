# src/simulator/run.py
"""
Entrypoint do simulador — chamado pelo Docker.
"""
from src.simulator.orchestrator import Orchestrator


def main():
    orchestrator = Orchestrator(seed=42)
    orchestrator.executar_ciclo(intervalo_segundos=2.0)


if __name__ == "__main__":
    main()
