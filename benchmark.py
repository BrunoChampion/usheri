import time
from dotenv import load_dotenv

load_dotenv()

print("--- Test 1: Tiempo de inicializacion del modelo ---")
start = time.time()
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=1.0)
print(f"Inicializacion: {time.time()-start:.2f}s")

print("\n--- Test 2: Tiempo de primera llamada ---")
start = time.time()
result = llm.invoke("Di 'hola' y nada mas")
print(f"Primera llamada: {time.time()-start:.2f}s")
print(f"Respuesta: {result.content[:50]}")

print("\n--- Test 3: Tiempo de segunda llamada ---")
start = time.time()
result2 = llm.invoke("Di 'adios' y nada mas")
print(f"Segunda llamada: {time.time()-start:.2f}s")
print(f"Respuesta: {result2.content[:50]}")
