import asyncio
import os
import json
import logging
import aio_pika

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Worker")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "shop_events"


async def main():
    logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()

        # Объявляем очередь (durable=True, чтобы сообщения сохранялись при перезапуске RabbitMQ)
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        logger.info(f"Waiting for messages in queue '{QUEUE_NAME}'...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        payload = json.loads(message.body.decode())
                        event_type = payload.get("event")
                        event_data = payload.get("data")

                        logger.info(f"📥 Received Event: {event_type}")
                        logger.info(f"📄 Data: {event_data}")

                    except json.JSONDecodeError:
                        logger.error("Failed to decode JSON message")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped")
