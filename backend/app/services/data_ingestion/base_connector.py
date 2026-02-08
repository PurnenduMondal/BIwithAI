from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

class BaseConnector(ABC):
    """Base class for data source connectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is valid"""
        pass
    
    @abstractmethod
    async def fetch_data(self) -> pd.DataFrame:
        """Fetch data from source"""
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """Get schema information"""
        pass