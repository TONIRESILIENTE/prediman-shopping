# src/services/verificacao_service.py
"""
Serviço de verificação visual com IA (YOLO).

Conceito:
    Cada tipo de EPI tem seu próprio modelo YOLO treinado.
    Este serviço carrega os modelos sob demanda (lazy loading)
    e os reutiliza nas próximas chamadas (singleton por tipo).

Segurança:
    - Fail closed: em caso de erro, retorna "não detectado".
      Nunca libera uma OS por falha do modelo.
    - Modelos ficam em /app/models/ (volume Docker).
    - Nenhum caminho de modelo hard-coded fora dos padrões.
"""
import os
from pathlib import Path
from typing import Dict, Optional

# Cache de modelos carregados: {"capacete": YOLO, "luva": YOLO, ...}
# Carregado uma vez, reutilizado nas próximas chamadas.
_MODELOS: Dict[str, object] = {}

# Configuração centralizada por tipo de EPI.
# Para adicionar um novo EPI no futuro, basta incluir uma linha aqui.
#   chave       → identificador interno (usado em verificar_<tipo>())
#   env_var     → variável de ambiente que pode sobrescrever o caminho
#   caminho     → caminho padrão dentro do container Docker
#   classe      → nome exato da classe no modelo YOLO (case-sensitive!)
_CONFIG: Dict[str, Dict[str, str]] = {
    "capacete": {
        "env_var": "YOLO_MODEL_PATH",  # mantido por compatibilidade
        "caminho": "/app/models/capacete_model.pt",
        "classe": "hard hat",
    },
    "luva": {
        "env_var": "YOLO_MODEL_LUVA_PATH",
        "caminho": "/app/models/luva_model.pt",
        "classe": "Gloves-Detection",  # exatamente como treinado
    },
}


def _carregar_modelo(tipo: str):
    """
    Carrega um modelo YOLO sob demanda (singleton por tipo).

    Na primeira chamada para um tipo, carrega o modelo do disco.
    Nas chamadas seguintes, retorna o modelo já em memória.
    """
    if tipo not in _CONFIG:
        print(f"⚠️ Tipo de EPI desconhecido: {tipo}")
        return None

    if tipo in _MODELOS:
        return _MODELOS[tipo]

    config = _CONFIG[tipo]
    caminho = os.getenv(config["env_var"], config["caminho"])

    try:
        from ultralytics import YOLO

        if not Path(caminho).exists():
            print(f"⚠️ Modelo não encontrado: {caminho}")
            return None

        _MODELOS[tipo] = YOLO(caminho)
        print(f"✅ Modelo YOLO '{tipo}' carregado: {caminho}")
        return _MODELOS[tipo]

    except Exception as e:
        print(f"⚠️ Erro ao carregar YOLO '{tipo}': {e}")
        return None


def _verificar_epi(caminho_foto: str, tipo: str, limiar: float = 0.5) -> Dict:
    """
    Lógica compartilhada de verificação.

    Retorna sempre um dict com:
        tem_epi   → bool
        confianca → float (0.0 a 1.0)
        detalhes  → str (mensagem legível)
    """
    modelo = _carregar_modelo(tipo)
    if modelo is None:
        return {
            "tem_epi": False,
            "confianca": 0.0,
            "detalhes": f"Modelo YOLO '{tipo}' indisponível",
        }

    classe_esperada = _CONFIG[tipo]["classe"]

    try:
        results = modelo(caminho_foto, verbose=False)

        tem_epi = False
        confianca_max = 0.0

        for r in results:
            for box in r.boxes:
                classe_id = int(box.cls[0])
                nome_classe = modelo.names[classe_id]
                confianca = float(box.conf[0])

                if nome_classe == classe_esperada and confianca > limiar:
                    tem_epi = True
                    confianca_max = max(confianca_max, confianca)

        return {
            "tem_epi": tem_epi,
            "confianca": round(confianca_max, 3),
            "detalhes": f"{tipo.capitalize()} detectado" if tem_epi
            else f"{tipo.capitalize()} NÃO detectado",
        }

    except Exception as e:
        # Fail closed: em erro, nunca considera detectado
        return {
            "tem_epi": False,
            "confianca": 0.0,
            "detalhes": f"Erro na verificação: {str(e)}",
        }


# ─── API pública (mantém compatibilidade com código existente) ───

def verificar_capacete(caminho_foto: str) -> Dict:
    """
    Verifica se uma foto contém capacete de segurança.

    Interface mantida idêntica à versão anterior — nenhum código
    que já chama esta função precisa ser alterado.
    """
    resultado = _verificar_epi(caminho_foto, "capacete")
    return {
        "tem_capacete": resultado["tem_epi"],
        "confianca": resultado["confianca"],
        "detalhes": resultado["detalhes"],
    }


def verificar_luva(caminho_foto: str) -> Dict:
    """
    Verifica se uma foto contém luva de proteção/isolante.

    Mesma estrutura de verificar_capacete(), para manter consistência.
    """
    resultado = _verificar_epi(caminho_foto, "luva")
    return {
        "tem_luva": resultado["tem_epi"],
        "confianca": resultado["confianca"],
        "detalhes": resultado["detalhes"],
    }
