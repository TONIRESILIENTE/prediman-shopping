# src/services/auth_service.py
# ─────────────────────────────────────────────
# CONCEITO: Serviço de autenticação.
#
# JWT (JSON Web Token) = "crachá digital".
#
# Fluxo:
# 1. Usuário faz login (email + senha)
# 2. Servidor verifica e gera um token assinado
# 3. Usuário envia o token em cada requisição
# 4. Servidor verifica assinatura → confia na identidade
#
# SEGURANÇA: Senhas NUNCA são armazenadas em texto puro.
# Usamos bcrypt — mesmo se o banco vazar, senhas estão protegidas.
# ─────────────────────────────────────────────

import os
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from jose import JWTError, jwt

# ─── Configuração ────────────────────────────

SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-desenvolvimento")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# "Banco" em memória
_usuarios: Dict[str, dict] = {}


# ─── Hash de senhas ─────────────────────────

def gerar_hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha."""
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_senha(senha_texto: str, hash_armazenado: str) -> bool:
    """Verifica se a senha confere com o hash."""
    return bcrypt.checkpw(senha_texto.encode('utf-8'), hash_armazenado.encode('utf-8'))


# ─── JWT ────────────────────────────────────

def criar_token_jwt(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token JWT assinado."""
    to_encode = data.copy()
    expire = datetime.now(
        timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    """Decodifica e valida um token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ─── Gerenciamento de usuários ──────────────

def registrar_usuario(email: str, senha: str, nome: str, papel: str = "tecnico") -> dict:
    """Registra um novo usuário."""
    if email in _usuarios:
        raise ValueError(f"Email '{email}' já está cadastrado.")

    papeis_validos = ["tecnico", "gestor", "admin"]
    if papel not in papeis_validos:
        raise ValueError(f"Papel inválido. Permitidos: {papeis_validos}")

    usuario = {
        "id": str(uuid.uuid4()),
        "email": email,
        "nome": nome,
        "senha_hash": gerar_hash_senha(senha),
        "papel": papel,
        "ativo": True,
        "criado_em": datetime.now(timezone.utc).isoformat(),
    }

    _usuarios[email] = usuario
    return usuario


def autenticar_usuario(email: str, senha: str) -> Optional[dict]:
    """Autentica um usuário e retorna token JWT."""
    usuario = _usuarios.get(email)

    if not usuario or not usuario["ativo"]:
        return None

    if not verificar_senha(senha, usuario["senha_hash"]):
        return None

    token = criar_token_jwt({
        "sub": usuario["email"],
        "papel": usuario["papel"],
        "nome": usuario["nome"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario["id"],
            "email": usuario["email"],
            "nome": usuario["nome"],
            "papel": usuario["papel"],
        },
    }


def buscar_usuario_por_email(email: str) -> Optional[dict]:
    """Busca usuário pelo email."""
    return _usuarios.get(email)
