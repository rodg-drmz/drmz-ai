import os, json
import httpx

# Read the agent spec
with open("agents/morpheus.json") as f:
    spec = json.load(f)

# Ensure the API key is set
api_key = os.environ.get("OPENAI_API_KEY")
assert api_key, "Missing OPENAI_API_KEY in environment"

# Call the Agents API
response = httpx.post(
    "https://api.openai.com/v1/agents",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json=spec
)
response.raise_for_status()
agent_id = response.json()["id"]
print(agent_id)
