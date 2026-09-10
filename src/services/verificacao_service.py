# src/services/verificacao_service.py
"""
Serviço de verificação visual com IA (YOLO).
"""
import os
from pathlib import Path
from typing import Dict

_modelo = None


def _carregar_modelo():
    """Carrega o modelo YOLO sob demanda (singleton)."""
    global _modelo
    if _modelo is None:
        try:
            from ultralytics import YOLO
            caminho = os.getenv("YOLO_MODEL_PATH",
                                "/app/models/capacete_model.pt")
            if Path(caminho).exists():
                _modelo = YOLO(caminho)
                print(f"✅ Modelo YOLO carregado: {caminho}")
            else:
                print(f"⚠️ Modelo não encontrado: {caminho}")
        except Exception as e:
            print(f"⚠️ Erro ao carregar YOLO: {e}")
    return _modelo


def verificar_capacete(caminho_foto: str) -> Dict:
    """Verifica se uma foto contém capacete de segurança."""
    modelo = _carregar_modelo()
    if modelo is None:
        return {"tem_capacete": False, "confianca": 0.0, "detalhes": "Modelo YOLO indisponível"}

    try:
        results = modelo(caminho_foto, verbose=False)
        tem_capacete = False
        confianca_max = 0.0

        for r in results:
            for box in r.boxes:
                classe_id = int(box.cls[0])
                nome_classe = modelo.names[classe_id]
                confianca = float(box.conf[0])

                if nome_classe == "hard hat" and confianca > 0.5:
                    tem_capacete = True
                    confianca_max = max(confianca_max, confianca)

        return {
            "tem_capacete": tem_capacete,
            "confianca": round(confianca_max, 3),
            "detalhes": "Capacete detectado" if tem_capacete else "Capacete NÃO detectado",
        }
    except Exception as e:
        return {"tem_capacete": False, "confianca": 0.0, "detalhes": f"Erro: {str(e)}"}
