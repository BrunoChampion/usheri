import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GOOGLE_API_KEY", "")[:15]
print(f"GOOGLE_API_KEY cargada: {key}...")
print(f"Empieza con AIzaSy: {key.startswith('AIzaSy')}")

print("\n--- Test con gemini-2.0-flash ---")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=1.0)
    result = llm.invoke("Hola, di 'funciona' en español")
    print(f"Respuesta: {result.content}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

print("\n--- Test con gemini-3-flash-preview ---")
try:
    llm2 = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=1.0)
    result2 = llm2.invoke("Hola, di 'funciona' en español")
    print(f"Respuesta: {result2.content}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
