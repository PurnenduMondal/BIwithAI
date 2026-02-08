from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pandas as pd
import asyncio
import logging
from datetime import datetime
from uuid import UUID

from app.config import settings

# Import all models FIRST to ensure relationships are registered
from app.models import DataSource, Dataset, DataSourceStatus

from app.services.data_ingestion.csv_connector import CSVConnector
from app.services.data_ingestion.database_connector import DatabaseConnector
from app.services.data_ingestion.schema_detector import SchemaDetector
from app.services.websocket.connection_manager import connection_manager
from app.utils.encryption import decrypt_dict
import os

logger = logging.getLogger(__name__)

# Create async engine for Celery tasks (after models are imported)
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@shared_task(bind=True, max_retries=3)
def process_data_source(self, data_source_id: str):
    """Process data source synchronously (Celery wrapper)"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_process_data_source_async(data_source_id))

async def _process_data_source_async(data_source_id: str):
    """Process data source - fetch, clean, analyze, store"""
    async with AsyncSessionLocal() as session:
        try:
            # Get data source
            result = await session.execute(
                select(DataSource).where(DataSource.id == UUID(data_source_id))
            )
            data_source = result.scalar_one_or_none()
            
            if not data_source:
                logger.error(f"Data source {data_source_id} not found")
                return {'status': 'error', 'message': 'Data source not found'}
            
            # Update status - Use underlying column
            data_source._status = DataSourceStatus.SYNCING.value
            await session.commit()
            
            # Decrypt config
            config = decrypt_dict(data_source.connection_config)
            
            # Fetch data based on type
            logger.info(f"Fetching data for {data_source.name} ({data_source.type})")
            
            if data_source.type == 'csv':
                connector = CSVConnector(config)
                df = await connector.fetch_data()
            
            elif data_source.type in ['postgresql', 'mysql']:
                connector = DatabaseConnector(data_source.type, config)
                table = config.get('table')
                query = config.get('query')
                df = await connector.fetch_data(query=query, table=table)
            
            else:
                raise ValueError(f"Unsupported data source type: {data_source.type}")
            
            logger.info(f"Fetched {len(df)} rows, {len(df.columns)} columns")
            
            # Detect schema
            schema_detector = SchemaDetector()
            schema = schema_detector.detect_schema(df)
            
            # Store schema
            data_source.schema_metadata = schema
            
            # Save to parquet
            storage_dir = os.path.join(settings.UPLOAD_DIR, str(data_source.org_id), 'datasets')
            os.makedirs(storage_dir, exist_ok=True)
            
            # Get next version
            version_result = await session.execute(
                select(Dataset)
                .where(Dataset.data_source_id == data_source.id)
                .order_by(Dataset.version.desc())
                .limit(1)
            )
            last_dataset = version_result.scalar_one_or_none()
            next_version = (last_dataset.version + 1) if last_dataset else 1
            
            # Storage path
            storage_path = os.path.join(
                storage_dir,
                f"{data_source_id}_v{next_version}.parquet"
            )
            
            # Save as parquet
            df.to_parquet(storage_path, index=False, compression='snappy')
            
            # Create dataset record
            dataset = Dataset(
                data_source_id=data_source.id,
                version=next_version,
                row_count=len(df),
                column_count=len(df.columns),
                data_profile=schema,
                storage_path=storage_path
            )
            
            session.add(dataset)
            
            # Update data source - Use underlying column
            data_source._status = DataSourceStatus.ACTIVE.value
            data_source.last_sync = datetime.utcnow()
            
            await session.commit()
            
            # Broadcast datasource update via websocket
            await connection_manager.broadcast_to_resource(
                "datasource",
                data_source_id,
                {
                    "type": "datasource_updated",
                    "datasource_id": data_source_id,
                    "status": "active",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Successfully processed data source {data_source.name}")
            
            return {
                'status': 'success',
                'rows': len(df),
                'columns': len(df.columns),
                'version': next_version
            }
        
        except Exception as e:
            logger.error(f"Error processing data source: {str(e)}", exc_info=True)
            
            # Update status to error - Use underlying column
            if data_source:
                data_source._status = DataSourceStatus.ERROR.value
                await session.commit()
            
            return {
                'status': 'error',
                'message': str(e)
            }

@shared_task
def sync_all_data_sources():
    """Periodic task to sync all active data sources"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_sync_all_data_sources_async())

async def _sync_all_data_sources_async():
    """Sync all data sources that need updating"""
    async with AsyncSessionLocal() as session:
        from datetime import timedelta
        
        # Get data sources that need syncing
        now = datetime.utcnow()
        
        result = await session.execute(
            select(DataSource)
            .where(DataSource.is_active == True)
            .where(DataSource.status != DataSourceStatus.SYNCING)
            .where(DataSource.sync_frequency != 'manual')
        )
        
        data_sources = result.scalars().all()
        
        synced_count = 0
        
        for ds in data_sources:
            # Check if sync is needed
            should_sync = False
            
            if not ds.last_sync:
                should_sync = True
            else:
                time_since_sync = now - ds.last_sync
                
                if ds.sync_frequency == 'hourly' and time_since_sync > timedelta(hours=1):
                    should_sync = True
                elif ds.sync_frequency == 'daily' and time_since_sync > timedelta(days=1):
                    should_sync = True
                elif ds.sync_frequency == 'weekly' and time_since_sync > timedelta(weeks=1):
                    should_sync = True
            
            if should_sync:
                # Trigger sync task
                process_data_source.delay(str(ds.id))
                synced_count += 1
        
        logger.info(f"Triggered sync for {synced_count} data sources")
        
        return {'synced_count': synced_count}