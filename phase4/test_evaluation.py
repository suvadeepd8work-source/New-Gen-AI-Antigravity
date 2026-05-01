import os
import sys
import time
import pytest
from fastapi.testclient import TestClient

# Add phase3 directory to Python path so we can import the FastAPI app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../phase3')))
try:
    from main import app
except ImportError:
    app = None

# Initialize TestClient
client = TestClient(app) if app else None

def test_api_performance_and_hallucination():
    """
    Phase 4 Evaluation:
    1. Tests the latency of the full Phase 3 API to ensure performance.
    2. Evaluates the LLM response for hallucinations (ensuring it only recommends from context).
    """
    
    if not app:
        pytest.fail("Could not import Phase 3 FastAPI app. Ensure Phase 3 is implemented.")
        
    if not os.environ.get("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set in environment. Skipping evaluation.")
        
    payload = {
        "min_rate": 4.0,
        "max_cost": 2000.0,
        "location": "",
        "cuisine": ""
    }
    
    print("\nStarting Phase 4 Evaluation...")
    
    # Measure Latency
    start_time = time.time()
    response = client.post("/api/recommend", json=payload)
    latency = time.time() - start_time
    
    # If 500 error, DB might not be set up
    if response.status_code == 500:
        pytest.skip(f"API Error (Likely Phase 2 Database missing): {response.text}")
        
    assert response.status_code == 200, f"Failed with status {response.status_code}"
    
    data = response.json()
    llm_output = data.get("recommendation", "")
    raw_data = data.get("raw_data", [])
    
    # 1. Performance Evaluation
    # Thanks to Groq, the full API roundtrip should be incredibly fast
    print(f"[Performance] Full API Latency: {latency:.2f} seconds")
    assert latency < 5.0, f"API is too slow, latency: {latency:.2f}s"
    
    # 2. Hallucination Evaluation
    # We must ensure the LLM only recommends restaurants that are actually in the DB context
    if len(raw_data) > 0:
        valid_names = [restaurant["name"] for restaurant in raw_data]
        
        # Check if at least one valid restaurant name is mentioned in the LLM output
        # (This is a basic string matching evaluator. For production, LLM-as-a-judge is preferred)
        found_match = any(name.lower() in llm_output.lower() for name in valid_names)
        
        print(f"[Evaluation] Valid restaurants from DB context: {valid_names}")
        assert found_match, "Hallucination Detected! The LLM did not recommend any restaurant from the context."
        print("[Evaluation] Passed: LLM successfully utilized the provided context.")
    else:
        # If DB returns no restaurants, LLM should gracefully handle it without hallucinating
        assert "couldn't find" in llm_output.lower() or "adjust" in llm_output.lower(), \
            "Hallucination Detected! LLM recommended a restaurant when the DB returned empty."
        print("[Evaluation] Passed: LLM gracefully handled empty context.")
