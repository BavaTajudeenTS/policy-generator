from flask import Flask, request, jsonify, render_template_string
from openai import AzureOpenAI
import os

app = Flask(__name__)

# Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Azure GPT Policy Generator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 40px; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
<div class="container">
    <h2 class="mb-4">🔐 Azure GPT-Powered Policy Generator</h2>
    <form id="policyForm">
        <div class="mb-3">
            <label class="form-label">Choose Example Prompt</label>
            <select class="form-select" id="templateSelect">
                <option value="">-- Select a template --</option>
                <option value="Allow inbound SSH from 20.0.0.5 to 10.0.0.6 on port 22">Allow inbound SSH</option>
                <option value="Deny all outbound except port 443">Deny all outbound except HTTPS</option>
                <option value="Allow VPN access from 20.0.0.5 to 10.0.0.5 and 10.0.0.6">VPN to multiple IPs</option>
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label">Prompt</label>
            <textarea class="form-control" id="prompt" rows="3" placeholder="Type your custom prompt here..."></textarea>
        </div>
        <div class="row mb-3">
            <div class="col-md-4">
                <label class="form-label">Source Zone</label>
                <select class="form-select" id="source_zone">
                    <option value="trust">trust</option>
                    <option value="untrust">untrust</option>
                    <option value="mgmt">mgmt</option>
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Destination Zone</label>
                <select class="form-select" id="destination_zone">
                    <option value="trust">trust</option>
                    <option value="untrust">untrust</option>
                    <option value="mgmt">mgmt</option>
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Action</label>
                <select class="form-select" id="action">
                    <option value="allow">allow</option>
                    <option value="deny">deny</option>
                </select>
            </div>
        </div>
        <div class="row mb-3">
            <div class="col-md-6">
                <label class="form-label">Tag Name</label>
                <select class="form-select" id="tag_name">
                    <option value="trust">trust</option>
                    <option value="untrust">untrust</option>
                    <option value="mgmt">mgmt</option>
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label">Group Profile</label>
                <input class="form-control" type="text" id="group_profile" placeholder="e.g., Default">
            </div>
        </div>
        <div class="mb-4">
            <label class="form-label">Output Format</label>
            <select class="form-select" id="format">
                <option value="json">JSON</option>
                <option value="bicep">Bicep</option>
                <option value="azcli">Azure CLI</option>
                <option value="terraform">Terraform</option>
                <option value="yaml">YAML</option>
            </select>
        </div>
        <div class="d-grid mb-3">
            <button type="submit" class="btn btn-primary">Generate Policy</button>
        </div>
    </form>

    <h5>Generated Output:</h5>
    <pre id="output" class="bg-light p-3 rounded">Waiting for input...</pre>
</div>

<script>
document.getElementById("templateSelect").addEventListener("change", function() {
    const template = this.value;
    if (template) document.getElementById("prompt").value = template;
});

document.getElementById("policyForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const prompt = document.getElementById("prompt").value;
    if (!prompt.trim()) {
        alert("Please enter or select a prompt.");
        return;
    }

    const payload = {
        prompt: prompt,
        source_zone: document.getElementById("source_zone").value,
        destination_zone: document.getElementById("destination_zone").value,
        action: document.getElementById("action").value,
        tag_name: document.getElementById("tag_name").value,
        group_profile: document.getElementById("group_profile").value,
        format: document.getElementById("format").value
    };

    const output = document.getElementById("output");
    output.textContent = "⏳ Generating policy...";

    const response = await fetch("/generate-policy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const result = await response.json();
    output.textContent = result.result || JSON.stringify(result);
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
        source_zone = data.get("source_zone", "trust")
        destination_zone = data.get("destination_zone", "trust")
        action = data.get("action", "allow")
        tag_name = data.get("tag_name", "trust")
        group_profile = data.get("group_profile", "Default")
        format_type = data.get("format", "json")

        deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        format_instruction = {
            "json": "Return output as a JavaScript object.",
            "bicep": "Generate the policy as a Bicep module.",
            "azcli": "Generate Azure CLI commands to implement this policy.",
            "terraform": "Generate Terraform code for this policy.",
            "yaml": "Generate the policy in YAML format."
        }.get(format_type, "Return output as a JavaScript object.")

        system_message = {
            "role": "system",
            "content": (
                f"You are a policy generator. Based on the user's prompt and the parameters below, generate output in the format specified.\n\n"
                f"{format_instruction}\n\n"
                f"Parameters to include:\n"
                f"- source_zone: ['{source_zone}']\n"
                f"- destination_zone: ['{destination_zone}']\n"
                f"- action: '{action}'\n"
                f"- tag_name: ['{tag_name}']\n"
                f"- group_profile: '{group_profile}'\n\n"
                f"Only return the generated configuration. Do not explain anything."
            )
        }

        user_message = {
            "role": "user",
            "content": prompt
        }

        response = client.chat.completions.create(
            model=deployment_id,
            messages=[system_message, user_message],
            temperature=0.3,
            max_tokens=1000
        )

        return jsonify({ "result": response.choices[0].message.content })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({ "error": str(e) }), 500

if __name__ == "__main__":
    app.run(debug=True)
