import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger("usheri")

ESCALATIONS_FILE = Path("data/escalations.jsonl")

VALID_MOTIVES = {
    "sin_informacion",
    "tema_sensible",
    "solicitud_explicita",
    "ambiguedad",
}
VALID_AREAS = {"rrhh", "it", "finanzas", "gerencia", "canal_etico"}

MOTIVE_LABELS: dict[str, str] = {
    "sin_informacion": "Sin información en la base de conocimiento",
    "tema_sensible": "Tema sensible que requiere criterio humano",
    "solicitud_explicita": "El empleado solicitó hablar con un humano",
    "ambiguedad": "Ambigüedad que requiere juicio humano",
}

AREA_LABELS: dict[str, str] = {
    "rrhh": "Gerencia de Personas",
    "it": "Equipo de IT",
    "finanzas": "Área de Finanzas",
    "gerencia": "Gerencia General",
    "canal_etico": "Canal Ético",
}

_escalation_counter = 0


def _next_escalation_id() -> str:
    global _escalation_counter
    _escalation_counter += 1
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"ESC-{ts}-{_escalation_counter:03d}"


@tool
def escalate_to_human(
    motivo: str,
    resumen_consulta: str,
    area_sugerida: str,
) -> dict:
    """Deriva la conversación a un agente humano cuando el sistema no puede
    o no debe resolver la consulta automáticamente.

    Úsala cuando:
      - La base de conocimiento no tiene información relevante sobre la pregunta
      - La consulta involucra temas sensibles: quejas, denuncias, conflictos
        laborales, casos disciplinarios, salud mental, remuneración personal
      - El empleado explícitamente pide hablar con un humano
      - Hay ambigüedad que requiere juicio humano para resolver correctamente

    No la uses cuando: ya encontraste respuesta en la base de conocimiento,
    o cuando la acción se puede manejar con create_ticket.

    Args:
        motivo: una de 'sin_informacion', 'tema_sensible', 'solicitud_explicita',
                'ambiguedad'.
        resumen_consulta: resumen en 1-2 oraciones de lo que el empleado
                          preguntó y por qué requiere humano.
        area_sugerida: una de 'rrhh', 'it', 'finanzas', 'gerencia', 'canal_etico'.

    Returns:
        dict con:
          - escalation_id: str, identificador único
          - estado: 'derivado'
          - area_asignada: área que recibe la conversación
    """
    start = time.time()

    if motivo not in VALID_MOTIVES:
        return {
            "error": f"Motivo inválido '{motivo}'. Válidos: {', '.join(sorted(VALID_MOTIVES))}"
        }

    if area_sugerida not in VALID_AREAS:
        return {
            "error": f"Área inválida '{area_sugerida}'. Válidas: {', '.join(sorted(VALID_AREAS))}"
        }

    escalation_id = _next_escalation_id()
    area_asignada = AREA_LABELS[area_sugerida]

    escalation = {
        "escalation_id": escalation_id,
        "motivo": motivo,
        "motivo_label": MOTIVE_LABELS[motivo],
        "resumen_consulta": resumen_consulta,
        "area_sugerida": area_sugerida,
        "area_asignada": area_asignada,
        "estado": "derivado",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    ESCALATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ESCALATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(escalation, ensure_ascii=False) + "\n")

    duration_ms = round((time.time() - start) * 1000)

    logger.info(
        "escalate_to_human",
        extra={
            "event": "tool_call",
            "tool_name": "escalate_to_human",
            "arguments": {
                "motivo": motivo,
                "area_sugerida": area_sugerida,
            },
        },
    )
    logger.info(
        "escalate_to_human_result",
        extra={
            "event": "tool_result",
            "tool_name": "escalate_to_human",
            "result_summary": f"escalation_id={escalation_id}, area_asignada={area_asignada}",
            "duration_ms": duration_ms,
        },
    )

    return {
        "escalation_id": escalation_id,
        "estado": "derivado",
        "area_asignada": area_asignada,
    }
