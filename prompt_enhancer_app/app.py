from flask import Flask, render_template, request, jsonify
import requests # Standard library for making HTTP requests
import os
import json
import uuid
from datetime import datetime

app = Flask(__name__)

PROMPT_LIBRARY_FILE = 'prompt_library.json'

# IMPORTANT: Replace "YOUR_API_KEY_HERE" with your actual Gemini API Key.
# In a production environment, API keys should not be hardcoded. 
# They should be stored securely, for example, as environment variables 
# or using a secrets management service.
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
# This is a placeholder. You'll need to find the correct API endpoint for Gemini.
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent" # Example endpoint

# --- Prompt Library Helper Functions ---
def load_prompts():
    """Loads prompts from the JSON storage file."""
    if not os.path.exists(PROMPT_LIBRARY_FILE):
        return []
    try:
        with open(PROMPT_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        # Ensure all prompts have the necessary fields, provide defaults for older data
        for prompt in prompts:
            prompt.setdefault('id', uuid.uuid4().hex) # Add id if missing
            prompt.setdefault('name', 'Untitled Prompt')
            prompt.setdefault('timestamp', datetime.utcnow().isoformat())
            prompt.setdefault('initialPrompt', '')
            prompt.setdefault('context', '')
            prompt.setdefault('tone', '')
            prompt.setdefault('outputFormat', '')
            prompt.setdefault('constraints', '')
        return prompts
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading prompts: {e}")
        return []

def save_prompts(prompts):
    """Saves prompts to the JSON storage file."""
    try:
        with open(PROMPT_LIBRARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=4)
        return True
    except (IOError, TypeError) as e: # TypeError for json.dump if prompts are not serializable
        print(f"Error saving prompts: {e}")
        return False

# --- Gemini API Call Function ---
def call_gemini_api(initial_prompt, context, tone, output_format, constraints): # Not directly used by library but part of the app
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

# --- Prompt Library Routes ---
@app.route('/library/save', methods=['POST'])
def save_prompt_to_library():
    data = request.json
    if not data or 'name' not in data or not data.get('initialPrompt'): # Ensure name and initialPrompt are present
        return jsonify({"error": "Prompt name and content are required."}), 400

    prompts = load_prompts()
    
    new_prompt = {
        "id": uuid.uuid4().hex,
        "name": data.get('name', 'Untitled Prompt'),
        "timestamp": datetime.utcnow().isoformat(),
        "initialPrompt": data.get('initialPrompt', ''),
        "context": data.get('context', ''),
        "tone": data.get('tone', ''),
        "outputFormat": data.get('outputFormat', ''),
        "constraints": data.get('constraints', '')
        # Add any other fields you expect from the frontend
    }
    prompts.append(new_prompt)
    
    if save_prompts(prompts):
        return jsonify(new_prompt), 201 # 201 Created
    else:
        return jsonify({"error": "Failed to save prompt to library."}), 500

@app.route('/library', methods=['GET'])
def get_library_prompts():
    prompts = load_prompts()
    # Sort by timestamp, newest first
    prompts_sorted = sorted(prompts, key=lambda p: p.get('timestamp', ''), reverse=True)
    return jsonify(prompts_sorted)

@app.route('/library/<prompt_id>', methods=['GET'])
def get_library_prompt(prompt_id):
    prompts = load_prompts()
    prompt = next((p for p in prompts if p.get('id') == prompt_id), None)
    if prompt:
        return jsonify(prompt)
    else:
        return jsonify({"error": "Prompt not found."}), 404

@app.route('/library/<prompt_id>', methods=['DELETE'])
def delete_library_prompt(prompt_id):
    prompts = load_prompts()
    initial_length = len(prompts)
    prompts = [p for p in prompts if p.get('id') != prompt_id]
    
    if len(prompts) == initial_length:
        return jsonify({"error": "Prompt not found to delete."}), 404

    if save_prompts(prompts):
        return "", 204 # No Content, success
    else:
        return jsonify({"error": "Failed to delete prompt from library."}), 500

if __name__ == '__main__':
    app.run(debug=True)
