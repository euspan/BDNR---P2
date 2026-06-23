from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class StatusPedido(str, Enum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"


class PedidoCreate(BaseModel):
    nome_cliente: str = Field(..., min_length=1, example="João Silva")
    nome_produto: str = Field(..., min_length=1, example="Notebook Dell")
    quantidade: int = Field(..., gt=0, example=1)


class PedidoResponse(BaseModel):
    id: str
    nome_cliente: str
    nome_produto: str
    quantidade: int
    status: StatusPedido

    class Config:
        use_enum_values = True
