import json
import logging
import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader as DocxLoader
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("usheri")

DOCUMENTS_DIR = Path("data/documents")
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db"))
COLLECTION_NAME = "amaru_policies"
METADATA_FILE = DOCUMENTS_DIR / "metadata.json"

MARKDOWN_SEPARATORS = ["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""]
GENERIC_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 320

EXTENSION_LOADERS: dict[str, type] = {
    ".md": TextLoader,
    ".pdf": PyPDFLoader,
    ".docx": DocxLoader,
    ".txt": TextLoader,
}


def _load_metadata_manifest() -> dict[str, dict]:
    if not METADATA_FILE.exists():
        logger.warning("metadata.json no encontrado en %s", METADATA_FILE)
        return {}
    with open(METADATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def _get_file_metadata(filename: str, manifest: dict[str, dict]) -> dict:
    entry = manifest.get(filename)
    if entry:
        return dict(entry)
    stem = Path(filename).stem
    logger.warning(
        "Sin entrada en metadata.json para '%s'; usando metadata mínima", filename
    )
    return {"titulo": stem, "categoria": "sin_categoria"}


def _load_documents() -> list:
    documents = []
    manifest = _load_metadata_manifest()

    for filepath in sorted(DOCUMENTS_DIR.iterdir()):
        if filepath.name == "metadata.json":
            continue
        ext = filepath.suffix.lower()
        loader_cls = EXTENSION_LOADERS.get(ext)
        if loader_cls is None:
            logger.warning("Formato no soportado, ignorando: %s", filepath.name)
            continue

        file_metadata = _get_file_metadata(filepath.name, manifest)
        file_metadata["source"] = filepath.name

        try:
            if ext == ".pdf":
                loader = loader_cls(str(filepath))
                loaded = loader.load()
                for doc in loaded:
                    doc.metadata.update(file_metadata)
                    documents.append(doc)
            elif ext in (".md", ".txt"):
                loader = loader_cls(str(filepath), encoding="utf-8")
                loaded = loader.load()
                for doc in loaded:
                    doc.metadata.update(file_metadata)
                    documents.append(doc)
            else:
                loader = loader_cls(str(filepath))
                loaded = loader.load()
                for doc in loaded:
                    doc.metadata.update(file_metadata)
                    documents.append(doc)
            logger.info("Cargado: %s (%d fragmentos)", filepath.name, len(loaded))
        except Exception as e:
            logger.error("Error cargando %s: %s", filepath.name, e)

    return documents


def _split_documents(documents: list) -> list:
    md_docs = []
    other_docs = []
    for doc in documents:
        if doc.metadata.get("source", "").endswith(".md"):
            md_docs.append(doc)
        else:
            other_docs.append(doc)

    chunks = []

    if md_docs:
        md_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=MARKDOWN_SEPARATORS,
        )
        chunks.extend(md_splitter.split_documents(md_docs))

    if other_docs:
        generic_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=GENERIC_SEPARATORS,
        )
        chunks.extend(generic_splitter.split_documents(other_docs))

    logger.info("Chunking: %d documentos -> %d chunks", len(documents), len(chunks))
    return chunks


def ingest() -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    documents = _load_documents()
    if not documents:
        logger.warning("No se encontraron documentos en %s", DOCUMENTS_DIR)
        return Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_PERSIST_DIR),
        )

    chunks = _split_documents(documents)

    if CHROMA_PERSIST_DIR.exists():
        import shutil

        shutil.rmtree(CHROMA_PERSIST_DIR, ignore_errors=True)
        logger.info("Colección anterior eliminada")

    vectorstore = Chroma.from_documents(
        collection_name=COLLECTION_NAME,
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_PERSIST_DIR),
    )

    logger.info("Ingesta completa: %d chunks en '%s'", len(chunks), COLLECTION_NAME)
    return vectorstore
