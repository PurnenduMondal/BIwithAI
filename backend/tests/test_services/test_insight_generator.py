import pytest
import pandas as pd
from app.services.ai.insight_generator import InsightGenerator

@pytest.mark.asyncio
async def test_statistical_insights():
    """Test generation of statistical insights"""
    df = pd.DataFrame({
        'revenue': [100, 200, 300, 1000, 250],  # 1000 is outlier
        'quantity': [10, 20, 30, 40, 50]
    })
    
    schema = {
        'metrics': {
            'revenue': {
                'outliers': {'count': 1, 'percentage': 20.0},
                'null_percentage': 0
            }
        }
    }
    
    generator = InsightGenerator()
    insights = generator._statistical_insights(df, schema)
    
    assert len(insights) > 0
    assert any(i['type'] == 'anomaly' for i in insights)

@pytest.mark.asyncio
async def test_trend_insights():
    """Test trend detection"""
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'sales': [100, 120, 140, 160, 180, 200, 220, 240, 260, 280]  # Strong upward trend
    })
    
    schema = {
        'time_column': 'date',
        'metrics': {
            'sales': {}
        }
    }
    
    generator = InsightGenerator()
    insights = generator._trend_insights(df, schema)
    
    assert len(insights) > 0
    assert any('increasing' in i['description'].lower() for i in insights)