from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pandas as pd
import asyncio
import logging
from uuid import UUID

from app.config import settings

# Import all models FIRST to ensure relationships are registered
from app.models import Dashboard, Widget, DataSource, Dataset

from app.services.dashboard.generator import DashboardGenerator

logger = logging.getLogger(__name__)

# Create async engine for Celery tasks (after models are imported)
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@shared_task(bind=True)
def generate_dashboard_task(self, dashboard_id: str, data_source_id: str, preferences: dict):
    """Generate dashboard content asynchronously"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        _generate_dashboard_async(dashboard_id, data_source_id, preferences)
    )

async def _generate_dashboard_async(dashboard_id: str, data_source_id: str, preferences: dict):
    """Generate dashboard widgets and layout"""
    async with AsyncSessionLocal() as session:
        try:
            # Get dashboard
            dashboard_result = await session.execute(
                select(Dashboard).where(Dashboard.id == UUID(dashboard_id))
            )
            dashboard = dashboard_result.scalar_one_or_none()
            
            if not dashboard:
                logger.error(f"Dashboard {dashboard_id} not found")
                return {'status': 'error', 'message': 'Dashboard not found'}
            
            # Get data source and latest dataset
            ds_result = await session.execute(
                select(DataSource).where(DataSource.id == UUID(data_source_id))
            )
            data_source = ds_result.scalar_one_or_none()
            
            if not data_source:
                return {'status': 'error', 'message': 'Data source not found'}
            
            # Get latest dataset
            dataset_result = await session.execute(
                select(Dataset)
                .where(Dataset.data_source_id == data_source.id)
                .order_by(Dataset.version.desc())
                .limit(1)
            )
            dataset = dataset_result.scalar_one_or_none()
            
            if not dataset:
                return {'status': 'error', 'message': 'No dataset available'}
            
            # Load data
            logger.info(f"Loading dataset from {dataset.storage_path}")
            df = pd.read_parquet(dataset.storage_path)
            
            # Generate dashboard
            generator = DashboardGenerator()
            dashboard_config = await generator.generate_dashboard(df, preferences)
            
            # Update dashboard
            dashboard.name = dashboard_config['name']
            dashboard.description = dashboard_config['description']
            dashboard.layout_config = dashboard_config['layout_config']
            dashboard.filters = dashboard_config['filters']
            dashboard.theme = dashboard_config['theme']
            
            # Create widgets
            for widget_data in dashboard_config['widgets']:
                widget = Widget(
                    dashboard_id=dashboard.id,
                    data_source_id=data_source.id,
                    widget_type=widget_data['type'],
                    title=widget_data['title'],
                    position=widget_data['position'],
                    config=widget_data['config']
                )
                session.add(widget)
            
            await session.commit()
            
            logger.info(f"Successfully generated dashboard {dashboard.name}")
            
            return {
                'status': 'success',
                'dashboard_id': str(dashboard.id),
                'widgets_created': len(dashboard_config['widgets'])
            }
        
        except Exception as e:
            logger.error(f"Error generating dashboard: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}