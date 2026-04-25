import shutil
from pathlib import Path

DATA_DIR = Path("data")
LOGS_DIR = Path("logs")

FILES_TO_DELETE = [
    DATA_DIR / "tickets.jsonl",
    DATA_DIR / "escalations.jsonl",
    LOGS_DIR / "agent.jsonl",
]

DIRS_TO_CLEAN = [
    DATA_DIR / "chroma_db",
]


def main() -> None:
    deleted_files = 0
    cleaned_dirs = 0

    for f in FILES_TO_DELETE:
        if f.exists():
            f.unlink()
            deleted_files += 1

    for d in DIRS_TO_CLEAN:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            cleaned_dirs += 1

    print(
        f"Reset completo: {deleted_files} archivos eliminados, {cleaned_dirs} directorios limpiados."
    )
    print("  - data/tickets.jsonl")
    print("  - data/escalations.jsonl")
    print("  - data/chroma_db/")
    print("  - logs/agent.jsonl")


if __name__ == "__main__":
    main()
