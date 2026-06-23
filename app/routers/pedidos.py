import uuid
from fastapi import APIRouter, HTTPException
from typing import List
from app.models import PedidoCreate, PedidoResponse, StatusPedido
from app.database import get_collection
from app.messaging import publish_rabbitmq, publish_kafka

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("/", response_model=PedidoResponse, status_code=201)
async def criar_pedido(pedido: PedidoCreate):
    pedido_id = str(uuid.uuid4())

    doc = {
        "_id": pedido_id,
        "nome_cliente": pedido.nome_cliente,
        "nome_produto": pedido.nome_produto,
        "quantidade": pedido.quantidade,
        "status": StatusPedido.PENDENTE.value,
    }

    collection = get_collection()
    await collection.insert_one(doc)

    evento = {
        "id": pedido_id,
        "nome_cliente": pedido.nome_cliente,
        "nome_produto": pedido.nome_produto,
        "quantidade": pedido.quantidade,
        "status": StatusPedido.PENDENTE.value,
    }

    # Publicar em RabbitMQ e Kafka (falhas não bloqueiam a resposta)
    await publish_rabbitmq(evento)
    await publish_kafka(evento)

    return PedidoResponse(id=pedido_id, **pedido.dict(), status=StatusPedido.PENDENTE)


@router.get("/", response_model=List[PedidoResponse])
async def listar_pedidos():
    collection = get_collection()
    pedidos = []
    async for doc in collection.find():
        pedidos.append(
            PedidoResponse(
                id=doc["_id"],
                nome_cliente=doc["nome_cliente"],
                nome_produto=doc["nome_produto"],
                quantidade=doc["quantidade"],
                status=doc["status"],
            )
        )
    return pedidos
