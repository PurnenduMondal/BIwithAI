"""
Celery Testing and Debugging Script
Run this to test if Celery tasks are working properly
"""
import asyncio
from app.workers.data_sync import process_data_source
from app.workers.celery_app import celery_app

def test_celery_connection():
    """Test 1: Check if Celery can connect to broker"""
    print("\n=== Test 1: Celery Broker Connection ===")
    try:
        # Inspect active workers
        inspect = celery_app.control.inspect()
        
        # Check active workers
        active = inspect.active()
        if active:
            print(f"✅ Active workers found: {list(active.keys())}")
            for worker, tasks in active.items():
                print(f"   Worker: {worker}")
                print(f"   Active tasks: {len(tasks)}")
        else:
            print("❌ No active workers found")
            
        # Check registered tasks
        registered = inspect.registered()
        if registered:
            print(f"\n✅ Registered tasks:")
            for worker, tasks in registered.items():
                print(f"   Worker: {worker}")
                for task in tasks:
                    print(f"   - {task}")
        else:
            print("❌ No registered tasks found")
            
        return True
    except Exception as e:
        print(f"❌ Error connecting to Celery: {e}")
        return False

def test_send_task():
    """Test 2: Try to send a test task"""
    print("\n=== Test 2: Send Test Task ===")
    try:
        # Send a dummy task (will fail but that's OK, we're testing queuing)
        task = process_data_source.delay("test-id-12345")
        print(f"✅ Task sent successfully!")
        print(f"   Task ID: {task.id}")
        print(f"   Task State: {task.state}")
        
        # Wait a bit and check status
        print("\n   Waiting 2 seconds...")
        import time
        time.sleep(2)
        
        print(f"   Task State after 2s: {task.state}")
        if task.failed():
            print(f"   Task failed (expected): {task.result}")
        elif task.successful():
            print(f"   Task succeeded: {task.result}")
        else:
            print(f"   Task still pending/running")
            
        return True
    except Exception as e:
        print(f"❌ Error sending task: {e}")
        return False

def test_redis_connection():
    """Test 3: Check Redis connection directly"""
    print("\n=== Test 3: Redis Connection ===")
    try:
        import redis
        from app.config import settings
        
        # Parse Redis URL
        r = redis.from_url(settings.CELERY_BROKER_URL)
        
        # Test connection
        r.ping()
        print(f"✅ Redis is reachable")
        
        # Check queue
        queue_name = "celery"
        queue_length = r.llen(queue_name)
        print(f"   Queue '{queue_name}' length: {queue_length}")
        
        # Check if there are any keys
        keys = r.keys("celery-task-meta-*")
        print(f"   Task result keys: {len(keys)}")
        
        return True
    except ImportError:
        print("⚠️  Redis package not installed. Install: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        print("\n   Make sure Redis is running:")
        print("   - WSL: sudo service redis-server start")
        print("   - Docker: docker run -d -p 6379:6379 redis:alpine")
        return False

def check_task_autodiscovery():
    """Test 4: Check if tasks are properly autodiscovered"""
    print("\n=== Test 4: Task Autodiscovery ===")
    try:
        # Get all registered tasks
        all_tasks = list(celery_app.tasks.keys())
        print(f"✅ Total registered tasks: {len(all_tasks)}")
        
        # Filter our tasks
        our_tasks = [t for t in all_tasks if 'app.workers' in t]
        if our_tasks:
            print(f"\n   Our tasks found:")
            for task in our_tasks:
                print(f"   - {task}")
        else:
            print("❌ No tasks found in app.workers")
            print("\n   All registered tasks:")
            for task in all_tasks[:10]:  # Show first 10
                print(f"   - {task}")
                
        return len(our_tasks) > 0
    except Exception as e:
        print(f"❌ Error checking autodiscovery: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CELERY DEBUGGING SCRIPT")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Redis Connection", test_redis_connection()))
    results.append(("Task Autodiscovery", check_task_autodiscovery()))
    results.append(("Celery Connection", test_celery_connection()))
    results.append(("Send Test Task", test_send_task()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    passed_count = sum(1 for _, p in results if p)
    print(f"Passed: {passed_count}/{len(results)}")
    
    if passed_count == len(results):
        print("\n🎉 All tests passed! Celery should be working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
