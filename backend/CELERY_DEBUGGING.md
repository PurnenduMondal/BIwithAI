# 🐛 Celery Debugging Guide

## The Problem You Had

You were using **FastAPI's `BackgroundTasks`** instead of **Celery**. This meant:
- Tasks ran in the same process as your API (not in Celery workers)
- Celery workers were idle because no tasks were being sent to them
- The worker showed "ready" but had nothing to do

## ✅ What I Fixed

### 1. **Replaced BackgroundTasks with Celery** 
Changed from:
```python
background_tasks.add_task(process_data_source, str(data_source.id))
```
To:
```python
process_data_source.delay(str(data_source.id))  # Queues to Celery
```

### 2. **Removed BackgroundTasks Import**
No longer needed in `data_sources.py`

### 3. **Added Task ID Tracking**
Now returns task IDs so you can monitor progress

---

## 🧪 How to Test Celery (Step-by-Step)

### Step 1: Run the Diagnostic Script

Open a terminal in the backend directory:
```bash
cd c:\Users\Purnendu\Documents\FinsEdSoft\Code\BIwithAI\backend
.\venv\Scripts\activate
python test_celery.py
```

**What to look for:**
- ✅ All 4 tests should pass
- If any fail, it will tell you what's wrong

**Common Issues:**
- ❌ Redis connection fails → Start Redis first
- ❌ No workers found → Start Celery worker
- ❌ No tasks registered → Check autodiscovery

---

### Step 2: Test via API

1. **Start all services** (3 terminals):

**Terminal 1 - Redis:**
```bash
wsl
sudo service redis-server start
redis-cli ping  # Should return PONG
```

**Terminal 2 - FastAPI:**
```bash
cd c:\Users\Purnendu\Documents\FinsEdSoft\Code\BIwithAI\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 3 - Celery Worker:**
```bash
cd c:\Users\Purnendu\Documents\FinsEdSoft\Code\BIwithAI\backend
.\venv\Scripts\activate
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

2. **Login to your API** (get auth token)

3. **Test the debug endpoints:**

**Check worker status:**
```bash
GET http://localhost:8000/api/v1/debug/celery-status
Authorization: Bearer YOUR_TOKEN
```

**Send a test task:**
```bash
POST http://localhost:8000/api/v1/debug/test-celery
Authorization: Bearer YOUR_TOKEN
```

**Check task status:**
```bash
GET http://localhost:8000/api/v1/debug/task-status/{task_id}
Authorization: Bearer YOUR_TOKEN
```

---

### Step 3: Test CSV Upload (Real Use Case)

1. **Upload a CSV file:**
```bash
POST http://localhost:8000/api/v1/data-sources/upload-csv
Authorization: Bearer YOUR_TOKEN
Content-Type: multipart/form-data

file: [your_csv_file.csv]
name: "Test Data Source"
```

2. **Watch the Celery worker logs** (Terminal 3):
You should see:
```
[2026-02-09 00:15:23,456: INFO/MainProcess] Task app.workers.data_sync.process_data_source[abc-123] received
[2026-02-09 00:15:24,789: INFO/MainProcess] Fetching data for Test Data Source (csv)
[2026-02-09 00:15:25,123: INFO/MainProcess] Fetched 100 rows, 5 columns
[2026-02-09 00:15:26,456: INFO/MainProcess] Task app.workers.data_sync.process_data_source[abc-123] succeeded
```

3. **Check the database:**
```sql
SELECT id, name, status FROM data_sources ORDER BY created_at DESC LIMIT 1;
```
Status should be: `PENDING` → `SYNCING` → `ACTIVE`

4. **Check for Dataset record:**
```sql
SELECT * FROM datasets WHERE data_source_id = 'your-data-source-id';
```

---

### Step 4: Monitor Tasks in Real-Time

Run the monitoring script:
```bash
python monitor_celery.py
```

This will show:
- New tasks as they're queued
- Task states (pending, running, success, failed)
- Queue length
- Task results

---

## 🔍 Debugging Commands

