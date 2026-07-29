# src/simulator/run.py
"""
Entrypoint do simulador — envia leituras automaticamente para a API.
"""
import time
import requests
import os
from src.simulator.orchestrator import Orchestrator

# POR QUÊ: URL da API via ambiente = funciona local e em deploy
API_URL = os.getenv("API_URL", "http://api:8000/api/v1")


def main():
    orchestrator = Orchestrator(seed=42)

    print("🏢 PrediMan Shopping — Simulador de Sensores")
    print(f"📡 Conectado à API: {API_URL}")
    print(f"🛠️  {len(orchestrator.simuladores)} equipamentos monitorados")
    print("=" * 50)

    while True:
        try:
            # Gera leituras de todos os equipamentos
            leituras = orchestrator.gerar_leituras()

            # Prepara lote para enviar à API
            medicoes = []
            for leitura in leituras:
                # Determina o tipo do equipamento
                equip_id = leitura.get("equipamento_id", "")
                if "Chiller" in equip_id:
                    tipo = "chiller"
                elif "Subestacao" in equip_id:
                    tipo = "subestacao"
                elif "Bomba" in equip_id:
                    tipo = "bomba"
                elif "Iluminacao" in equip_id:
                    tipo = "iluminacao"
                else:
                    continue

                # Remove campos de metadados (a API espera só os dados do sensor)
                dados_sensor = {
                    k: v for k, v in leitura.items()
                    if k not in ["equipamento_id", "timestamp", "anomalia_detectada", "tipo_anomalia"]
                }

                medicoes.append({
                    "equipamento_id": equip_id,
                    "tipo": tipo,
                    "dados": dados_sensor,
                })

            # Envia para a API
            response = requests.post(
                f"{API_URL}/medicao/lote",
                json={"medicoes": medicoes},
                timeout=5,
            )

            if response.status_code == 201:
                data = response.json()
                anomalias = data.get("total_anomalias", 0)
                status_icone = "⚠️" if anomalias > 0 else "✅"
                print(f"{status_icone} Lote enviado: {data['total_recebido']} leituras, "
                      f"{anomalias} anomalia(s) detectada(s)")
            else:
                print(f"❌ Erro ao enviar: {response.status_code}")

        except requests.ConnectionError:
            print("❌ API indisponível. Tentando novamente em 5s...")
        except Exception as e:
            print(f"❌ Erro: {e}")

        # Aguarda 5 segundos entre envios
        time.sleep(5)


if __name__ == "__main__":
    main()
