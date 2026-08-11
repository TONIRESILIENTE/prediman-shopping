# src/services/auth_service.py
import os
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from src.database.models import Usuario

SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-desenvolvimento")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_senha(senha_texto: str, hash_armazenado: str) -> bool:
    return bcrypt.checkpw(senha_texto.encode('utf-8'), hash_armazenado.encode('utf-8'))


def criar_token_jwt(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(
        timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def registrar_usuario(db: Session, email: str, senha: str, nome: str, papel: str = "tecnico") -> Usuario:
    existente = db.query(Usuario).filter(Usuario.email == email).first()
    if existente:
        raise ValueError(f"Email '{email}' já está cadastrado.")

    papeis_validos = ["tecnico", "gestor", "admin"]
    if papel not in papeis_validos:
        raise ValueError(f"Papel inválido. Permitidos: {papeis_validos}")

    usuario = Usuario(
        email=email,
        nome=nome,
        senha_hash=gerar_hash_senha(senha),
        papel=papel,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def autenticar_usuario(db: Session, email: str, senha: str) -> Optional[dict]:
    usuario = db.query(Usuario).filter(
        Usuario.email == email, Usuario.ativo == True).first()
    if not usuario:
        return None
    if not verificar_senha(senha, usuario.senha_hash):
        return None

    token = criar_token_jwt({
        "sub": usuario.email,
        "papel": usuario.papel,
        "nome": usuario.nome,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": str(usuario.id),
            "email": usuario.email,
            "nome": usuario.nome,
            "papel": usuario.papel,
            "ativo": usuario.ativo,
        },
    }


def buscar_usuario_por_email(db: Session, email: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.email == email, Usuario.ativo == True).first()
