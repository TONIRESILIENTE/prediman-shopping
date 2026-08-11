# src/api/middleware/auth.py
# ─────────────────────────────────────────────
# CONCEITO: Middleware de autenticação.
#
# Esta função é usada como "dependência" nas rotas.
# Se o token for inválido, a rota nem executa.
#
# FastAPI chama esta função ANTES da rota.
# Se lançar HTTPException, a rota retorna 401 automaticamente.
# ─────────────────────────────────────────────

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import Usuario

from src.services.auth_service import decodificar_token, buscar_usuario_por_email

# POR QUÊ: HTTPBearer extrai o token do header Authorization.
# O cliente envia: Authorization: Bearer <token>
security = HTTPBearer()


async def obter_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    token = credentials.credentials
    payload = decodificar_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401, detail="Token inválido ou expirado.")

    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Token malformado.")

    usuario = buscar_usuario_por_email(db, email)
    if usuario is None:
        raise HTTPException(
            status_code=401, detail="Usuário não encontrado ou inativo.")

    return usuario


def exigir_papel(*papeis: str):
    """
    Factory que cria uma dependência para exigir papel específico.

    Uso:
        @app.get("/admin")
        async def rota_admin(usuario: dict = Depends(exigir_papel("admin", "gestor"))):
            ...

    POR QUÊ: Factory pattern — cada rota define quais papéis pode acessar.
    """
    async def verificador_papel(usuario: dict = Depends(obter_usuario_atual)) -> dict:
        if usuario["papel"] not in papeis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Papéis permitidos: {papeis}",
            )
        return usuario

    return verificador_papel
