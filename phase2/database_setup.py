import sqlite3
import pandas as pd
import os

DB_NAME = "zomato.db"

def create_connection(db_file=DB_NAME):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
    return conn

def setup_database(conn):
    """Creates the restaurants table if it doesn't exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rate REAL,
        location TEXT NOT NULL,
        cuisines TEXT NOT NULL,
        approx_cost REAL,
        rest_type TEXT
    );
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        conn.commit()
        print("Database schema verified/created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")

def ingest_data(conn, csv_file_path="../phase1/cleaned_zomato.csv"):
    """Reads the cleaned CSV and inserts data into the database."""
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found at {csv_file_path}. Please run Phase 1 first or provide valid mock data.")
        return False
        
    try:
        df = pd.read_csv(csv_file_path)
        
        # Rename columns to match the SQLite table schema
        # Map 'approx_cost(for two people)' to 'approx_cost'
        if 'approx_cost(for two people)' in df.columns:
            df.rename(columns={'approx_cost(for two people)': 'approx_cost'}, inplace=True)
            
        # Select the relevant columns
        cols_to_insert = ['name', 'rate', 'location', 'cuisines', 'approx_cost']
        if 'rest_type' in df.columns:
            cols_to_insert.append('rest_type')
            
        df_to_insert = df[[col for col in cols_to_insert if col in df.columns]]
        
        # Clear existing data to avoid duplicates on re-run (optional, but good for idempotency)
        conn.execute("DELETE FROM restaurants;")
        
        # Insert data into sqlite
        df_to_insert.to_sql('restaurants', conn, if_exists='append', index=False)
        print(f"Successfully ingested {len(df_to_insert)} records into the database.")
        return True
    except Exception as e:
        print(f"Error ingesting data: {e}")
        return False

def filter_restaurants(conn, min_rate=None, max_cost=None, location=None, cuisine=None):
    """A sample query function to filter restaurants before sending to LLM."""
    query = "SELECT * FROM restaurants WHERE 1=1"
    params = []
    
    if min_rate:
        query += " AND rate >= ?"
        params.append(min_rate)
    if max_cost:
        query += " AND approx_cost <= ?"
        params.append(max_cost)
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if cuisine:
        query += " AND cuisines LIKE ?"
        params.append(f"%{cuisine}%")
        
    df = pd.read_sql_query(query, conn, params=params)
    return df

if __name__ == '__main__':
    print("Starting Phase 2: Database Setup & Data Ingestion...")
    conn = create_connection()
    if conn is not None:
        setup_database(conn)
        ingest_data(conn)
        
        # Example Test Query if data was ingested
        print("\n--- Example Query ---")
        print("Looking for: location='Banashankari', rating >= 4.0, cost <= 800")
        results = filter_restaurants(conn, min_rate=4.0, max_cost=800, location="Banashankari")
        if not results.empty:
            print(results.head())
        else:
            print("No results found or dataset is not ingested yet.")
            
        conn.close()
