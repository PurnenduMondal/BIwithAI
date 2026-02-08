"""
Celery workers package
Import tasks here to ensure they're registered
"""
from app.workers.celery_app import celery_app

# Import all task modules to ensure they're registered
from app.workers import data_sync
from app.workers import dashboard_generation
from app.workers import data_sync as sync_tasks
from app.workers import export_tasks

__all__ = ['celery_app', 'data_sync', 'dashboard_generation', 'export_tasks']
