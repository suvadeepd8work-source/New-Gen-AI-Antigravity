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
    
    # Pre-defined list of common Zomato restaurant types
    REST_TYPES = [
        "Any", "Casual Dining", "Cafe", "Quick Bites", "Delivery", 
        "Mess", "Dessert Parlor", "Bakery", "Pub", "Bar", 
        "Beverage Shop", "Fine Dining", "Lounge", "Food Court", "Kiosk"
    ]
    selected_type = st.selectbox("🏪 Restaurant Type", options=REST_TYPES)
    rest_type = "" if selected_type == "Any" else selected_type
    
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

def filter_restaurants_from_db(min_rate, max_cost, location, cuisine, rest_type, limit=5):
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
    if rest_type:
        query += " AND rest_type LIKE ?"
        params.append(f"%{rest_type}%")
        
    query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# Main content area
if get_recs_btn:
    with st.spinner("AI is curating the perfect dining experience for you..."):
        try:
            # 1. Retrieve Data from Database directly
            df_restaurants = filter_restaurants_from_db(min_rate, max_cost, location, cuisine, rest_type)
            
            if df_restaurants.empty:
                st.warning("I couldn't find any restaurants matching your specific criteria or the database couldn't be loaded. Could you try adjusting your filters?")
            else:
                # 2. Format Context for the LLM
                context_str = "Here are the top restaurant matches from our database:\n\n"
                for _, row in df_restaurants.iterrows():
                    context_str += f"- Name: {row['name']} (Rating: {row['rate']}/5, Cost for two: ~{row['approx_cost']})\n"
                    context_str += f"  Location: {row['location']}\n"
                    context_str += f"  Cuisines: {row['cuisines']}\n"
                    context_str += f"  Type: {row['rest_type']}\n\n"
                    
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
                    f"Location: {location}, Cuisine: {cuisine}, Type: {rest_type}\n\n"
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
                
                # Beautiful Header for results
                st.markdown("---")
                st.markdown("<h2 style='text-align: center; color: #2c3e50;'>✨ Your Curated Dining Experience</h2>", unsafe_allow_html=True)
                
                # Show quick metrics
                st.markdown("<br>", unsafe_allow_html=True)
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Top Matches Found", len(df_restaurants))
                with cols[1]:
                    avg_cost = df_restaurants['approx_cost'].mean()
                    st.metric("Avg Cost for Two", f"₹{avg_cost:.0f}")
                with cols[2]:
                    max_rating = df_restaurants['rate'].max()
                    st.metric("Highest Rating", f"⭐ {max_rating:.1f}/5")
                
                # Display the LLM Recommendation
                st.markdown("<div class='recommendation-box'>", unsafe_allow_html=True)
                st.markdown(recommendation)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Display the raw data as beautiful cards
                st.markdown("<br><h3 style='color: #2c3e50;'>📊 Detailed Database Matches</h3>", unsafe_allow_html=True)
                for _, row in df_restaurants.iterrows():
                    cuisine_keyword = row['cuisines'].split(',')[0].strip()
                    img_url = f"https://loremflickr.com/600/300/food,{cuisine_keyword}?lock={row['id']}"
                    
                    st.markdown(f"""
                    <div style='background-color: rgba(255, 255, 255, 0.9); backdrop-filter: blur(5px); border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; border: 1px solid #eee;'>
                        <img src="{img_url}" style="width: 100%; height: 250px; object-fit: cover;" alt="{row['name']}">
                        <div style="padding: 20px;">
                            <h4 style='margin-top: 0; margin-bottom: 8px; color: #d35400;'>{row['name']}</h4>
                            <div style='display: flex; justify-content: space-between; color: #444;'>
                                <span><strong>📍 Location:</strong> {row['location']}</span>
                                <span><strong>⭐ Rating:</strong> {row['rate']} / 5</span>
                            </div>
                            <div style='display: flex; justify-content: space-between; color: #444; margin-top: 5px;'>
                                <span><strong>🍕 Cuisine:</strong> {row['cuisines']}</span>
                                <span><strong>💰 Cost for Two:</strong> ₹{row['approx_cost']}</span>
                            </div>
                            <div style='color: #666; margin-top: 8px; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 8px;'>
                                <span><strong>🏪 Type:</strong> {row['rest_type']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                        
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
else:
    st.info("👈 Enter your preferences in the sidebar and click 'Get Recommendations' to start!")
