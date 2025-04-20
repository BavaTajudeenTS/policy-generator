from flask import Flask, request, jsonify, render_template_string
from openai import AzureOpenAI
import os

app = Flask(__name__)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Simple HTML UI template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Azure GPT Policy Generator</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        textarea { width: 100%; height: 80px; font-size: 16px; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 8px; }
        button { padding: 10px 20px; font-size: 16px; margin-top: 10px; }
    </style>
</head>
<body>
    <h2>🔐 Azure GPT-Powered Policy Generator</h2>
    <form id="policyForm">
        <label for="prompt">Enter your policy prompt:</label><br>
        <textarea id="prompt" name="prompt" placeholder="Allow inbound SSH from 10.0.0.0/24"></textarea><br>
        <button type="submit">Generate Policy</button>
    </form>
    <h3>Generated Policy (JSON):</h3>
    <pre id="output">Waiting for input...</pre>

    <script>
        document.getElementById("policyForm").addEventListener("submit", async function(event) {
            event.preventDefault();
            const prompt = document.getElementById("prompt").value;
            const response = await fetch("/generate-policy", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ prompt })
            });

            const result = await response.json();
            try {
                const jsonObj = JSON.parse(result.result);
                document.getElementById("output").textContent = JSON.stringify(jsonObj, null, 2);
            } catch {
                document.getElementById("output").textContent = result.result || JSON.stringify(result);
            }
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/generate-policy", methods=["POST"])
def generate_policy():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        system_message = {
            "role": "system",
            "content": (
                "You are a network security policy generator. "
                "Always return the response in valid JSON format with the following fields: "
                "`action`, `protocol`, `port`, `source`, and `description`."
            )
        }

        user_message = {
            "role": "user",
            "content": prompt
        }

        response = client.chat.completions.create(
            model=deployment_id,
            messages=[system_message, user_message],
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
