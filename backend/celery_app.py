"""Celery application configuration for async task processing."""

from celery import Celery
import os
from kombu import Queue

# Create Celery instance
celery_app = Celery(
    'rag_chatbot',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    'backend.tasks.process_document_task': {'queue': 'documents'},
    'backend.tasks.generate_embeddings_task': {'queue': 'embeddings'},
    'backend.tasks.send_email_task': {'queue': 'emails'},
    'backend.tasks.cleanup_old_data': {'queue': 'maintenance'},
}

# Queues
celery_app.conf.task_queues = (
    Queue('default'),
    Queue('documents', routing_key='document.#'),
    Queue('embeddings', routing_key='embedding.#'),
    Queue('emails', routing_key='email.#'),
    Queue('maintenance', routing_key='maintenance.#'),
)

