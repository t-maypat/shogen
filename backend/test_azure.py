import os
from openai import AzureOpenAI
import traceback

from dotenv import load_dotenv
load_dotenv()

def test():
    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("SHOGEN_AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("SHOGEN_AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("SHOGEN_AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        )
        deployment = os.getenv("SHOGEN_AZURE_OPENAI_DEPLOYMENT")
        
        print(f"Testing Azure OpenAI connection...")
        print(f"Endpoint: {client.base_url}")
        print(f"Deployment: {deployment}")
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": "Hello"}],
        )
        print("Standard chat completion: SUCCESS")
        with open("test_output.txt", "w", encoding="utf-8") as f:
            f.write(response.choices[0].message.content)
        
        from app.schemas.evaluation import Wave2AIOutput
        schema = Wave2AIOutput.model_json_schema()
        import json
        print("Schema generated:")
        print(json.dumps(schema, indent=2))
        
        print("\nTesting structured output with Wave2AIOutput...")
        structured = client.beta.chat.completions.parse(
            model=deployment,
            messages=[{"role": "user", "content": "Generate wave 2"}],
            response_format=Wave2AIOutput
        )
        print("Structured output: SUCCESS")
        
    except Exception as e:
        print("ERROR:", e)
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
