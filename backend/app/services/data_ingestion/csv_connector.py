from typing import Dict, Any
import pandas as pd
import os

from app.services.data_ingestion.base_connector import BaseConnector

class CSVConnector(BaseConnector):
    """Connector for CSV files"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.file_path = config.get('file_path')
    
    async def test_connection(self) -> bool:
        """Test if CSV file exists and is readable"""
        try:
            if not os.path.exists(self.file_path):
                return False
            
            # Try reading first few rows
            pd.read_csv(self.file_path, nrows=5)
            return True
        except Exception:
            return False
    
    async def fetch_data(self) -> pd.DataFrame:
        """Read CSV file into DataFrame"""
        try:
            # Read CSV with automatic type inference
            df = pd.read_csv(
                self.file_path,
                encoding=self.config.get('encoding', 'utf-8'),
                sep=self.config.get('separator', ','),
                thousands=self.config.get('thousands', None),
                decimal=self.config.get('decimal', '.'),
                parse_dates=True  # Datetime format inference is now automatic
            )
            
            return df
        except Exception as e:
            raise Exception(f"Failed to read CSV: {str(e)}")
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get CSV schema"""
        df = await self.fetch_data()
        
        schema = {
            'columns': [],
            'row_count': len(df),
            'file_size': os.path.getsize(self.file_path)
        }
        
        for col in df.columns:
            schema['columns'].append({
                'name': col,
                'type': str(df[col].dtype),
                'null_count': int(df[col].isnull().sum()),
                'unique_count': int(df[col].nunique())
            })
        
        return schema