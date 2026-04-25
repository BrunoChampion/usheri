import time
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.7)

for i in range(3):
    start = time.time()
    result = llm.invoke("Di 'hola' y nada mas")
    print(f"Llamada {i+1}: {time.time()-start:.2f}s -> {result.content}")
