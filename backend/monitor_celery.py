"""
Real-time Celery Task Monitor
Watches for new tasks and shows their execution
"""
import time
import redis
from app.config import settings
from celery.result import AsyncResult
from app.workers.celery_app import celery_app

def monitor_tasks(interval=2):
    """Monitor Celery tasks in real-time"""
    print("=" * 70)
    print("CELERY TASK MONITOR")
    print("=" * 70)
    print("Monitoring for new tasks... (Press Ctrl+C to exit)\n")
    
    r = redis.from_url(settings.CELERY_BROKER_URL)
    seen_tasks = set()
    
    try:
        while True:
            # Get all task result keys
            task_keys = r.keys("celery-task-meta-*")
            
            for key in task_keys:
                task_id = key.decode().replace("celery-task-meta-", "")
                
                if task_id not in seen_tasks:
                    seen_tasks.add(task_id)
                    
                    # Get task result
                    task = AsyncResult(task_id, app=celery_app)
                    
                    # Print task info
                    print(f"\n📋 New Task Detected!")
                    print(f"   Task ID: {task_id}")
                    print(f"   State: {task.state}")
                    
                    if task.ready():
                        if task.successful():
                            print(f"   ✅ Result: {task.result}")
                        elif task.failed():
                            print(f"   ❌ Error: {task.result}")
                    else:
                        print(f"   ⏳ Status: Pending/Running")
            
            # Check queue length
            queue_length = r.llen("celery")
            if queue_length > 0:
                print(f"\n📦 Queue Length: {queue_length} tasks waiting")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Redis is running:")
        print("  wsl: sudo service redis-server start")

if __name__ == "__main__":
    monitor_tasks()