### Check if Redis is Running
```bash
wsl
redis-cli ping
```

### Check Queue Length
```bash
redis-cli
LLEN celery
```

### View All Task Results
```bash
redis-cli
KEYS celery-task-meta-*
```

### Check Registered Tasks
```bash
celery -A app.workers.celery_app inspect registered
```

### Check Active Tasks
```bash
celery -A app.workers.celery_app inspect active
```

### Check Worker Stats
```bash
celery -A app.workers.celery_app inspect stats
```

### Purge All Pending Tasks
```bash
celery -A app.workers.celery_app purge
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "No active workers"
**Cause:** Celery worker not running
**Solution:** 
```bash
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

### Issue 2: "Cannot connect to Redis"
**Cause:** Redis not running
**Solution:**
```bash
wsl
sudo service redis-server start
```

### Issue 3: "Task not registered"
**Cause:** Autodiscovery not working
**Solution:** Check that:
- Task has `@shared_task` decorator
- Task is in `app/workers/` directory
- `celery_app.autodiscover_tasks(['app.workers'])` is present

### Issue 4: Tasks stuck in PENDING state
**Cause:** Worker crashed or not picking up tasks
**Solution:**
1. Restart Celery worker
2. Check worker logs for errors
3. Purge stuck tasks: `celery -A app.workers.celery_app purge`

### Issue 5: "Dataset not created"
**Check these:**
1. Task completed successfully (check worker logs)
2. Database connection working (check DB URL)
3. File permissions (can worker read uploaded CSV?)
4. Storage directory exists (check `settings.UPLOAD_DIR`)

---

## 📊 Expected Workflow

```
1. User uploads CSV via API
   ↓
2. API saves file and creates DataSource record (status=PENDING)
   ↓
3. API calls: process_data_source.delay(data_source_id)
   ↓
4. Task is serialized and sent to Redis queue
   ↓
5. Celery worker picks up task from Redis
   ↓
6. Worker executes process_data_source(data_source_id)
   ↓
7. Worker updates status: PENDING → SYNCING
   ↓
8. Worker reads CSV, detects schema, saves to Parquet
   ↓
9. Worker creates Dataset record
   ↓
10. Worker updates status: SYNCING → ACTIVE
    ↓
11. Result stored in Redis (celery-task-meta-{task_id})
```

---

## 📝 Monitoring Checklist

Before uploading CSV:
- [ ] Redis is running (`redis-cli ping`)
- [ ] FastAPI is running (http://localhost:8000/docs)
- [ ] Celery worker is running and shows "ready"
- [ ] You're logged in and have auth token

After uploading CSV:
- [ ] API returns 201 Created with data_source object
- [ ] Celery worker logs show task received
- [ ] Worker logs show "Fetching data..."
- [ ] Worker logs show "Fetched X rows, Y columns"
- [ ] Worker logs show task succeeded
- [ ] Database shows data_source status = ACTIVE
- [ ] Database shows dataset record created

If any step fails:
- Check worker logs for error message
- Check FastAPI logs
- Check Redis connection
- Run diagnostic script: `python test_celery.py`

---

## 🎯 Quick Test

**Fastest way to verify everything works:**

1. Start services (Redis, FastAPI, Celery)
2. Run: `python test_celery.py`
3. If all pass → Test CSV upload
4. If any fail → Check the specific test that failed

**Success indicators:**
- `test_celery.py` shows 4/4 tests passed
- Worker logs show task execution
- Data source status changes to ACTIVE
- Dataset record created in database

---

## 📚 Additional Resources

- **Celery Docs:** https://docs.celeryq.dev/
- **Redis CLI Guide:** https://redis.io/docs/manual/cli/
- **FastAPI Background Tasks:** https://fastapi.tiangolo.com/tutorial/background-tasks/

---

**Remember:** With Celery properly configured:
- Tasks run **asynchronously** in worker processes
- API responds immediately (doesn't wait for processing)
- Workers can be **scaled horizontally** (multiple workers)
- Tasks are **retried** on failure (configured in @shared_task)
- You can **monitor** task progress in real-time
