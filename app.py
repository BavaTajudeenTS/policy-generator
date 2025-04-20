from flask import Flask, request, jsonify
from openai import AzureOpenAI
import os

app = Flask(__name__)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

@app.route("/generate-policy", methods=["POST"])
def generate_policy():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        response = client.chat.completions.create(
            model=deployment_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000
        )

        return jsonify({
            "result": response.choices[0].message.content
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
