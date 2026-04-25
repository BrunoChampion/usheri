import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger("usheri")

TICKETS_FILE = Path("data/tickets.jsonl")

CATEGORY_TO_AREA: dict[str, str] = {
    "it_acceso": "Equipo IT Operaciones",
    "it_hardware": "Equipo IT Infraestructura",
    "it_software": "Equipo IT Aplicaciones",
    "rrhh_solicitud": "Gerencia de Personas",
    "finanzas_gasto": "Área de Finanzas",
    "facilities": "Facilities y Mantenimiento",
}

VALID_CATEGORIES = set(CATEGORY_TO_AREA.keys())
VALID_PRIORITIES = {"baja", "normal", "alta", "urgente"}

PRIORITY_SLA: dict[str, str] = {
    "baja": "72 horas",
    "normal": "24 horas",
    "alta": "8 horas",
    "urgente": "2 horas",
}

_ticket_counter = 0


def _next_ticket_id() -> str:
    global _ticket_counter
    _ticket_counter += 1
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"TCK-{ts}-{_ticket_counter:03d}"


@tool
def create_ticket(
    categoria: str,
    titulo: str,
    descripcion: str,
    prioridad: str = "normal",
    empleado_id: str | None = None,
) -> dict:
    """Crea un ticket operativo cuando el empleado necesita que se ejecute
    una acción concreta: solicitud de acceso a software, reporte de problema
    técnico, solicitud de hardware, solicitud de aprobación de gasto
    fuera de política, etc.

    Úsala cuando la respuesta NO está en la base de conocimiento porque
    requiere una acción, no una consulta.

    No la uses para: consultas de información (usa search_knowledge_base),
    quejas sensibles o denuncias (usa escalate_to_human), consultas que ya
    respondiste con la base de conocimiento.

    Args:
        categoria: una de 'it_acceso', 'it_hardware', 'it_software',
                   'rrhh_solicitud', 'finanzas_gasto', 'facilities'.
        titulo: título corto y descriptivo del ticket (máx 100 caracteres).
        descripcion: descripción completa de la solicitud del empleado,
                     incluyendo contexto relevante.
        prioridad: 'baja', 'normal', 'alta', 'urgente'. Default 'normal'.
        empleado_id: identificador del empleado si se conoce; opcional.

    Returns:
        dict con:
          - ticket_id: str, identificador del ticket creado (ej. 'TCK-20260421-001')
          - estado: 'creado'
          - asignado_a: área responsable según categoría
    """
    start = time.time()

    if categoria not in VALID_CATEGORIES:
        return {
            "error": f"Categoría inválida '{categoria}'. Válidas: {', '.join(sorted(VALID_CATEGORIES))}"
        }

    if prioridad not in VALID_PRIORITIES:
        prioridad = "normal"

    ticket_id = _next_ticket_id()
    asignado_a = CATEGORY_TO_AREA[categoria]

    ticket = {
        "ticket_id": ticket_id,
        "categoria": categoria,
        "titulo": titulo[:100],
        "descripcion": descripcion,
        "prioridad": prioridad,
        "empleado_id": empleado_id,
        "estado": "creado",
        "asignado_a": asignado_a,
        "sla": PRIORITY_SLA.get(prioridad, "24 horas"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TICKETS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(ticket, ensure_ascii=False) + "\n")

    duration_ms = round((time.time() - start) * 1000)

    logger.info(
        "create_ticket",
        extra={
            "event": "tool_call",
            "tool_name": "create_ticket",
            "arguments": {
                "categoria": categoria,
                "titulo": titulo,
                "prioridad": prioridad,
            },
        },
    )
    logger.info(
        "create_ticket_result",
        extra={
            "event": "tool_result",
            "tool_name": "create_ticket",
            "result_summary": f"ticket_id={ticket_id}, asignado_a={asignado_a}",
            "duration_ms": duration_ms,
        },
    )

    return {
        "ticket_id": ticket_id,
        "estado": "creado",
        "asignado_a": asignado_a,
        "sla": PRIORITY_SLA.get(prioridad, "24 horas"),
    }
