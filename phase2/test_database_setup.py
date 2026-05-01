import sqlite3
import pandas as pd
import pytest
from database_setup import setup_database, ingest_data, filter_restaurants

@pytest.fixture
def memory_db():
    """Fixture to create an in-memory SQLite DB for testing."""
    conn = sqlite3.connect(':memory:')
    setup_database(conn)
    yield conn
    conn.close()

def test_database_setup(memory_db):
    """Test if the table is created successfully."""
    cursor = memory_db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='restaurants';")
    table_exists = cursor.fetchone()
    assert table_exists is not None

def test_ingest_data(memory_db, tmp_path):
    """Test data ingestion using a dynamically created mock CSV file."""
    # Create mock CSV
    mock_df = pd.DataFrame({
        'name': ['Test Rest 1', 'Test Rest 2'],
        'rate': [4.5, 3.8],
        'location': ['Location A', 'Location B'],
        'cuisines': ['Italian, Pizza', 'Chinese'],
        'approx_cost(for two people)': [1000.0, 500.0],
        'rest_type': ['Casual Dining', 'Quick Bites']
    })
    
    mock_csv_path = tmp_path / "mock_cleaned_zomato.csv"
    mock_df.to_csv(mock_csv_path, index=False)
    
    # Ingest data into memory DB
    success = ingest_data(memory_db, str(mock_csv_path))
    assert success is True
    
    # Verify insertion count
    cursor = memory_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM restaurants;")
    count = cursor.fetchone()[0]
    assert count == 2

def test_filter_restaurants(memory_db):
    """Test the SQL filtering logic with mock inserted data."""
    # Insert direct data bypassing the CSV ingest function for this specific test
    mock_df = pd.DataFrame({
        'name': ['Good Pizza', 'Cheap Chinese', 'Expensive Italian', 'Bad Pizza'],
        'rate': [4.5, 3.8, 4.8, 2.5],
        'location': ['Downtown', 'Downtown', 'Uptown', 'Downtown'],
        'cuisines': ['Italian, Pizza', 'Chinese', 'Italian', 'Pizza'],
        'approx_cost': [800.0, 300.0, 2000.0, 500.0]
    })
    mock_df.to_sql('restaurants', memory_db, if_exists='append', index=False)
    
    # Filter 1: High rating pizza downtown
    results1 = filter_restaurants(memory_db, min_rate=4.0, location='Downtown', cuisine='Pizza')
    assert len(results1) == 1
    assert results1.iloc[0]['name'] == 'Good Pizza'
    
    # Filter 2: Cheap food (cost <= 600)
    results2 = filter_restaurants(memory_db, max_cost=600.0)
    assert len(results2) == 2
    assert 'Cheap Chinese' in results2['name'].values
    assert 'Bad Pizza' in results2['name'].values
