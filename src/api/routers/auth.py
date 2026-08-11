# src/api/routers/auth.py
# ─────────────────────────────────────────────
# Rotas de autenticação: registro e login.
# Estas rotas NÃO são protegidas (são a porta de entrada).
# ─────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from src.database.connection import get_db

from src.services.auth_service import registrar_usuario, autenticar_usuario
from src.api.middleware.auth import obter_usuario_atual

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


# ─── Schemas ────────────────────────────────

class RegistroRequest(BaseModel):
    """Dados para criar uma conta nova."""
    email: EmailStr = Field(..., description="Email válido")
    senha: str = Field(
        ...,
        min_length=6,
        description="Senha com no mínimo 6 caracteres",
        examples=["SenhaSegura123"]
    )
    nome: str = Field(..., min_length=2, description="Nome completo")
    papel: str = Field(default="tecnico", description="tecnico, gestor, admin")


class LoginRequest(BaseModel):
    """Dados para login."""
    email: EmailStr
    senha: str


class UsuarioResponse(BaseModel):
    id: str
    email: str
    nome: str
    papel: str
    ativo: bool = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse


class MensagemResponse(BaseModel):
    mensagem: str


# ─── Rotas ──────────────────────────────────

@router.post(
    "/registro",
    response_model=MensagemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
)
async def registrar(body: RegistroRequest, db: Session = Depends(get_db)):
    """Cria uma nova conta de usuário."""
    try:
        usuario = registrar_usuario(
            db=db,
            email=body.email,
            senha=body.senha,
            nome=body.nome,
            papel=body.papel,
        )
        return MensagemResponse(
            mensagem=f"Usuário '{usuario.nome}' registrado com sucesso."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Autentica usuário e retorna token JWT para usar nas rotas protegidas.",
)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Faz login e retorna token de acesso."""
    resultado = autenticar_usuario(db=db, email=body.email, senha=body.senha)

    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(**resultado)


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Dados do usuário logado",
)
async def me(usuario=Depends(obter_usuario_atual)):
    return UsuarioResponse(
        id=str(usuario.id),
        email=usuario.email,
        nome=usuario.nome,
        papel=usuario.papel,
        ativo=usuario.ativo,
    )
