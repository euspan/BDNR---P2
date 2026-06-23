import os
import json
import logging
import aio_pika
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
RABBITMQ_QUEUE = "pedidos_criados"
KAFKA_TOPIC = "pedidos-criados"


# ── RabbitMQ ──────────────────────────────────────────────────────────────────

async def publish_rabbitmq(pedido: dict):
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(RABBITMQ_QUEUE, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(pedido).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=RABBITMQ_QUEUE,
            )
        logger.info(f"[RabbitMQ] Mensagem publicada para pedido {pedido.get('id')}")
    except Exception as e:
        logger.error(f"[RabbitMQ] Falha ao publicar: {e}")


# ── Kafka ─────────────────────────────────────────────────────────────────────

async def publish_kafka(pedido: dict):
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    try:
        await producer.start()
        await producer.send_and_wait(KAFKA_TOPIC, pedido)
        logger.info(f"[Kafka] Evento publicado para pedido {pedido.get('id')}")
    except Exception as e:
        logger.error(f"[Kafka] Falha ao publicar: {e}")
    finally:
        await producer.stop()
