from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
import logging
from datetime import datetime
from uuid import UUID
import os
import io

from app.config import settings

# Import all models FIRST to ensure relationships are registered
from app.models import Dashboard, Widget

from app.services.cache.redis_cache import RedisCache
from app.services.dashboard.export_service import ExportService
from app.services.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)

# Create async engine for Celery tasks (after models are imported)
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
cache = RedisCache()

@shared_task(bind=True)
def export_dashboard_task(self, job_id: str, dashboard_id: str, format: str, user_id: str):
    """Export dashboard - Celery wrapper"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _export_dashboard_async(job_id, dashboard_id, format, user_id)
        )
    finally:
        loop.close()

def export_dashboard_task_sync(job_id: str, dashboard_id: str, format: str, user_id: str):
    """Export dashboard - BackgroundTasks wrapper"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _export_dashboard_async(job_id, dashboard_id, format, user_id)
        )
    finally:
        loop.close()

async def _export_dashboard_async(job_id: str, dashboard_id: str, format: str, user_id: str):
    """Export dashboard asynchronously"""
    logger.info(f"=== EXPORT TASK STARTED === Job ID: {job_id}, Dashboard: {dashboard_id}, Format: {format}, User: {user_id}")
    try:
        # Update status to processing
        logger.info(f"Updating job {job_id} to processing status")
        await cache.set(
            f"export_job:{job_id}",
            {
                "status": "processing",
                "progress": 10,
                "format": format,
                "type": "dashboard",
                "resource_id": dashboard_id
            },
            ttl=3600
        )
        
        # Broadcast progress via websocket
        logger.info(f"Broadcasting progress 10% for job {job_id}")
        await connection_manager.broadcast_to_resource(
            "export_job",
            job_id,
            {
                "type": "export_progress",
                "job_id": job_id,
                "status": "processing",
                "progress": 10,
                "message": "Starting export..."
            }
        )
        logger.info(f"Broadcast complete for job {job_id} at 10%")
        
        async with AsyncSessionLocal() as session:
            # Get dashboard with widgets and their data sources
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(Dashboard)
                .options(selectinload(Dashboard.widgets).selectinload(Widget.data_source))
                .where(Dashboard.id == UUID(dashboard_id))
            )
            dashboard = result.scalar_one_or_none()
            
            if not dashboard:
                logger.error(f"Dashboard {dashboard_id} not found")
                raise Exception("Dashboard not found")
            
            logger.info(f"Found dashboard {dashboard.name} with {len(dashboard.widgets)} widgets")
            
            # Update progress
            await cache.set(
                f"export_job:{job_id}",
                {"status": "processing", "progress": 30},
                ttl=3600
            )
            
            # Broadcast progress via websocket
            logger.info(f"Broadcasting progress 30% for job {job_id}")
            await connection_manager.broadcast_to_resource(
                "export_job",
                job_id,
                {
                    "type": "export_progress",
                    "job_id": job_id,
                    "status": "processing",
                    "progress": 30,
                    "message": "Generating export..."
                }
            )
            
            # Export based on format
            logger.info(f"Creating export service for dashboard {dashboard_id}, format: {format}")
            export_service = ExportService(db_session=session)
            
            try:
                if format == "pdf":
                    logger.info(f"Exporting dashboard {dashboard_id} to PDF")
                    file_bytes = await export_service.export_dashboard_to_pdf(dashboard)
                    file_ext = "pdf"
                elif format == "png":
                    logger.info(f"Exporting dashboard {dashboard_id} to PNG")
                    file_bytes = await export_service.export_dashboard_to_image(dashboard, format="png")
                    file_ext = "png"
                elif format == "json":
                    logger.info(f"Exporting dashboard {dashboard_id} to JSON")
                    file_bytes = await export_service.export_dashboard_to_json(dashboard)
                    file_ext = "json"
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                logger.info(f"Export completed, file size: {len(file_bytes)} bytes")
            except Exception as export_error:
                logger.error(f"Error during export generation: {str(export_error)}", exc_info=True)
                raise
            
            # Update progress
            await cache.set(
                f"export_job:{job_id}",
                {"status": "processing", "progress": 70},
                ttl=3600
            )
            
            # Broadcast progress via websocket
            logger.info(f"Broadcasting progress 70% for job {job_id}")
            await connection_manager.broadcast_to_resource(
                "export_job",
                job_id,
                {
                    "type": "export_progress",
                    "job_id": job_id,
                    "status": "processing",
                    "progress": 70,
                    "message": "Saving file..."
                }
            )
            
            # Save file
            export_dir = os.path.join(settings.UPLOAD_DIR, "exports", user_id)
            os.makedirs(export_dir, exist_ok=True)
            
            filename = f"dashboard_{dashboard_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
            file_path = os.path.join(export_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            # Generate download URL
            download_url = f"/api/v1/downloads/{user_id}/{filename}"
            
            # Update status to completed
            await cache.set(
                f"export_job:{job_id}",
                {
                    "status": "completed",
                    "progress": 100,
                    "download_url": download_url,
                    "completed_at": datetime.utcnow().isoformat()
                },
                ttl=3600
            )
            
            # Broadcast via websocket
            logger.info(f"Broadcasting completion for job {job_id}")
            await connection_manager.broadcast_to_resource(
                "export_job",
                job_id,
                {
                    "type": "export_completed",
                    "job_id": job_id,
                    "status": "completed",
                    "download_url": download_url,
                    "format": format,
                    "resource_type": "dashboard",
                    "resource_id": dashboard_id
                }
            )
            logger.info(f"Broadcast complete for job {job_id} - completed")
            
            logger.info(f"Successfully exported dashboard {dashboard_id} to {format}")
            
            return {"status": "completed", "download_url": download_url}
    
    except Exception as e:
        logger.error(f"Error exporting dashboard: {str(e)}", exc_info=True)
        
        # Update status to failed
        await cache.set(
            f"export_job:{job_id}",
            {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            },
            ttl=3600
        )
        
        # Broadcast via websocket
        await connection_manager.broadcast_to_resource(
            "export_job",
            job_id,
            {
                "type": "export_failed",
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            }
        )
        
        return {"status": "failed", "error": str(e)}

@shared_task(bind=True)
def export_widget_task(self, job_id: str, widget_id: str, format: str, width: int, height: int, user_id: str):
    """Export widget - Celery wrapper"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _export_widget_async(job_id, widget_id, format, width, height, user_id)
        )
    finally:
        loop.close()

def export_widget_task_sync(job_id: str, widget_id: str, format: str, width: int, height: int, user_id: str):
    """Export widget - BackgroundTasks wrapper"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _export_widget_async(job_id, widget_id, format, width, height, user_id)
        )
    finally:
        loop.close()

