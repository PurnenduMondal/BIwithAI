import pytest
import pandas as pd
from app.services.data_ingestion.schema_detector import SchemaDetector

def test_detect_numeric_metric():
    """Test detection of numeric metrics"""
    df = pd.DataFrame({
        'revenue': [100, 200, 300, 400, 500],
        'quantity': [1, 2, 3, 4, 5]
    })
    
    detector = SchemaDetector()
    schema = detector.detect_schema(df)
    
    assert 'revenue' in schema['metrics']
    assert schema['metrics']['revenue']['semantic_type'] == 'metric'
    assert 'mean' in schema['metrics']['revenue']

def test_detect_categorical_dimension():
    """Test detection of categorical dimensions"""
    df = pd.DataFrame({
        'category': ['A', 'B', 'A', 'C', 'B'],
        'region': ['East', 'West', 'East', 'North', 'West']
    })
    
    detector = SchemaDetector()
    schema = detector.detect_schema(df)
    
    assert 'category' in schema['dimensions']
    assert schema['dimensions']['category']['semantic_type'] == 'categorical'
    assert schema['dimensions']['category']['cardinality'] == 'low'

def test_detect_time_column():
    """Test detection of time column"""
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'value': range(10)
    })
    
    detector = SchemaDetector()
    schema = detector.detect_schema(df)
    
    assert schema['time_column'] == 'date'

def test_detect_outliers():
    """Test outlier detection"""
    df = pd.DataFrame({
        'normal_data': [10, 12, 11, 13, 12, 11, 10, 12],
        'outlier_data': [10, 12, 11, 100, 12, 11, 10, 12]  # 100 is outlier
    })
    
    detector = SchemaDetector()
    schema = detector.detect_schema(df)
    
    assert schema['metrics']['outlier_data']['outliers']['count'] > 0