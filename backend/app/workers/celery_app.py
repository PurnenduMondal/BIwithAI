from celery import Celery
from app.config import settings

celery_app = Celery(
    'bi_dashboard',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

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

# Import tasks to register them
# Must import after celery_app is created to avoid circular imports
from app.workers import data_sync, dashboard_generation, export_tasks

# Auto-discover tasks (backup, but explicit imports above ensure registration)
celery_app.autodiscover_tasks(['app.workers'])