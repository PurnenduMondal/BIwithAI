from typing import Dict, Any
import pandas as pd
from sqlalchemy import create_engine, text
import asyncio

from app.services.data_ingestion.base_connector import BaseConnector

class DatabaseConnector(BaseConnector):
    """Connector for SQL databases (PostgreSQL, MySQL)"""
    
    def __init__(self, db_type: str, config: Dict[str, Any]):
        super().__init__(config)
        self.db_type = db_type
        self.connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build database connection string"""
        host = self.config.get('host')
        port = self.config.get('port')
        database = self.config.get('database')
        username = self.config.get('username')
        password = self.config.get('password')
        
        if self.db_type == 'postgresql':
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif self.db_type == 'mysql':
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            engine = create_engine(self.connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return True
        except Exception:
            return False
    
    async def fetch_data(self, query: str = None, table: str = None) -> pd.DataFrame:
        """Fetch data from database"""
        if not query and not table:
            raise ValueError("Either query or table must be provided")
        
        if not query:
            query = f"SELECT * FROM {table}"
        
        try:
            engine = create_engine(self.connection_string)
            df = pd.read_sql(query, engine)
            engine.dispose()
            return df
        except Exception as e:
            raise Exception(f"Failed to fetch data: {str(e)}")
    
    async def get_schema(self, table: str = None) -> Dict[str, Any]:
        """Get database schema"""
        try:
            engine = create_engine(self.connection_string)
            
            if table:
                # Get schema for specific table
                df = pd.read_sql(f"SELECT * FROM {table} LIMIT 0", engine)
                schema = {
                    'table': table,
                    'columns': [
                        {
                            'name': col,
                            'type': str(df[col].dtype)
                        }
                        for col in df.columns
                    ]
                }
            else:
                # Get list of all tables
                if self.db_type == 'postgresql':
                    query = """
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """
                else:  # mysql
                    query = "SHOW TABLES"
                
                tables_df = pd.read_sql(query, engine)
                schema = {
                    'tables': tables_df.iloc[:, 0].tolist()
                }
            
            engine.dispose()
            return schema
        except Exception as e:
            raise Exception(f"Failed to get schema: {str(e)}")