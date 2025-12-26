"""Consumer service for processing order completion events"""
import time
import socket
import redis
from inventory.app.database import SessionLocal, init_db
from inventory.app.repositories import product as product_repo
from inventory.app.config import settings
from inventory.app.core.logging import setup_logging

# Setup logging
logger = setup_logging("inventory-consumer")
IDEMPOTENCY_KEY = "processed:inventory:orders"

def process_order(redis_client, order_data: dict, message_id: str, key: str, group: str) -> bool:
    # Idempotency check
    if redis_client.sismember(IDEMPOTENCY_KEY, message_id):
        logger.info(
            "Skipping already processed message",
            extra={"message_id": message_id}
        )
        redis_client.xack(key, group, message_id)
        return True
    
    """Process a single order completion event. Returns True if successful."""
    db = SessionLocal()
    try:
        product_id = int(order_data['product_id'])
        quantity = int(order_data['quantity'])
        
        # Get product first to check availability
        product = product_repo.get_product_by_id(db, product_id)
        
        if not product:
            # Product not found, send to refund queue
            logger.warning(f"Product {product_id} not found, sending to refund")
            redis_client.xadd('refund_order', order_data, '*')
            redis_client.sadd(IDEMPOTENCY_KEY, message_id)
            redis_client.xack(key, group, message_id)
            return True
        
        # Check if we have sufficient quantity BEFORE updating
        if product.quantity < quantity:
            # Insufficient stock, send to refund queue without updating
            logger.warning(
                f"Product {product_id} has insufficient stock: {product.quantity} available, "
                f"{quantity} requested. Sending to refund"
            )
            redis_client.xadd('refund_order', order_data, '*')
            redis_client.sadd(IDEMPOTENCY_KEY, message_id)
            redis_client.xack(key, group, message_id)
            return True
        
        # Sufficient stock available, proceed with update
        product = product_repo.update_product_quantity(db, product_id, -quantity)
        
        logger.info(f"Product {product_id} quantity updated: {product.quantity} (reduced by {quantity})")
        
        redis_client.sadd(IDEMPOTENCY_KEY, message_id)
        redis_client.xack(key, group, message_id)
        return True
        
    except Exception as e:
        logger.error(f"Error processing order {message_id}: {str(e)}", exc_info=True)
        db.rollback()
        redis_client.xadd('refund_order', order_data, '*')
        redis_client.xack(key, group, message_id)
        return False
    finally:
        db.close()


def consume_orders() -> None:
    """Main consumer loop for processing order completion events"""
    logger.info("Starting inventory consumer service")
    
    # Initialize database tables before starting consumer
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        decode_responses=True
    )

    key = 'order_completed'
    group = 'inventory-group'
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
                    process_order(redis_client, order_data, message_id, key, group)
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
                        process_order(redis_client, order_data, message_id, key, group)

        except Exception as e:
            logger.error(f"Consumer error: {str(e)}", exc_info=True)
        
        time.sleep(1)


if __name__ == "__main__":
    consume_orders()
