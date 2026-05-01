import os
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_recommendation_endpoint():
    """
    Integration test to verify the FastAPI endpoint and Groq LLM connection.
    This test ensures the DB is queried and the LLM returns a valid response.
    """
    
    # 1. Verify the API Key is loaded from the .env file
    api_key = os.environ.get("GROQ_API_KEY")
    assert api_key is not None, "GROQ_API_KEY is not set. Ensure the .env file is present in the root folder."
    
    # 2. Test Payload mimicking a user request
    payload = {
        "min_rate": 4.0,
        "max_cost": 1500.0,
        "location": "",
        "cuisine": ""
    }
    
    # 3. Trigger the endpoint
    response = client.post("/api/recommend", json=payload)
    
    # 4. Validate successful status code
    # Note: If this fails with 500, it likely means the Phase 2 database hasn't been created yet.
    assert response.status_code == 200, f"API failed. Message: {response.text}"
    
    # 5. Validate JSON response structure
    data = response.json()
    assert "recommendation" in data
    assert "raw_data" in data
    
    # 6. Verify Groq LLM actually generated a response
    assert isinstance(data["recommendation"], str)
    assert len(data["recommendation"]) > 10
    
    print("\n--- Groq LLM Test Output ---")
    print(data["recommendation"][:300] + "...\n")