async def _export_widget_async(job_id: str, widget_id: str, format: str, width: int, height: int, user_id: str):
    """Export widget asynchronously"""
    try:
        await cache.set(
            f"export_job:{job_id}",
            {"status": "processing", "progress": 20},
            ttl=3600
        )
        
        # Broadcast progress via websocket
        await connection_manager.broadcast_to_resource(
            "export_job",
            job_id,
            {
                "type": "export_progress",
                "job_id": job_id,
                "status": "processing",
                "progress": 20,
                "message": "Starting widget export..."
            }
        )
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(Widget)
                .options(selectinload(Widget.data_source))
                .where(Widget.id == UUID(widget_id))
            )
            widget = result.scalar_one_or_none()
            
            if not widget:
                logger.error(f"Widget {widget_id} not found")
                raise Exception("Widget not found")
            
            logger.info(f"Found widget {widget.title}")
            
            export_service = ExportService(db_session=session)
            
            if format == "png":
                file_bytes = await export_service.export_widget_to_image(widget, "png", width, height)
                file_ext = "png"
            elif format == "svg":
                file_bytes = await export_service.export_widget_to_image(widget, "svg", width, height)
                file_ext = "svg"
            elif format == "json":
                file_bytes = await export_service.export_widget_to_json(widget)
                file_ext = "json"
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Save file
            export_dir = os.path.join(settings.UPLOAD_DIR, "exports", user_id)
            os.makedirs(export_dir, exist_ok=True)
            
            filename = f"widget_{widget_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
            file_path = os.path.join(export_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            download_url = f"/api/v1/downloads/{user_id}/{filename}"
            
            await cache.set(
                f"export_job:{job_id}",
                {
                    "status": "completed",
                    "progress": 100,
                    "download_url": download_url,
                    "completed_at": datetime.utcnow().isoformat()
                },
                ttl=3600
            )
            
            # Broadcast via websocket
            await connection_manager.broadcast_to_resource(
                "export_job",
                job_id,
                {
                    "type": "export_completed",
                    "job_id": job_id,
                    "status": "completed",
                    "download_url": download_url,
                    "format": format,
                    "resource_type": "widget",
                    "resource_id": widget_id
                }
            )
            
            return {"status": "completed", "download_url": download_url}
    
    except Exception as e:
        logger.error(f"Error exporting widget: {str(e)}", exc_info=True)
        
        await cache.set(
            f"export_job:{job_id}",
            {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            },
            ttl=3600
        )
        
        # Broadcast via websocket
        await connection_manager.broadcast_to_resource(
            "export_job",
            job_id,
            {
                "type": "export_failed",
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            }
        )
        
        return {"status": "failed", "error": str(e)}