import os
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

project_endpoint = os.environ["PROJECT_ENDPOINT"]
credential = DefaultAzureCredential()

project_client = AIProjectClient(
    credential=credential,
    endpoint=project_endpoint
)

openai_client = project_client.get_openai_client()
conversation = openai_client.conversations.create()

response = openai_client.responses.create(
    conversation=conversation.id,
    input="What's expected of me when submitting a pull request?",
    extra_body={"agent_reference": {"name": "support-assistant", "type": "agent_reference"}},
)

print(response.output_text)

print("\nSources:")
sources = set()
for item in response.output:
    if hasattr(item, "content"):
        for content_part in item.content:
            if hasattr(content_part, "annotations"):
                for annotation in content_part.annotations:
                    filename = annotation.url.split("/")[-1].replace("_", " ").replace(".pdf", "").title()
                    sources.add(filename)

for source in sources:
    print(f"- {source}")