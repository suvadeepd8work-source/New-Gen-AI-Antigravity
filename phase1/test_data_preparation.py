import pandas as pd
import pytest
from data_preparation import clean_data

def test_clean_data():
    """Test the data cleaning logic to ensure conversions are correct."""
    # Create a mock dataframe mimicking raw dataset
    mock_df = pd.DataFrame({
        'name': ['Restaurant A', 'Restaurant B', 'Restaurant C'],
        'rate': ['4.1/5', 'NEW', '3.5/5'],
        'location': ['Location A', 'Location B', None],
        'cuisines': ['Italian', 'Chinese', 'Cafe'],
        'approx_cost(for two people)': ['800', '1,200', '600']
    })
    
    cleaned_df = clean_data(mock_df)
    
    # Test 1: Missing value handling
    # Restaurant C has None for location, should be dropped
    assert len(cleaned_df) == 2
    
    # Test 2: Rate parsing
    # '4.1/5' -> 4.1
    assert cleaned_df.iloc[0]['rate'] == 4.1
    # 'NEW' should be coerced to NaN
    assert pd.isna(cleaned_df.iloc[1]['rate'])
    
    # Test 3: Cost parsing
    # '800' -> 800.0, '1,200' -> 1200.0
    assert cleaned_df.iloc[0]['approx_cost(for two people)'] == 800.0
    assert cleaned_df.iloc[1]['approx_cost(for two people)'] == 1200.0
