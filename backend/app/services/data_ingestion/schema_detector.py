import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

class SchemaDetector:
    """Automatically detects schema and metadata from datasets"""
    
    def detect_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Main method to analyze and detect schema"""
        schema = {
            'columns': [],
            'row_count': len(df),
            'column_count': len(df.columns),
            'relationships': [],
            'metrics': {},
            'dimensions': {},
            'time_column': None
        }
        
        for column in df.columns:
            column_info = self._analyze_column(df[column], column)
            schema['columns'].append(column_info)
            
            # Categorize as metric or dimension
            if column_info['semantic_type'] == 'metric':
                schema['metrics'][column] = column_info
            else:
                schema['dimensions'][column] = column_info
        
        # Detect time column
        schema['time_column'] = self._detect_time_column(df)
        
        # Detect relationships
        schema['relationships'] = self._detect_relationships(df)
        
        return schema
    
    def _analyze_column(self, series: pd.Series, name: str) -> Dict:
        """Analyze individual column"""
        analysis = {
            'name': name,
            'data_type': str(series.dtype),
            'null_count': int(series.isnull().sum()),
            'null_percentage': float(series.isnull().sum() / len(series) * 100),
            'unique_count': int(series.nunique()),
            'cardinality': 'high' if series.nunique() > len(series) * 0.5 else 'low'
        }
        
        # Infer semantic type
        analysis['semantic_type'] = self._infer_semantic_type(series, name)
        
        # Type-specific analysis
        if pd.api.types.is_numeric_dtype(series):
            analysis.update(self._analyze_numeric(series))
        elif pd.api.types.is_datetime64_any_dtype(series):
            analysis.update(self._analyze_datetime(series))
        else:
            analysis.update(self._analyze_categorical(series))
        
        return analysis
    
    def _infer_semantic_type(self, series: pd.Series, name: str) -> str:
        """Infer what the column represents"""
        name_lower = name.lower()
        
        # Temporal
        if any(kw in name_lower for kw in ['date', 'time', 'timestamp', 'created', 'updated']):
            return 'temporal'
        
        # Identifier
        if any(kw in name_lower for kw in ['id', 'key', 'code', 'uuid']):
            return 'identifier'
        
        # Contact
        if any(kw in name_lower for kw in ['email', 'phone', 'address']):
            return 'contact'
        
        # Numeric columns
        if pd.api.types.is_numeric_dtype(series):
            # Metrics
            metric_keywords = [
                'revenue', 'sales', 'amount', 'price', 'cost', 'value', 
                'total', 'count', 'quantity', 'qty', 'units', 'score',
                'rate', 'percent', 'average', 'sum'
            ]
            if any(kw in name_lower for kw in metric_keywords):
                return 'metric'
            
            # Low cardinality integers might be categorical
            if series.nunique() < 20 and all(series.dropna() == series.dropna().astype(int)):
                return 'categorical'
            
            return 'metric'
        
        # String columns
        if series.nunique() < len(series) * 0.05:  # Low cardinality
            return 'categorical'
        
        return 'text'
    
    def _analyze_numeric(self, series: pd.Series) -> Dict:
        """Analyze numeric column"""
        # Skip analysis if series is empty or all NaN
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return {
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std': None,
                'quartiles': {'q25': None, 'q75': None},
                'outliers': {'count': 0, 'percentage': 0.0}
            }
        
        return {
            'min': float(non_null_series.min()),
            'max': float(non_null_series.max()),
            'mean': float(non_null_series.mean()),
            'median': float(non_null_series.median()),
            'std': float(non_null_series.std()) if len(non_null_series) > 1 else 0.0,
            'quartiles': {
                'q25': float(non_null_series.quantile(0.25)),
                'q75': float(non_null_series.quantile(0.75))
            },
            'outliers': self._detect_outliers(non_null_series)
        }
    
    def _analyze_datetime(self, series: pd.Series) -> Dict:
        """Analyze datetime column"""
        return {
            'min_date': str(series.min()),
            'max_date': str(series.max()),
            'date_range_days': (series.max() - series.min()).days,
            'granularity': self._detect_time_granularity(series)
        }
    
    def _analyze_categorical(self, series: pd.Series) -> Dict:
        """Analyze categorical column"""
        # Skip if series is empty or all NaN
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return {
                'top_values': {},
                'distribution': 'unknown'
            }
        
        value_counts = non_null_series.value_counts()
        if len(value_counts) == 0:
            return {
                'top_values': {},
                'distribution': 'unknown'
            }
        
        # Calculate distribution only if we have multiple values
        if len(value_counts) > 1 and value_counts.mean() > 0:
            distribution = 'uniform' if value_counts.std() < value_counts.mean() * 0.5 else 'skewed'
        else:
            distribution = 'uniform'
        
        return {
            'top_values': value_counts.head(10).to_dict(),
            'distribution': distribution
        }
    
    def _detect_outliers(self, series: pd.Series) -> Dict:
        """Detect outliers using IQR method"""
        # Skip if series is empty or has less than 4 values
        if len(series) < 4:
            return {
                'count': 0,
                'percentage': 0.0
            }
        
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        # Skip outlier detection if IQR is 0 (all values the same)
        if IQR == 0:
            return {
                'count': 0,
                'percentage': 0.0
            }
        
        outliers = series[(series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)]
        
        return {
            'count': len(outliers),
            'percentage': float(len(outliers) / len(series) * 100) if len(series) > 0 else 0.0
        }
    
    def _detect_time_column(self, df: pd.DataFrame) -> str:
        """Identify the primary time column"""
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        if len(datetime_cols) > 0:
            # Prefer columns with 'date' or 'time' in name
            for col in datetime_cols:
                if 'date' in col.lower() or 'time' in col.lower():
                    return col
            return datetime_cols[0]
        
        return None
    
    def _detect_time_granularity(self, series: pd.Series) -> str:
        """Detect the granularity of time data"""
        diffs = series.diff().dropna()
        median_diff = diffs.median()
        
        if median_diff < pd.Timedelta(hours=1):
            return 'minute'
        elif median_diff < pd.Timedelta(days=1):
            return 'hourly'
        elif median_diff < pd.Timedelta(days=7):
            return 'daily'
        elif median_diff < pd.Timedelta(days=32):
            return 'weekly'
        else:
            return 'monthly'
    
    def _detect_relationships(self, df: pd.DataFrame) -> List[Dict]:
        """Detect potential relationships between columns"""
        relationships = []
        
        # Look for foreign key relationships
        for col1 in df.columns:
            for col2 in df.columns:
                if col1 != col2:
                    # Skip if either column is empty or has no unique values
                    nunique_col1 = df[col1].nunique()
                    nunique_col2 = df[col2].nunique()
                    
                    if nunique_col1 == 0 or nunique_col2 == 0:
                        continue
                    
                    # Check if col1 values are subset of col2
                    if nunique_col1 < nunique_col2:
                        overlap = len(set(df[col1].dropna().unique()) & set(df[col2].dropna().unique()))
                        
                        # Prevent division by zero
                        if nunique_col1 > 0:
                            overlap_ratio = overlap / nunique_col1
                            
                            if overlap_ratio > 0.8:
                                relationships.append({
                                    'from': col1,
                                    'to': col2,
                                    'type': 'potential_fk',
                                    'confidence': overlap_ratio
                                })
        
        return relationships