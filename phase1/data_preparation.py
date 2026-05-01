import pandas as pd
import os
from datasets import load_dataset

def fetch_data():
    """Fetches the dataset from Hugging Face and returns a Pandas DataFrame."""
    print("Downloading dataset from Hugging Face...")
    dataset = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")
    return pd.DataFrame(dataset)

def clean_data(df):
    """Cleans the raw dataframe."""
    print("Cleaning dataset...")
    # Lowercase column names for consistency
    df.columns = [col.lower().strip() for col in df.columns]

    # Clean the 'rate' column (e.g., '4.1/5' -> 4.1)
    if 'rate' in df.columns:
        df['rate'] = df['rate'].astype(str).str.replace('/5', '', regex=False).str.strip()
        df['rate'] = pd.to_numeric(df['rate'], errors='coerce')

    # Clean the 'approx_cost(for two people)' column (e.g., '1,200' -> 1200.0)
    if 'approx_cost(for two people)' in df.columns:
        df['approx_cost(for two people)'] = df['approx_cost(for two people)'].astype(str).str.replace(',', '', regex=False)
        df['approx_cost(for two people)'] = pd.to_numeric(df['approx_cost(for two people)'], errors='coerce')

    # Drop rows where critical information is missing
    required_cols = [col for col in ['name', 'location', 'cuisines'] if col in df.columns]
    if required_cols:
        df = df.dropna(subset=required_cols)

    return df

def process_pipeline(output_path="cleaned_zomato.csv"):
    """Runs the full pipeline: Fetch -> Clean -> Export."""
    try:
        df = fetch_data()
        cleaned_df = clean_data(df)
        
        cleaned_df.to_csv(output_path, index=False)
        print(f"Data processing complete. Exported {len(cleaned_df)} rows to {output_path}")
        return True
    except Exception as e:
        print(f"Pipeline failed: {e}")
        return False

if __name__ == "__main__":
    process_pipeline()
