"""
Utilitaires pour la connexion Redis et Redis Queue.

Ce module fournit des helpers pour la connexion Redis
et la gestion des jobs asynchrones via Redis Queue (RQ).
"""

from typing import Optional

import redis
from redis import Redis
from rq import Queue

from app.config import get_settings


class RedisClient:
    """Client Redis singleton pour l'application."""

    _instance: Optional[Redis] = None
    _high_queue: Optional[Queue] = None
    _default_queue: Optional[Queue] = None

    @classmethod
    def get_client(cls) -> Redis:
        """
        Récupère l'instance unique du client Redis.

        Returns:
            Redis: Instance du client Redis.

        Raises:
            ValueError: Si REDIS_URL n'est pas configuré.
        """
        if cls._instance is None:
            settings = get_settings()
            if not settings.REDIS_URL:
                raise ValueError(
                    "REDIS_URL doit être défini dans les variables d'environnement"
                )
            cls._instance = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
        return cls._instance

    @classmethod
    def get_queue(cls, queue_name: str = "default") -> Queue:
        """
        Récupère une queue Redis Queue.

        Args:
            queue_name: Nom de la queue ('high' ou 'default').

        Returns:
            Queue: Instance de la queue RQ.
        """
        client = cls.get_client()

        if queue_name == "high":
            if cls._high_queue is None:
                cls._high_queue = Queue("high", connection=client)
            return cls._high_queue
        else:
            if cls._default_queue is None:
                cls._default_queue = Queue("default", connection=client)
            return cls._default_queue


def get_redis() -> Redis:
    """
    Helper pour récupérer le client Redis.

    Returns:
        Redis: Instance du client Redis.
    """
    return RedisClient.get_client()


def get_queue(queue_name: str = "default") -> Queue:
    """
    Helper pour récupérer une queue RQ.

    Args:
        queue_name: Nom de la queue.

    Returns:
        Queue: Instance de la queue RQ.
    """
    return RedisClient.get_queue(queue_name)


def enqueue_job(
    func,
    *args,
    queue_name: str = "default",
    job_timeout: str = "10m",
    **kwargs
):
    """
    Ajoute un job à une queue Redis Queue.

    Args:
        func: Fonction à exécuter de manière asynchrone.
        *args: Arguments positionnels pour la fonction.
        queue_name: Nom de la queue ('high' ou 'default').
        job_timeout: Timeout du job (ex: '10m', '1h').
        **kwargs: Arguments nommés pour la fonction.

    Returns:
        Job: Instance du job RQ créé.

    Example:
        >>> from app.workers.jobs import process_email_job
        >>> enqueue_job(
        ...     process_email_job,
        ...     email_data=email_dict,
        ...     queue_name='high',
        ...     job_timeout='15m'
        ... )
    """
    queue = get_queue(queue_name)
    return queue.enqueue(func, *args, timeout=job_timeout, **kwargs)
