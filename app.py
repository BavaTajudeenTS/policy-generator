from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

@app.route("/")
def home():
    return "Policy Generator API is live 🚀"

@app.route("/generate-policy", methods=["POST"])
def generate_policy():
    data = request.get_json()
    prompt = data.get("prompt", "")
    
    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai.api_type = "azure"
    openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    response = openai.ChatCompletion.create(
        engine=deployment_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1000
    )

    return jsonify({
        "result": response['choices'][0]['message']['content']
    })
