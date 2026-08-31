import os
from calle import CalleClient
from config import settings

client = CalleClient(api_key=settings.CALLE_API_KEY)

# Strict schema required from Call-E
incident_schema = {
    "type": "object",
    "required": ["city", "location", "issue_type", "severity"],
    "properties": {
        "city": {
            "type": "string",
            "description": "The municipality/city where the issue is located (e.g., Springfield)."
        },
        "location": {
            "type": "string",
            "description": "The specific street address or nearest intersection (e.g., 742 Evergreen Terrace)."
        },
        "issue_type": {
            "type": "string",
            "description": "Category of the problem: pothole, garbage, streetlight, water leak, etc."
        },
        "severity": {
            "type": "string",
            "enum": ["low", "medium", "high", "emergency"],
            "description": "The estimated urgency based on caller description."
        }
    }
}

agent_goal = """
You are 'Call-E', the AI Municipal Dispatcher.

YOUR GOAL:
Collect and verify city incident reports from citizens.

CONVERSATION WORKFLOW:
1. Greet the citizen and ask what issue they are reporting.
2. Ask for both the CITY and the STREET ADDRESS / LANDMARK where the problem is located.
3. LOCATION VALIDATION:
   - Immediately run the `verify_location` MCP tool with the provided city and street address.
   - If the tool returns INVALID_CITY, inform the caller politely about which cities are serviced and ask for clarification.
   - If the tool returns AMBIGUOUS_STREET, ask for a nearby landmark or cross street.
4. Collect the severity (e.g., is it blocking traffic or causing immediate danger?).
5. Once all fields are confirmed valid, thank the caller, reassure them that the dispatch team has been notified, and end the call.
"""

def configure_agent():
    agent = client.agents.create(
        name="Municipal Incident Dispatcher",
        goal=agent_goal,
        result_schema=incident_schema,
        mcp_servers=[
            {
                "name": "LocationVerificationServer",
                "url": "https://your-ngrok-url.ngrok-free.app/sse"
            }
        ]
    )
    print(f"✅ Agent configured with ID: {agent.id}")

    # Attach to inbound line
    client.numbers.update(
        phone_number=settings.CALLE_PHONE_NUMBER,
        agent_id=agent.id
    )
    print(f"✅ Inbound number {settings.CALLE_PHONE_NUMBER} attached.")

if __name__ == "__main__":
    configure_agent()