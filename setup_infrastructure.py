import os
from dotenv import load_dotenv

# Import Azure identity and AI Projects client - authenticates using Azure credentials instead of an API key
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.projects import AIProjectClient

# Import PromptAgentDefinition and MCPTool to define a custom agent and connect to the knowledge base
from azure.ai.projects.models import PromptAgentDefinition, MCPTool

# Load environment variables from .env file
load_dotenv()

# Connect to the Foundry project
project_endpoint = os.environ["PROJECT_ENDPOINT"]
credential = DefaultAzureCredential()

project_client = AIProjectClient(
    credential=credential,
    endpoint=project_endpoint
)

# Import the requests library to make HTTP requests to the Azure Management API
import requests

# Load connection details from environment variables
project_resource_id = os.environ["PROJECT_RESOURCE_ID"]
project_connection_name = os.environ["PROJECT_CONNECTION_NAME"]
mcp_endpoint = os.environ["MCP_ENDPOINT"]

# Get bearer token for authenticating with the Azure Management API
bearer_token_provider = get_bearer_token_provider(credential, "https://management.azure.com/.default")
headers = {
    "Authorization": f"Bearer {bearer_token_provider()}",
}

# The project connection, tool definition and custom

# Create project connection to the knowledge base's MCP endpoint. 
response = requests.put(
    f"https://management.azure.com{project_resource_id}/connections/{project_connection_name}?api-version=2025-10-01-preview",
    headers=headers,
    json={
        "name": project_connection_name,
        "type": "Microsoft.MachineLearningServices/workspaces/connections",
        "properties": {
            "authType": "ProjectManagedIdentity",
            "category": "RemoteTool",
            "target": mcp_endpoint,
            "isSharedToAll": True,
            "audience": "https://search.azure.com/",
            "metadata": {"ApiType": "Azure"}
        }
    }
)

# response.raise_for_status()
print(f"Connection '{project_connection_name}' created or updated successfully.")

# # Define the tool that wraps your knowledge base
mcp_kb_tool = MCPTool(
    server_label="knowledge-base",
    server_url=mcp_endpoint,
    require_approval="never",
    allowed_tools=["knowledge_base_retrieve"],
    project_connection_id=project_connection_name
)

# # Define what the agent should do and how it should behave
instructions = """
You are a helpful assistant that answers questions using the company's internal engineering documentation.
Use the knowledge base tool to answer questions about onboarding, incident response, security policy, or coding standards.
Prioritise the Security and Access Policy for questions about credentials, passwords, VPN access, two-factor authentication, or data classification.
Prioritise the Incident Response Runbook for questions about outages, severity levels, escalation, or on-call procedures.
Prioritise the API and Coding Style Guide for questions about naming conventions, pull requests, testing, or API design.
Prioritise the New Engineer Onboarding Guide for questions about first-week setup, dev environment configuration, or team norms.
If a question could reasonably relate to more than one document, check all relevant documents.
If the knowledge base doesn't contain the answer, respond with "I don't know".
Always cite the sources you used.
"""

# # Create the agent, giving it a model, instructions, and the tool
agent = project_client.agents.create_version(
    agent_name="support-assistant",
    definition=PromptAgentDefinition(
        model="gpt-5-mini",
        instructions=instructions,
        tools=[mcp_kb_tool]
    )
)

print(f"Agent '{agent.name}' created or updated successfully.")