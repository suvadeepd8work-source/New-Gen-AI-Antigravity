import os
import sqlite3
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from the .env file in the parent directory
load_dotenv(dotenv_path="../.env")

# Initialize FastAPI application
app = FastAPI(title="AI Restaurant Recommendation API")

# Add CORS middleware to allow the Phase 5 frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (e.g., file:// or local servers)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the database created in Phase 2
DB_PATH = "../phase2/zomato.db"

# Initialize the Groq Client
# Ensure the GROQ_API_KEY environment variable is set before running the server
try:
    api_key = os.environ.get("GROQ_API_KEY")
    groq_client = Groq(api_key=api_key) if api_key else None
    if not groq_client:
        print("Warning: GROQ_API_KEY environment variable not set. API calls will fail.")
except Exception as e:
    print(f"Warning: Groq client failed to initialize. Error: {e}")
    groq_client = None

# Pydantic model for request validation
class RecommendationRequest(BaseModel):
    min_rate: float = None
    max_cost: float = None
    location: str = None
    cuisine: str = None

def filter_restaurants_from_db(min_rate, max_cost, location, cuisine, limit=5):
    """Retrieve filtered restaurants from the SQLite database."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found. Please run Phase 2 first.")
        
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM restaurants WHERE 1=1"
    params = []
    
    if min_rate is not None:
        query += " AND rate >= ?"
        params.append(min_rate)
    if max_cost is not None:
        query += " AND approx_cost <= ?"
        params.append(max_cost)
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if cuisine:
        query += " AND cuisines LIKE ?"
        params.append(f"%{cuisine}%")
        
    query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

@app.post("/api/recommend")
async def get_recommendation(req: RecommendationRequest):
    """Endpoint that filters the DB and calls the Groq LLM to generate recommendations."""
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq API client is not configured. Please set the GROQ_API_KEY environment variable.")
        
    # 1. Retrieve Data from Database
    df_restaurants = filter_restaurants_from_db(
        req.min_rate, 
        req.max_cost, 
        req.location, 
        req.cuisine
    )
    
    if df_restaurants.empty:
        return {
            "recommendation": "I couldn't find any restaurants matching your specific criteria. Could you try adjusting your filters?",
            "raw_data": []
        }
        
    # 2. Format Context for the LLM
    context_str = "Here are the top restaurant matches from our database:\n\n"
    for _, row in df_restaurants.iterrows():
        context_str += f"- Name: {row['name']} (Rating: {row['rate']}/5, Cost for two: ~{row['approx_cost']})\n"
        context_str += f"  Location: {row['location']}\n"
        context_str += f"  Cuisines: {row['cuisines']}\n\n"
        
    # 3. Prompt Engineering
    system_prompt = (
        "You are an enthusiastic, expert food critic and local restaurant guide. "
        "Your task is to recommend restaurants based strictly on the provided database matches context. "
        "Write a conversational, highly engaging recommendation highlighting why these places are great. "
        "Use markdown formatting (bolding, bullet points) to make it easy to read. "
        "Do NOT invent or hallucinate restaurants that are not in the context list."
    )
    
    user_prompt = (
        f"User Preferences -> Min Rating: {req.min_rate}, Max Cost: {req.max_cost}, "
        f"Location: {req.location}, Cuisine: {req.cuisine}\n\n"
        f"{context_str}\n\n"
        f"Please give me your best recommendation based on this!"
    )
    
    # 4. Call Groq LLM
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Switched to the latest active Groq model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        
        llm_response = completion.choices[0].message.content
        return {
            "recommendation": llm_response, 
            "raw_data": df_restaurants.to_dict(orient="records")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendation from Groq: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
