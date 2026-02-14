# ========================================
# AI2BI - Backend Setup & Commands
# ========================================

# Navigate to backend directory
cd c:\Users\Purnendu\Documents\FinsEdSoft\Code\BIwithAI\backend

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies (if not already done)
pip install -r requirements.txt

# ========================================
# STARTING SERVICES
# ========================================

# Terminal 1: Start Redis (in WSL)
wsl
sudo service redis-server start
# Verify Redis is running:
redis-cli ping
# Should return: PONG

# Terminal 2: Start FastAPI server
uvicorn app.main:app --reload

# Terminal 3: Start Celery Worker
celery -A app.workers.celery_app worker --loglevel=info --pool=solo

# ========================================
# TESTING & DEBUGGING CELERY
# ========================================

# 1. Test Celery setup (run from backend directory)
python test_celery.py

# 2. Test via API endpoints (after logging in):
# GET  http://localhost:8000/api/v1/debug/celery-status
# POST http://localhost:8000/api/v1/debug/test-celery
# GET  http://localhost:8000/api/v1/debug/task-status/{task_id}

# 3. Monitor Celery worker logs in real-time
#    Watch Terminal 3 for task execution logs

# 4. Check Redis directly (in WSL)
redis-cli
KEYS *                    # See all keys
LLEN celery               # Check queue length
KEYS celery-task-meta-*   # See task results

# ========================================
# TROUBLESHOOTING
# ========================================

# If tasks aren't being picked up:
# 1. Make sure Redis is running
redis-cli ping

# 2. Make sure Celery worker is running and ready
#    Look for: "celery@LAPTOP-0TMTR1FT ready."

# 3. Check if tasks are registered
celery -A app.workers.celery_app inspect registered

# 4. Check active workers
celery -A app.workers.celery_app inspect active

# 5. Purge all pending tasks (if stuck)
celery -A app.workers.celery_app purge

# 6. Check database for data source status
#    Status should change: PENDING -> SYNCING -> ACTIVE

# ========================================
# TEST CREDENTIALS
# ========================================
purnendu5031@gmail.com
P@$$w0rd

test@example.com
testuser2@example.com
testuser3@example.com
Test123!@#