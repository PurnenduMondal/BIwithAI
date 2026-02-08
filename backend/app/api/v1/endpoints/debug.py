"""
Debug endpoints for testing Celery tasks
"""
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User
from app.workers.data_sync import process_data_source
from app.workers.celery_app import celery_app

router = APIRouter()

@router.post("/test-celery")
async def test_celery_task(
    data_source_id: str = "test-12345",
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint to queue a Celery task
    """
    # Queue the task
    task = process_data_source.delay(data_source_id)
    
    return {
        "message": "Task queued successfully",
        "task_id": task.id,
        "task_state": task.state,
        "data_source_id": data_source_id
    }

@router.get("/celery-status")
async def celery_status(current_user: User = Depends(get_current_user)):
    """
    Check Celery worker status
    """
    try:
        inspect = celery_app.control.inspect()
        
        # Get active workers
        active = inspect.active()
        registered = inspect.registered()
        stats = inspect.stats()
        
        return {
            "active_workers": list(active.keys()) if active else [],
            "registered_tasks": registered,
            "worker_stats": stats,
            "status": "connected" if active else "no_workers"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Cannot connect to Celery. Make sure Redis and Celery worker are running."
        }

@router.get("/task-status/{task_id}")
async def task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check the status of a specific task
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "state": task.state,
        "ready": task.ready(),
        "successful": task.successful() if task.ready() else None,
        "failed": task.failed() if task.ready() else None,
    }
    
    if task.ready():
        if task.successful():
            response["result"] = task.result
        elif task.failed():
            response["error"] = str(task.result)
    
    return response
