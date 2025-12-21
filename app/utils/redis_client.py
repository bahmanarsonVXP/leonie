"""
Client Redis singleton pour les queues de background jobs.

Ce module fournit un accès centralisé aux queues Redis (RQ)
utilisées pour le traitement asynchrone des emails.
"""

import redis
from rq import Queue

from app.config import get_settings

# Récupération settings
settings = get_settings()

# Connexion Redis
redis_conn = redis.from_url(
    settings.REDIS_URL,
    decode_responses=False  # RQ nécessite bytes
)

# Queues
queue_high = Queue(settings.REDIS_QUEUE_HIGH, connection=redis_conn)
queue_default = Queue(settings.REDIS_QUEUE_DEFAULT, connection=redis_conn)


def get_queue(priority: str = "default") -> Queue:
    """
    Retourne la queue appropriée selon la priorité.

    Args:
        priority: Priorité ("high" ou "default")

    Returns:
        Queue RQ correspondante

    Example:
        >>> from app.utils.redis_client import get_queue
        >>> queue = get_queue("high")
        >>> job = queue.enqueue('my_module.my_function', arg1="value")
    """
    if priority == "high":
        return queue_high
    return queue_default


def get_redis_connection() -> redis.Redis:
    """
    Retourne la connexion Redis.

    Returns:
        Connexion Redis
    """
    return redis_conn
