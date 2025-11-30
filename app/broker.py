import os
import json
import aio_pika
from aio_pika import Message, DeliveryMode

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "shop_events"


async def send_message(event_type: str, data: dict):
    """
    Отправляет сообщение в очередь RabbitMQ.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()

        # Объявляем очередь, чтобы убедиться, что она существует
        await channel.declare_queue(QUEUE_NAME, durable=True)

        message_body = {"event": event_type, "data": data}

        await channel.default_exchange.publish(
            Message(
                body=json.dumps(message_body).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key=QUEUE_NAME,
        )
