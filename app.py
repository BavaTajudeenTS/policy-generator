from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_KEY")

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")

@app.route("/generate-policy", methods=["POST"])
def generate_policy():
    prompt = request.json.get("prompt")
    response = openai.ChatCompletion.create(
        engine=DEPLOYMENT_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=800
    )
    return jsonify(response["choices"][0]["message"]["content"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
