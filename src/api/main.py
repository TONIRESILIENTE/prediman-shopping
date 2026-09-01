# src/api/main.py
# ─────────────────────────────────────────────
# Entrypoint da API FastAPI.
# Registra todos os routers e middlewares.
# ─────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from src.api.routers import dados, equipamentos, ordens, pops, auth, passos
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="PrediMan Shopping API",
    description="Plataforma de Manutenção Preditiva Inteligente para Shopping Centers",
    version="0.2.0",
)

# ─── CORS ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Registrar Routers ──────────────────────
# POR QUÊ: Cada router é um módulo independente.
# Isso mantém main.py enxuto — só registra, não implementa.
app.include_router(dados.router)
app.include_router(equipamentos.router)
app.include_router(ordens.router)
app.include_router(pops.router)
app.include_router(auth.router)
app.include_router(passos.router)

# Servir PWA como arquivos estáticos
app.mount("/pwa", StaticFiles(directory="src/pwa", html=True), name="pwa")


# ─── Rotas Básicas ─────────────────────────

@app.get("/")
async def root():
    return {
        "status": "online",
        "sistema": "PrediMan Shopping",
        "versao": "0.2.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "docs": "/docs",
            "medicao": "/api/v1/medicao",
            "lote": "/api/v1/medicao/lote",
            "equipamentos": "/api/v1/equipamentos",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
