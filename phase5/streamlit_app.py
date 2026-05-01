import streamlit as st
import sqlite3
import pandas as pd
import os
from groq import Groq

# Configure the Streamlit page
st.set_page_config(
    page_title="AI Restaurant Recommender",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for glassmorphism and modern design
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        color: #2c3e50;
        text-align: center;
        padding-bottom: 2rem;
    }
    .recommendation-box {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🍽️ AI Restaurant Recommender</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>Discover your next favorite meal using the power of AI!</p>", unsafe_allow_html=True)

# Sidebar for inputs
with st.sidebar:
    st.header("🎯 Your Preferences")
    
    location = st.text_input("📍 Location", placeholder="e.g., Indiranagar")
    cuisine = st.text_input("🍕 Cuisine", placeholder="e.g., Italian")
    
    st.markdown("---")
    min_rate = st.slider("⭐ Minimum Rating", min_value=1.0, max_value=5.0, value=4.0, step=0.1)
    max_cost = st.slider("💰 Max Cost (for two)", min_value=100, max_value=5000, value=2000, step=100)
    
    st.markdown("---")
    get_recs_btn = st.button("🚀 Get Recommendations", use_container_width=True, type="primary")

# API Key and Client initialization
# Try getting from Streamlit Secrets first (for Cloud), then fallback to environment variables
api_key = ""
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not api_key:
    from dotenv import load_dotenv
    # Fallback to local .env file
    load_dotenv(dotenv_path=".env")
    load_dotenv(dotenv_path="../.env")
    api_key = os.environ.get("GROQ_API_KEY", "")

if not api_key:
    st.error("🔑 GROQ_API_KEY is not set. Please configure it in your Streamlit Cloud Secrets!")
    st.stop()

groq_client = Groq(api_key=api_key)

def filter_restaurants_from_db(min_rate, max_cost, location, cuisine, limit=5):
    """Retrieve filtered restaurants from the SQLite database."""
    # Handle paths for both local and cloud deployment
    db_paths = ["phase2/zomato.db", "../phase2/zomato.db", "zomato.db"]
    db_path = None
    for p in db_paths:
        if os.path.exists(p):
            db_path = p
            break
            
    if not db_path:
        return pd.DataFrame()
        
    conn = sqlite3.connect(db_path)
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

# Main content area
if get_recs_btn:
    with st.spinner("AI is curating the perfect dining experience for you..."):
        try:
            # 1. Retrieve Data from Database directly
            df_restaurants = filter_restaurants_from_db(min_rate, max_cost, location, cuisine)
            
            if df_restaurants.empty:
                st.warning("I couldn't find any restaurants matching your specific criteria or the database couldn't be loaded. Could you try adjusting your filters?")
            else:
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
                    f"User Preferences -> Min Rating: {min_rate}, Max Cost: {max_cost}, "
                    f"Location: {location}, Cuisine: {cuisine}\n\n"
                    f"{context_str}\n\n"
                    f"Please give me your best recommendation based on this!"
                )
                
                # 4. Call Groq LLM directly
                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                )
                
                recommendation = completion.choices[0].message.content
                raw_data = df_restaurants.to_dict(orient="records")
                
                # Display the LLM Recommendation
                st.markdown("<div class='recommendation-box'>", unsafe_allow_html=True)
                st.markdown("### ✨ AI's Top Picks")
                st.markdown(recommendation)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Display the raw data
                if raw_data:
                    with st.expander("📊 View Raw Database Matches"):
                        df = pd.DataFrame(raw_data)
                        st.dataframe(df, use_container_width=True)
                        
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
else:
    st.info("👈 Enter your preferences in the sidebar and click 'Get Recommendations' to start!")
