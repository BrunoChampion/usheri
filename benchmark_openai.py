import time
from dotenv import load_dotenv

load_dotenv()

print("--- Test: gpt-5.4-mini ---")
try:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.7)
    
    start = time.time()
    result = llm.invoke("Di 'hola' y nada mas")
    print(f"Tiempo: {time.time()-start:.2f}s")
    print(f"Respuesta: {result.content}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    print("\n--- Fallback a gpt-4o-mini ---")
    try:
        llm2 = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        start = time.time()
        result2 = llm2.invoke("Di 'hola' y nada mas")
        print(f"Tiempo: {time.time()-start:.2f}s")
        print(f"Respuesta: {result2.content}")
    except Exception as e2:
        print(f"Error fallback: {e2}")
