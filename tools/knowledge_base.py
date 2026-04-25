import logging
import time

from langchain_core.tools import tool

from rag.retriever import query_knowledge_base

logger = logging.getLogger("usheri")


@tool
def search_knowledge_base(query: str) -> dict:
    """Busca en la base de conocimiento interna de la empresa para responder
    preguntas sobre políticas, procedimientos, beneficios, o procesos internos.

    Úsala cuando el empleado pregunta sobre: vacaciones, licencias, gastos,
    beneficios, políticas de IT, procesos de onboarding/offboarding, código
    de conducta, o cualquier información que viva en un documento oficial
    de la empresa.

    No la uses para: pedir acceso a sistemas (eso es create_ticket),
    reportar incidentes técnicos (eso es create_ticket), o preguntas que
    requieren criterio humano.

    Args:
        query: pregunta específica reformulada para búsqueda semántica.
               Preferentemente en forma afirmativa o con keywords clave.

    Returns:
        dict con campos:
          - results: lista de chunks relevantes con contenido, fuente y metadata
          - found: bool, True si hay al menos un resultado con score > umbral
    """
    start = time.time()
    result = query_knowledge_base(query)
    duration_ms = round((time.time() - start) * 1000)

    num_results = len(result["results"])
    top_score = result["results"][0]["score"] if result["results"] else None

    logger.info(
        "search_knowledge_base",
        extra={
            "event": "tool_call",
            "tool_name": "search_knowledge_base",
            "arguments": {"query": query},
        },
    )
    logger.info(
        "search_knowledge_base_result",
        extra={
            "event": "tool_result",
            "tool_name": "search_knowledge_base",
            "result_summary": f"{num_results} resultados, top_score={top_score}",
            "duration_ms": duration_ms,
        },
    )

    return result
