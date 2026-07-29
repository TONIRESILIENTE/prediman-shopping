from src.simulator.orchestrator import Orchestrator
import requests

o = Orchestrator()
o.ativar_anomalia('Chiller_01', 'desgaste_rolamento')
leitura = o.gerar_leituras()[0]

dados = {k: v for k, v in leitura.items() if k not in [
    'equipamento_id', 'timestamp', 'anomalia_detectada', 'tipo_anomalia']}

resp = requests.post('http://api:8000/api/v1/medicao', json={
    'equipamento_id': 'Chiller_01',
    'tipo': 'chiller',
    'dados': dados,
})

data = resp.json()
print(f"ANOMALIA: {data['diagnostico']['tipo_anomalia']}")
print(f"OS: {data.get('os_titulo', 'N/A')}")
