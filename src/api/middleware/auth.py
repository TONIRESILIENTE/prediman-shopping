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

from src.services.auth_service import decodificar_token, buscar_usuario_por_email

# POR QUÊ: HTTPBearer extrai o token do header Authorization.
# O cliente envia: Authorization: Bearer <token>
security = HTTPBearer()


async def obter_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency que protege rotas.

    Uso:
        @app.get("/rota-protegida")
        async def rota(usuario: dict = Depends(obter_usuario_atual)):
            ...

    Fluxo:
    1. Extrai token do header Authorization
    2. Decodifica e valida assinatura + expiração
    3. Busca usuário no banco
    4. Retorna usuário (disponível na rota)
    5. Se qualquer passo falhar → 401 Unauthorized
    """
    token = credentials.credentials

    # Decodifica token
    payload = decodificar_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Busca usuário
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado: email não encontrado.",
        )

    usuario = buscar_usuario_por_email(email)
    if usuario is None or not usuario.get("ativo"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo.",
        )

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
