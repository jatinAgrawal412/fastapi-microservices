"""Consumer service for processing refund order events"""
import time
import socket
import redis
from payment.app.database import SessionLocal, init_db
from payment.app.repositories import order as order_repo
from payment.app.models.order import OrderStatus
from payment.app.config import settings
from payment.app.core.logging import setup_logging

logger = setup_logging("payment-consumer")
IDEMPOTENCY_KEY = "processed:payment:refund"


def process_refund(redis_client, order_data: dict, message_id: str, key: str, group: str) -> bool:
    # Idempotency check
    if redis_client.sismember(IDEMPOTENCY_KEY, message_id):
        logger.info(
            "Skipping already processed message",
            extra={"message_id": message_id}
        )
        redis_client.xack(key, group, message_id)
        return True
    
    """Process a single refund event. Returns True if successful."""
    db = SessionLocal()
    try:
        order_id = int(order_data['pk'])
        
        # Update order status to refunded
        order = order_repo.update_order_status(db, order_id, OrderStatus.REFUNDED)
        
        if not order:
            logger.warning(f"Order {order_id} not found for refund")
            # Acknowledge message even if order not found
            redis_client.sadd(IDEMPOTENCY_KEY, message_id)
            redis_client.xack(key, group, message_id)
            return False
        else:
            logger.info(f"Order {order_id} refunded successfully")
            # Acknowledge successful processing
            redis_client.sadd(IDEMPOTENCY_KEY, message_id)
            redis_client.xack(key, group, message_id)
            return True
            
    except Exception as e:
        logger.error(f"Error processing refund for order {order_data.get('pk', 'unknown')}: {str(e)}", exc_info=True)
        # Rollback database transaction
        db.rollback()
        # Acknowledge message to prevent infinite reprocessing
        redis_client.xack(key, group, message_id)
        return False
    finally:
        db.close()


def consume_refunds() -> None:
    """Main consumer loop for processing refund events"""
    logger.info("Starting payment consumer service")
    
    # Initialize database tables before starting consumer
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
    # Reuse Redis connection
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        decode_responses=True
    )
    
    key = 'refund_order'
    group = 'payment-group'
    # Use hostname as consumer name for identification
    consumer_name = socket.gethostname()
    
    try:
        redis_client.xgroup_create(
            name=key,
            groupname=group,
            id="0",
            mkstream=True
        )
        logger.info(f"Created consumer group '{group}' for stream '{key}'")
    except Exception:
        logger.info(f"Consumer group '{group}' already exists")
    
    logger.info(f"Consumer '{consumer_name}' started for group '{group}' on stream '{key}'")
    
    # First, try to read any existing undelivered messages from the beginning
    # This handles the case where messages existed before the consumer group was created
    try:
        initial_results = redis_client.xreadgroup(
            groupname=group,
            consumername=consumer_name,
            streams={key: "0"},
            count=100
        )
        if initial_results:
            for stream, messages in initial_results:
                logger.info(f"Found {len(messages)} existing undelivered messages to process")
                for message_id, order_data in messages:
                    process_refund(redis_client, order_data, message_id, key, group)
    except Exception as e:
        logger.error(f"Error reading initial messages: {str(e)}", exc_info=True)

    logger.info("Starting to consume messages from Redis stream")
    while True:
        try:
            results = redis_client.xreadgroup(
                groupname=group,
                consumername=consumer_name,
                streams={key: ">"},
                count=10,
                block=5000
            )
            
            if results:
                for stream, messages in results:
                    for message_id, order_data in messages:
                        process_refund(redis_client, order_data, message_id, key, group)
        
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}", exc_info=True)
        
        time.sleep(1)


if __name__ == "__main__":
    consume_refunds()
