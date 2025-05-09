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

# Rich UI HTML Template using Bootstrap
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Azure GPT Policy Generator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding-top: 40px; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <h2 class="mb-4 text-center">🔐 Azure GPT-Powered Policy Generator</h2>
            <form id="policyForm">
                <div class="mb-3">
                    <label for="prompt" class="form-label">Policy Prompt</label>
                    <textarea class="form-control" id="prompt" rows="4" placeholder="e.g., Allow inbound SSH from 10.0.0.0/24"></textarea>
                </div>
                <div class="d-grid">
                    <button type="submit" class="btn btn-primary">Generate Policy</button>
                </div>
            </form>
            <div class="mt-4">
                <h5>Generated Policy (JSON):</h5>
                <pre id="output" class="bg-light p-3 rounded">Waiting for input...</pre>
            </div>
        </div>
    </div>
</div>

<script>
document.getElementById("policyForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const output = document.getElementById("output");
    output.textContent = "⏳ Generating policy...";

    const prompt = document.getElementById("prompt").value;
    try {
        const response = await fetch("/generate-policy", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ prompt })
        });

        const result = await response.json();
        const jsonStr = result.result || JSON.stringify(result);
        try {
            const jsonObj = JSON.parse(jsonStr);
            output.textContent = JSON.stringify(jsonObj, null, 2);
        } catch {
            output.textContent = jsonStr;
        }
    } catch (err) {
        output.textContent = "❌ Error: " + err.message;
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
