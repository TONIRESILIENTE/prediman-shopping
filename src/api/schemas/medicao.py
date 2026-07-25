# src/api/schemas/medicao.py
# ─────────────────────────────────────────────
# CONCEITO: Schemas Pydantic = contrato da API.
#
# Toda requisição é validada ANTES de chegar na lógica.
# Se o JSON não bater com o schema, a API rejeita com erro 422
# e uma mensagem clara do que está errado.
#
# ANALOGIA: É o inspetor de qualidade na entrada da fábrica.
# Se a matéria-prima não está no padrão, nem entra na linha.
# ─────────────────────────────────────────────

from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TipoEquipamento(str, Enum):
    CHILLER = "chiller"
    SUBESTACAO = "subestacao"
    BOMBA = "bomba"
    ILUMINACAO = "iluminacao"


class Severidade(str, Enum):
    NORMAL = "normal"
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


# ─── Request Schemas (o que o cliente envia) ───

class MedicaoRequest(BaseModel):
    """
    Schema para UMA leitura de sensor.

    Exemplo de JSON válido:
    {
        "equipamento_id": "Chiller_01",
        "tipo": "chiller",
        "dados": {
            "vibracao_mm_s": 3.2,
            "temp_entrada_c": 12.0,
            "temp_saida_c": 7.0,
            "delta_t_c": 5.0,
            "corrente_a": 58.0
        }
    }
    """
    equipamento_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identificador único do equipamento",
        examples=["Chiller_01"]
    )
    tipo: TipoEquipamento = Field(
        ...,
        description="Tipo do equipamento monitorado"
    )
    dados: dict = Field(
        ...,
        description="Dicionário com as leituras dos sensores"
    )

    # POR QUÊ: Validator customizado = regras que dependem de mais de um campo.
    # Ex: se tipo é 'chiller', os dados DEVEM conter 'vibracao_mm_s'.
    @model_validator(mode="after")
    def validar_dados_por_tipo(self):
        """Garante que os campos obrigatórios por tipo estão presentes."""
        campos_obrigatorios = {
            "chiller": ["vibracao_mm_s", "delta_t_c", "corrente_a"],
            "subestacao": ["fator_potencia", "tensao_v", "corrente_a"],
            "bomba": ["vibracao_mm_s", "corrente_a", "status_bomba"],
            "iluminacao": ["corrente_a", "estado"],
        }

        obrigatorios = campos_obrigatorios.get(self.tipo.value, [])
        for campo in obrigatorios:
            if campo not in self.dados:
                raise ValueError(
                    f"Campo '{campo}' é obrigatório para equipamentos do tipo '{self.tipo.value}'"
                )
        return self


class LoteMedicaoRequest(BaseModel):
    """Schema para múltiplas leituras de uma vez."""
    medicoes: List[MedicaoRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista de leituras (máximo 100 por requisição)"
    )


# ─── Response Schemas (o que a API retorna) ───

class DiagnosticoResponse(BaseModel):
    """Resposta padronizada de diagnóstico."""
    equipamento_id: str
    anomalia_detectada: bool
    tipo_anomalia: Optional[str] = None
    severidade: Severidade
    detalhes: str
    regra_disparada: Optional[str] = None
    timestamp: str


class MedicaoResponse(BaseModel):
    """Resposta após processar uma leitura."""
    status: str = "processado"
    equipamento_id: str
    diagnostico: DiagnosticoResponse
    timestamp_processamento: str


class LoteMedicaoResponse(BaseModel):
    """Resposta para lote de leituras."""
    status: str = "processado"
    total_recebido: int
    total_anomalias: int
    diagnosticos: List[DiagnosticoResponse]


class EquipamentoResponse(BaseModel):
    """Informações de um equipamento cadastrado."""
    id: str
    nome: str
    tipo: str
    localizacao: str
    ativo: bool


class MensagemResponse(BaseModel):
    """Resposta genérica."""
    mensagem: str
    detalhes: Optional[str] = None
