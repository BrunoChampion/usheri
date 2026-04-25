import io
import json
import logging
import sys
import uuid

if sys.platform == "win32":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding="utf-8")


from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent.graph import build_agent
from rag.logging_config import log_event, setup_logging

load_dotenv()

SESSION_ID = uuid.uuid4().hex[:8]
BANNER = """
╔══════════════════════════════════════════════════════════╗
║          Amaru Asistente Interno — Usheri v0.1           ║
║   Empresa ficticia: Amaru Soluciones S.A.C. (85 emp.)   ║
╠══════════════════════════════════════════════════════════╣
║  Comandos: /exit · /quit · /reset · /debug · /stats     ║
╚══════════════════════════════════════════════════════════╝
"""


def _extract_response_text(content: str | list | dict) -> str:
    """Extrae texto limpio de la respuesta del LLM.

    Gemini puede devolver el contenido como string plano o como lista
    de dicts con campos 'type', 'text' y 'extras'. Esta función normaliza
    cualquier formato a un string legible.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return content.get("text", str(content))
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts)
    return str(content)


def _format_tool_call(name: str, args: dict) -> str:
    args_str = ", ".join(
        f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}" for k, v in args.items()
    )
    return f"→ tool_call: {name}({args_str})"


def _format_tool_result(name: str, result: dict | list | str) -> str:
    if isinstance(result, dict):
        if "ticket_id" in result:
            return f"← {name}: ticket_id={result['ticket_id']}, asignado_a={result.get('asignado_a', 'N/A')}"
        if "escalation_id" in result:
            return f"← {name}: escalation_id={result['escalation_id']}, area_asignada={result.get('area_asignada', 'N/A')}"
        if "found" in result:
            num = len(result.get("results", []))
            return f"← {name}: {num} resultados, found={result['found']}"
        return f"← {name}: {json.dumps(result, ensure_ascii=False)[:120]}"
    return f"← {name}: {str(result)[:120]}"


def _get_session_stats() -> dict:
    stats: dict = {"tickets": 0, "escalations": 0}
    try:
        with open("data/tickets.jsonl", encoding="utf-8") as f:
            stats["tickets"] = sum(1 for _ in f)
    except FileNotFoundError:
        pass
    try:
        with open("data/escalations.jsonl", encoding="utf-8") as f:
            stats["escalations"] = sum(1 for _ in f)
    except FileNotFoundError:
        pass
    return stats


def main() -> None:
    setup_logging()
    logger = logging.getLogger("usheri")

    print(BANNER)

    agent = build_agent()
    messages: list = []
    debug_mode = False
    turn = 0

    log_event("conversation_start", session_id=SESSION_ID)

    while True:
        try:
            user_input = input("\n[Tú]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n¡Hasta luego!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/exit", "/quit"):
            print("¡Hasta luego!")
            break

        if user_input.lower() == "/reset":
            messages = []
            turn = 0
            print("[Sistema] Conversación reiniciada.")
            continue

        if user_input.lower() == "/debug":
            debug_mode = not debug_mode
            print(f"[Sistema] Modo debug: {'ON' if debug_mode else 'OFF'}")
            continue

        if user_input.lower() == "/stats":
            stats = _get_session_stats()
            print(
                f"[Sistema] Tickets creados: {stats['tickets']} | Escalamientos: {stats['escalations']}"
            )
            continue

        turn += 1
        log_event(
            "user_message", session_id=SESSION_ID, content=user_input, turn_number=turn
        )

        messages.append(HumanMessage(content=user_input))

        try:
            result = agent.invoke({"messages": messages})
        except Exception as e:
            logger.error(
                "agent_error",
                extra={
                    "event": "error",
                    "error_type": type(e).__name__,
                    "traceback": str(e),
                },
            )
            print(f"[Error] {e}")
            messages.pop()
            continue

        response_messages = result.get("messages", [])
        messages = response_messages

        final_response = ""
        for msg in response_messages:
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                final_response = _extract_response_text(msg.content)
            if debug_mode and isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"[DEBUG] {_format_tool_call(tc['name'], tc['args'])}")
            if debug_mode and isinstance(msg, ToolMessage):
                tool_name = msg.name or "unknown"
                try:
                    content = (
                        json.loads(msg.content)
                        if isinstance(msg.content, str)
                        else msg.content
                    )
                    print(f"[DEBUG] {_format_tool_result(tool_name, content)}")
                except (json.JSONDecodeError, TypeError):
                    print(f"[DEBUG] ← {tool_name}: {str(msg.content)[:120]}")

        if final_response:
            print(f"\n[Amaru Asistente]: {final_response}")
            log_event(
                "agent_response",
                session_id=SESSION_ID,
                content=final_response,
                turn_number=turn,
            )
        else:
            print("\n[Amaru Asistente]: (sin respuesta textual)")


if __name__ == "__main__":
    main()
