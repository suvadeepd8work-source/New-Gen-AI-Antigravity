# AI Restaurant Recommendation Service Architecture

## Goal Description
Build an AI-powered service that provides highly relevant restaurant recommendations using the Zomato dataset (`ManikaSaini/zomato-restaurant-recommendation`). The service takes user preferences (price, place, rating, cuisine) and leverages the Groq LLM to generate clear, conversational, and tailored recommendations.

---

## High-Level Architecture Overview

1. **Frontend (User Interface)**
   - A dynamic web interface capturing user inputs: Price range, Location/Place, Minimum Rating, and Cuisine.
   - Displays Groq LLM-generated recommendations in an engaging, easy-to-read format.
2. **Backend API (Application Logic)**
   - Receives the user inputs from the frontend.
   - Constructs queries to search the dataset or database.
   - Constructs prompts and interacts with the Groq API.
3. **Data Pipeline & Storage (The Zomato Dataset)**
   - Fetches the dataset from Hugging Face.
   - Cleans and preprocesses data for efficient querying.
   - Stores it in a searchable database (e.g., PostgreSQL, SQLite) or a Vector Database for semantic search capabilities.
4. **LLM Engine (Recommendation Generation)**
   - Uses the ultra-fast Groq LLM API.
   - Ingests context (retrieved restaurants based on user filters) and outputs personalized, natural language recommendations.

---

## Project Phases

### Phase 1: Data Acquisition & Preparation
- **Objective:** Obtain, clean, and structure the Zomato dataset.
- **Tasks:**
  - Download the dataset using the Hugging Face `datasets` library or directly via pandas.
  - Perform Exploratory Data Analysis (EDA) to understand feature distributions.
  - **Data Cleaning:** Handle missing values, normalize text (cuisines, locations), and convert `approx_cost` and `rate` to numerical formats suitable for filtering.
  - Export cleaned data to a structured format (CSV/Parquet) or load it directly into a local database.

### Phase 2: Database Setup & Data Ingestion
- **Objective:** Create a fast, queryable data store to filter restaurants before sending them to the LLM.
- **Tasks:**
  - Choose a database solution based on the needed complexity.
  - **Traditional Filtering (SQL):** Store structured fields (price, place, rating, cuisine) for exact or range filtering.
  - Ingest the cleaned dataset into the chosen database.

### Phase 3: Backend Service Development & Groq LLM Integration
- **Objective:** Build the core API logic connecting the Database and the Groq LLM.
- **Tasks:**
  - Set up a web framework (e.g., FastAPI, Flask, or Node.js/Express).
  - Create endpoints (e.g., `POST /api/recommend`).
  - **Retrieval Logic:** When a request is received with the user's constraints, query the database to filter and retrieve the top *N* matching restaurants.
  - **Groq LLM Setup:** Implement the connection to the Groq API.
  - **Prompt Engineering:** Define the system prompt (e.g., "You are an expert food critic...") and inject the filtered restaurant data into the prompt context to generate the final response.

### Phase 4: Testing & Evaluation
- **Objective:** Ensure quality and prevent hallucinations.
- **Tasks:**
  - **Evaluation:** Test the Groq LLM responses to ensure it only recommends restaurants from the provided context and accurately reflects the user's constraints.
  - **Performance:** Optimize database queries and LLM response latency.

### Phase 5: Frontend UI Page & Deployment
- **Objective:** Build the user-facing application UI page and launch the service.
- **Tasks:**
  - **UI Page Creation:** Build a dedicated web UI page with input forms, dropdowns, and sliders for Price, Location, Rating, and Cuisine.
  - Design a "Get Recommendations" interaction with intuitive loading states.
  - Build a results view to cleanly render the Groq LLM's text output, emphasizing modern, dynamic design aesthetics.
  - **Deployment:** Deploy the backend API to a cloud platform (e.g., AWS, Render) and the frontend UI page to a hosting service (e.g., Vercel, Netlify).
