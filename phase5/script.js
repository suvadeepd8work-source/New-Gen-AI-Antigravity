document.addEventListener('DOMContentLoaded', () => {
    const rateSlider = document.getElementById('min_rate');
    const rateValue = document.getElementById('rate-value');
    const costSlider = document.getElementById('max_cost');
    const costValue = document.getElementById('cost-value');
    const form = document.getElementById('recommendation-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.querySelector('.btn-text');
    const spinner = document.querySelector('.spinner');
    const resultsContainer = document.getElementById('results-container');
    const resultsContent = document.getElementById('results-content');

    // Dynamically update slider values on screen
    rateSlider.addEventListener('input', (e) => rateValue.textContent = parseFloat(e.target.value).toFixed(1));
    costSlider.addEventListener('input', (e) => costValue.textContent = e.target.value);

    // Handle Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Trigger UI Loading State
        btnText.classList.add('hidden');
        spinner.classList.remove('hidden');
        submitBtn.disabled = true;
        resultsContainer.classList.add('hidden');

        // Construct JSON Payload
        const payload = {
            location: document.getElementById('location').value.trim() || null,
            cuisine: document.getElementById('cuisine').value.trim() || null,
            min_rate: parseFloat(rateSlider.value),
            max_cost: parseFloat(costSlider.value)
        };

        try {
            // Fetch from FastAPI backend
            const response = await fetch('http://localhost:8000/api/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Render the LLM markdown response beautifully
            resultsContent.innerHTML = marked.parse(data.recommendation);
            resultsContainer.classList.remove('hidden');
            
            // Smooth scroll to the results
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        } catch (error) {
            console.error("API Call Failed:", error);
            resultsContent.innerHTML = `
                <div style="color: #ef4444; padding: 1rem; border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.1); border-radius: 8px;">
                    <strong>Connection Error:</strong> Could not reach the backend AI engine. 
                    <br><br>Make sure you are running the FastAPI server from Phase 3:
                    <br><code>cd phase3 && python main.py</code>
                </div>`;
            resultsContainer.classList.remove('hidden');
        } finally {
            // Restore UI Submit Button State
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });
});
