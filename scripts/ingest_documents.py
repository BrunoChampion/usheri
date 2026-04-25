import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

from rag.ingest import ingest
from rag.logging_config import setup_logging

load_dotenv()


def main() -> None:
    setup_logging()
    print("Iniciando ingesta de documentos...")
    print("Buscando archivos en data/documents/ (.md, .pdf, .docx)\n")
    vectorstore = ingest()
    count = vectorstore._collection.count()
    print(f"\nIngesta completa. {count} vectores en la colección 'amaru_policies'.")
    print("Puedes ejecutar el agente con: python main.py")


if __name__ == "__main__":
    main()
