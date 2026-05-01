import streamlit as st
import requests
import pandas as pd

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

# Main content area
if get_recs_btn:
    with st.spinner("AI is curating the perfect dining experience for you..."):
        # Prepare request payload
        payload = {}
        if min_rate: payload["min_rate"] = float(min_rate)
        if max_cost: payload["max_cost"] = float(max_cost)
        if location: payload["location"] = location.strip()
        if cuisine: payload["cuisine"] = cuisine.strip()

        try:
            # Call the FastAPI backend
            response = requests.post("http://localhost:8000/api/recommend", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                recommendation = data.get("recommendation", "")
                raw_data = data.get("raw_data", [])
                
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
            else:
                st.error(f"Error from API: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("Failed to connect to the backend. Please ensure the FastAPI server is running (start_app.bat).")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
else:
    st.info("👈 Enter your preferences in the sidebar and click 'Get Recommendations' to start!")
