# Proyecto: Agente Asistente Interno Amaru

## Qué es
Prototipo de agente con LangGraph que responde consultas internas de
empleados de una empresa ficticia (Amaru Soluciones S.A.C.) usando RAG
sobre documentos de políticas, con capacidad de crear tickets y escalar
a humanos.

## Objetivo de aprendizaje
Entender el loop agéntico completo con 3 tools en LangGraph antes de
aplicarlo con clientes reales.

## Stack
- Python 3.11+
- LangGraph (create_react_agent)
- LangChain (solo loaders y splitters)
- Chroma (vector store local)
- OpenAI text-embedding-3-small (embeddings)
- Google Gemini 3 Flash Preview (LLM del agente)

## Comandos frecuentes
- Ingestar documentos: `python scripts/ingest_documents.py`
- Ejecutar agente: `python main.py`
- Reset datos: `python scripts/reset_data.py`
- Tests: `pytest tests/`
- Lint: `ruff check .` y `ruff format .`

## Reglas críticas
- Todos los documentos en data/documents/ deben tener su metadata en metadata.json
  con los campos: titulo, categoria, vigencia_desde, version, responsable
- Las 3 tools son: search_knowledge_base, create_ticket, escalate_to_human
- Nunca agregar tools que modifiquen datos reales (solo crear tickets locales)
- El agente responde siempre en español
- Cada tool call se loggea en logs/agent.jsonl

## Archivos clave
- agent/system_prompt.md: prompt del sistema del agente
- agent/graph.py: construcción del grafo LangGraph
- tools/: las 3 tools, una por archivo
- rag/ingest.py: pipeline de ingesta a Chroma

## Convenciones
- snake_case en Python
- Docstrings formato Google
- Type hints obligatorios
- Commits separados por archivo
