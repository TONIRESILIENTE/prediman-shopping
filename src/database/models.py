import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime,
    ForeignKey, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.database.connection import Base


class TipoEquipamento(str, enum.Enum):
    CHILLER = "chiller"
    SUBESTACAO = "subestacao"
    BOMBA = "bomba"
    ILUMINACAO = "iluminacao"


class SeveridadeOS(str, enum.Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class StatusOS(str, enum.Enum):
    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    PAUSADA = "pausada"
    CONCLUIDA = "concluida"


class PapelUsuario(str, enum.Enum):
    TECNICO = "tecnico"
    GESTOR = "gestor"
    ADMIN = "admin"


class Equipamento(Base):
    __tablename__ = "equipamentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(100), nullable=False, unique=True)
    tipo = Column(String(50), nullable=False)
    localizacao = Column(String(200), nullable=False)
    fabricante = Column(String(100))
    modelo = Column(String(100))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc))

    leituras = relationship("LeituraSensor", back_populates="equipamento")
    ordens_servico = relationship("OrdemServico", back_populates="equipamento")


class LeituraSensor(Base):
    __tablename__ = "leituras_sensores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipamento_id = Column(UUID(as_uuid=True), ForeignKey(
        "equipamentos.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc))
    dados = Column(JSON, nullable=False)

    equipamento = relationship("Equipamento", back_populates="leituras")


class OrdemServico(Base):
    __tablename__ = "ordens_servico"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipamento_id = Column(UUID(as_uuid=True), ForeignKey(
        "equipamentos.id"), nullable=False)
    usuario_abertura_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    usuario_responsavel_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=False)
    severidade = Column(String(20), default="media")
    status = Column(String(20), default="aberta")
    diagnostico_ml = Column(String(200), nullable=True)
    criado_em = Column(DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime(timezone=True),
                           onupdate=lambda: datetime.now(timezone.utc))
    concluido_em = Column(DateTime(timezone=True), nullable=True)

    equipamento = relationship("Equipamento", back_populates="ordens_servico")
    pop = relationship("POP", back_populates="ordem_servico", uselist=False)


class POP(Base):
    __tablename__ = "pops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ordem_servico_id = Column(UUID(as_uuid=True), ForeignKey(
        "ordens_servico.id"), unique=True, nullable=True)
    codigo = Column(String(20), unique=True, nullable=False)
    titulo = Column(String(200), nullable=False)
    equipamento_tipo = Column(String(50), nullable=False)
    passos = Column(JSON, nullable=False)
    ferramentas = Column(JSON)
    epi_obrigatorio = Column(JSON)
    tempo_estimado_minutos = Column(Integer)
    criado_em = Column(DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc))

    ordem_servico = relationship("OrdemServico", back_populates="pop")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    senha_hash = Column(String(255), nullable=False)
    papel = Column(String(20), default="tecnico")
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc))
