from flask import Flask, render_template, request, jsonify
import requests # Standard library for making HTTP requests

app = Flask(__name__)

# IMPORTANT: Replace "YOUR_API_KEY_HERE" with your actual Gemini API Key.
# In a production environment, API keys should not be hardcoded. 
# They should be stored securely, for example, as environment variables 
# or using a secrets management service.
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
# This is a placeholder. You'll need to find the correct API endpoint for Gemini.
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent" # Example endpoint

def call_gemini_api(initial_prompt, context, tone, output_format, constraints):
    """
    Constructs a prompt and calls the Gemini API.
    """
    # Construct a detailed prompt for the Gemini API
    # This is a simple example of how you might structure the prompt.
    # You may need to adjust this based on how Gemini best understands these fields.
    structured_prompt = f"""Enhance the following user prompt:
Initial Prompt: "{initial_prompt}"

With the following considerations:
Context: "{context}"
Desired Tone: "{tone}"
Desired Output Format: "{output_format}"
Constraints/Keywords: "{constraints}"

Provide an enhanced version of the initial prompt based on these details.
"""

    headers = {
        "Content-Type": "application/json",
    }
    
    # The request body structure will depend heavily on the Gemini API's specific requirements.
    # This is a common structure for generative text APIs.
    # You MUST consult the Gemini API documentation for the correct format.
    data = {
        "contents": [{
            "parts": [{
                "text": structured_prompt
            }]
        }],
        # Add other parameters like 'generationConfig' if needed, e.g.,
        # "generationConfig": {
        #   "temperature": 0.7,
        #   "maxOutputTokens": 2048,
        # }
    }

    full_api_url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

    try:
        response = requests.post(full_api_url, headers=headers, json=data)
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
        
        # Assuming the API returns JSON with the enhanced prompt in a specific field.
        # This will need to be adjusted based on the actual Gemini API response structure.
        # For example, it might be response.json().get('candidates')[0].get('content').get('parts')[0].get('text')
        return response.json() 
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        # In a real app, you'd want more robust error handling here.
        # Maybe return a specific error structure or raise a custom exception.
        if e.response:
            print(f"Error Response: {e.response.text}")
            return {"error": str(e), "details": e.response.text}
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enhance-prompt', methods=['POST'])
def enhance_prompt_route():
    if request.method == 'POST':
        initial_prompt = request.form.get('initialPrompt')
        context = request.form.get('context')
        tone = request.form.get('tone')
        output_format = request.form.get('outputFormat')
        constraints = request.form.get('constraints')

        if not initial_prompt:
            return jsonify({"error": "Initial prompt is required."}), 400

        api_response = call_gemini_api(initial_prompt, context, tone, output_format, constraints)
        
        # For now, just return the raw API response.
        # In the next step, we'll process this and display it nicely.
        return jsonify(api_response)

if __name__ == '__main__':
    app.run(debug=True)
