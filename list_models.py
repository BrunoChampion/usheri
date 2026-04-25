import os
from dotenv import load_dotenv

load_dotenv()

print("Listando modelos disponibles en tu cuenta...\n")

try:
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    for model in client.models.list():
        if "gemini" in model.name.lower():
            print(f"  - {model.name}")
except Exception as e:
    print(f"Error: {e}")
    print("\nIntentando con Vertex AI backend...")
    try:
        from google import genai
        client = genai.Client(vertexai=True, project=os.getenv("GOOGLE_CLOUD_PROJECT", "unknown"))
        for model in client.models.list():
            if "gemini" in model.name.lower():
                print(f"  - {model.name}")
    except Exception as e2:
        print(f"Error también con Vertex: {e2}")
