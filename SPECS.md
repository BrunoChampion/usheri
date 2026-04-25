# Proyecto: Agente Asistente Interno para Empleados (RAG + Acciones)
## Nombre: Usheri

**Autor:** Bruno Champion — NYVEX
**Fecha:** Abril 2026
**Objetivo:** Prototipo funcional que demuestre el loop agéntico completo (razonamiento + RAG + acción externa + escalamiento a humano) en el caso de uso "asistente interno para empleados", aplicable al ICP de NYVEX (empresas B2B LATAM, 20–200 empleados).

---

## 1. Contexto y propósito

### 1.1 Por qué este proyecto

Bruno ya construyó un RAG agéntico de producción (Main + Judge + Regenerator) para Axton IT. El siguiente salto natural en su ruta de aprendizaje es pasar de "RAG con validación interna" a "agente que decide cuándo consultar RAG y cuándo ejecutar acciones externas". Este proyecto es el vehículo mínimo para adquirir esa experiencia antes de proponer capacidades agénticas a clientes actuales o futuros.

### 1.2 Caso de negocio que simula

El agente resuelve consultas de empleados internos de una empresa ficticia sobre políticas, beneficios, procesos de IT y procedimientos de RRHH. Cuando la pregunta tiene respuesta en la documentación, responde directamente; cuando requiere una acción operativa (ej. solicitud de acceso, reporte de incidente), crea un ticket; cuando no tiene información suficiente o la consulta excede su alcance, escala a humano.

Este caso es deliberadamente universal para el ICP: toda empresa mediana tiene documentos de RRHH/IT y empleados repitiendo las mismas preguntas. No requiere CRM ni knowledge base de producto maduro.

### 1.3 Alcance del prototipo

**En alcance:**
- Loop agéntico end-to-end con 3 tools explícitas
- RAG sobre 10–15 documentos de empresa ficticia en español
- Interfaz por terminal (CLI interactivo)
- Logging estructurado de cada decisión del agente
- Persistencia local de tickets y escalamientos (JSON)

**Fuera de alcance (v2+):**
- UI web o integración con Slack/Teams
- Memoria persistente entre sesiones
- Multi-agente
- Autenticación / multi-tenant
- Deployment en cloud
- Evals automatizadas
- Herramientas de escritura que modifiquen datos corporativos reales

---

## 2. Arquitectura del sistema

### 2.1 Diagrama lógico

```
Usuario (CLI)
    │
    ▼
┌──────────────────────────────────────────────────┐
│         LangGraph Agent (ReAct loop)             │
│  ┌────────────────────────────────────────────┐  │
│  │  LLM node: decide acción                   │  │
│  │  - Responder directamente                  │  │
│  │  - Llamar tool                             │  │
│  └────────────────────────────────────────────┘  │
│                    │                             │
│                    ▼                             │
│  ┌────────────────────────────────────────────┐  │
│  │  ToolNode: ejecuta tool solicitada         │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
    │            │            │
    ▼            ▼            ▼
┌────────┐  ┌─────────┐  ┌──────────────┐
│ search │  │ create  │  │ escalate_to  │
│ kb     │  │ ticket  │  │ _human       │
└────────┘  └─────────┘  └──────────────┘
    │            │            │
    ▼            ▼            ▼
 Chroma     tickets.jsonl  escalations.jsonl
(vector DB)   (local)       (local)
```

### 2.2 Componentes principales

1. **Capa de ingesta y RAG**: carga, chunking, embedding y persistencia de documentos en vector store local.
2. **Capa de agente (LangGraph)**: loop ReAct con 3 tools y system prompt específico.
3. **Capa de tools**: funciones Python decoradas, con contratos claros y logging.
4. **Capa de interfaz**: CLI interactivo y logging estructurado.

---

## 3. Stack tecnológico

| Componente | Tecnología | Justificación |
|---|---|---|
| Lenguaje | Python 3.11+ | Ecosistema maduro para LangGraph/LangChain |
| Orquestación agente | LangGraph ≥ 1.0 (stable) | Estándar de producción en 2026; soporte nativo para tool calling, checkpointing y HITL |
| Framework RAG (componentes) | LangChain (loaders, text splitters) | Solo como toolbox de utilidades; no se construyen chains |
| Vector store | Chroma (local, persistente) | Zero-config, integración nativa con LangChain, ideal para prototipo <100k vectores |
| Embeddings | OpenAI `text-embedding-3-small` | Multilingual razonable para español, $0.02/M tokens, 1536 dims |
| LLM del agente | Google `gemini-3-flash-preview` | Modelo rápido y de bajo costo ($0.50/M input, $3/M output) con tool use nativo; diseñado para agentic workflows. En preview a abril 2026. |
| Gestión de dependencias | `uv` o `pip` con `requirements.txt` | uv preferido por velocidad; pip aceptable |
| Variables de entorno | `.env` + `python-dotenv` | Estándar |
| Logging | `logging` stdlib + formato JSON estructurado | Suficiente para prototipo |

### 3.1 Nota sobre elección de LangGraph vs código puro

Bruno ya dominó el loop agéntico en código puro en Axton. El objetivo aquí **no es reaprender el loop, sino aprender la abstracción que se usa en producción con clientes B2B**. LangGraph es la opción correcta porque:

- Control de flujo explícito como grafo de estados (alineado con necesidades empresariales de auditabilidad).
- Primitivas nativas para human-in-the-loop, checkpointing y streaming.
- Portable a futuros clientes sin reescribir arquitectura.

### 3.2 Nota sobre `create_react_agent` vs `StateGraph` manual

**Recomendación para v1 del prototipo: usar `create_react_agent` de `langgraph.prebuilt`.**

La regla práctica de la documentación oficial de LangGraph 2026: empezar con `create_react_agent` para agentes estándar con tools; migrar a `StateGraph` manual solo cuando se necesite control de flujo paralelo, patrones supervisor-worker, lógica de retry custom o ramificación compleja.

Para este prototipo (3 tools, loop ReAct estándar, sin ramificación custom), `create_react_agent` es suficiente y más limpio. Si en una v2 se quiere agregar un nodo de guardrails o un nodo de aprobación humana previo al `create_ticket`, ahí se migra a `StateGraph`.

---

## 4. Empresa ficticia y documentos

### 4.1 Nombre y contexto

**Empresa ficticia:** `Amaru Soluciones S.A.C.`
- Sector: servicios de consultoría en transformación digital
- Tamaño: 85 empleados
- Ubicación: Lima, Perú
- Idioma de documentos: español (Perú)

Amaru es deliberadamente plausible como cliente del ICP de NYVEX. Los documentos deben estar redactados en español natural, con el tono típico de un manual corporativo peruano/latinoamericano.

### 4.2 Documentos base

Ubicación: `data/documents/`. Formatos soportados: Markdown (`.md`), PDF (`.pdf`), Microsoft Word (`.docx`).

Los documentos son provistos externamente y no se asumen nombres de archivo específicos. El pipeline de ingesta procesa automáticamente todos los archivos `.md`, `.pdf` y `.docx` presentes en `data/documents/`. Para ejecutar la ingesta, correr:

```bash
python scripts/ingest_documents.py
```

El script es idempotente: elimina la colección existente y la recrea con los documentos actuales.

Se recomienda cubrir como mínimo los siguientes temas para que el agente pueda manejar los escenarios de prueba (sección 11):

- Introducción general y valores de la empresa
- Política de vacaciones (días, proceso de solicitud, restricciones)
- Política de gastos reembolsables (categorías, límites, aprobación)
- Política de home office (elegibilidad, días, requerimientos)
- Política de licencias (maternidad, paternidad, enfermedad, duelo)
- Procedimiento de onboarding y offboarding
- FAQ de IT (accesos, VPN, software, hardware)
- Política de seguridad de la información
- Política de capacitación
- Política de beneficios
- Código de conducta y canal ético
- Directorio de áreas y contactos de escalamiento

### 4.3 Metadata de documentos

Cada documento debe tener metadata asociada (título, categoría, vigencia, versión, responsable) para que el agente pueda citar fuentes y para habilitar filtros futuros en el vector store.

La metadata se proporciona mediante un **archivo de manifiesto** ubicado en `data/documents/metadata.json`. Este archivo es la única fuente de verdad para la metadata de todos los documentos, independientemente de su formato.

Estructura del manifiesto:

```json
{
  "politica_vacaciones.pdf": {
    "titulo": "Política de Vacaciones",
    "categoria": "rrhh",
    "vigencia_desde": "2025-01-15",
    "vigencia_hasta": null,
    "version": "2.3",
    "responsable": "Gerencia de Personas"
  },
  "codigo_conducta.docx": {
    "titulo": "Código de Conducta",
    "categoria": "rrhh",
    "vigencia_desde": "2024-06-01",
    "vigencia_hasta": null,
    "version": "1.1",
    "responsable": "Gerencia de Personas"
  }
}
```

Si un archivo en `data/documents/` no tiene entrada en el manifiesto, la ingesta procede con metadata mínima (`titulo` = nombre del archivo sin extensión, `categoria` = `"sin_categoria"`) y se emite un warning en el log.

### 4.4 Regla de contenido

Cada documento debe tener al menos **un detalle específico verificable** (un número, un plazo, un monto, un nombre de rol). Esto es crítico porque el agente debe poder distinguir entre "el RAG respondió con información concreta" vs "el RAG no tiene la información".

Ejemplo (para un documento de política de vacaciones):
- "Los empleados con menos de 1 año acumulan 1.25 días por mes trabajado."
- "La solicitud debe hacerse con al menos 15 días calendario de anticipación."
- "El responsable de aprobación es el jefe directo, con visto bueno de Gerencia de Personas."

---

## 5. Capa de ingesta y RAG

### 5.1 Pipeline de ingesta

Script: `scripts/ingest_documents.py`

Pasos:
1. Cargar todos los documentos en `data/documents/` usando el loader apropiado según extensión:
   - `.md` → `UnstructuredMarkdownLoader` o `TextLoader`
   - `.pdf` → `PyPDFLoader` o `UnstructuredPDFLoader`
   - `.docx` → `Docx2txtLoader` o `UnstructuredWordDocumentLoader`
2. Cargar el manifiesto de metadata desde `data/documents/metadata.json` y asociar cada documento con su metadata. Para archivos sin entrada en el manifiesto, asignar metadata mínima y emitir warning.
3. Aplicar chunking con `RecursiveCharacterTextSplitter`:
   - `chunk_size=512` tokens (aprox. 2000 caracteres)
   - `chunk_overlap=80` tokens (aprox. 320 caracteres, ~15%)
   - `separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""]` (para `.md`); para PDF/Word usar separadores genéricos `["\n\n", "\n", ". ", " ", ""]`
4. Generar embeddings con `text-embedding-3-small` (1536 dims).
5. Persistir en Chroma en `data/chroma_db/`.

### 5.2 Justificación de la estrategia de chunking

Según benchmarks 2026 (NVIDIA, Chroma Research, FloTorch), la configuración 512 tokens + 10–20% overlap con recursive splitter es el punto de partida validado para queries factuales sobre documentos de políticas. Se evita semantic chunking porque:
- Aumenta costo de embedding sin ganancia garantizada en corpus pequeño.
- FloTorch 2026 encontró que semantic chunking produce fragmentos muy pequeños (~43 tokens) que degradan accuracy al 54% vs 69% de recursive 512.
- El objetivo del prototipo es demostrar el loop, no optimizar retrieval.

El uso de separators que respetan headers Markdown es una mejora barata sobre el default para archivos `.md`, ya que los documentos de RRHH suelen tener estructura jerárquica clara. Para PDF y Word, que pierden la estructura de headings al extraer texto, se usan separadores genéricos.

### 5.3 Índice vectorial

- Colección única: `amaru_policies`
- Distancia: cosine similarity (default Chroma)
- Persistencia: sí, en disco local
- Re-ingesta: script idempotente que elimina la colección y la recrea si se corre de nuevo

### 5.4 Query del RAG

Función: `tools/knowledge_base.py::search_knowledge_base`

Parámetros:
- `query: str` — pregunta del empleado o sub-pregunta del agente
- `top_k: int = 5` — número de chunks a recuperar

Retorno: lista de dicts con:
- `content: str` — texto del chunk
- `source: str` — nombre del documento
- `metadata: dict` — metadata completa del documento (incluye `titulo`, `categoria`, `version`, `vigencia_desde`)
- `score: float` — score de similitud

---

## 6. Las 3 tools del agente

### 6.1 Tool 1: `search_knowledge_base`

**Propósito:** Consultar documentación interna para responder preguntas sobre políticas, procedimientos y beneficios.

**Firma:**
```python
@tool
def search_knowledge_base(query: str) -> dict:
    """
    Busca en la base de conocimiento interna de la empresa para responder
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
```

**Comportamiento:**
- Llama al vector store con `top_k=5`.
- Si ningún chunk supera un umbral mínimo de similitud (ej. score < 0.3 con cosine distance invertido), devuelve `found=False` y lista vacía. Esto es señal explícita para que el agente decida escalar.
- Incluye metadata completa para que el agente pueda citar fuente y versión del documento.

**Logging:** cada llamada loggea query original, número de resultados, y top score.

### 6.2 Tool 2: `create_ticket`

**Propósito:** Crear un ticket en el sistema de gestión para acciones operativas que requieren ejecución humana o de un sistema backend.

**Firma:**
```python
@tool
def create_ticket(
    categoria: str,
    titulo: str,
    descripcion: str,
    prioridad: str = "normal",
    empleado_id: str | None = None,
) -> dict:
    """
    Crea un ticket operativo cuando el empleado necesita que se ejecute
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
```

**Comportamiento:**
- Genera un `ticket_id` usando timestamp + contador.
- Mapea categoría a área responsable (ej. `it_acceso` → "Equipo IT Operaciones").
- Persiste el ticket en `data/tickets.jsonl` como una línea JSON.
- Retorna el `ticket_id` para que el agente pueda mencionárselo al empleado.

**Logging:** cada ticket creado se loggea con full payload.

### 6.3 Tool 3: `escalate_to_human`

**Propósito:** Derivar la conversación a un humano cuando el agente no puede responder con confianza, cuando la consulta es sensible, o cuando la política explícitamente requiere juicio humano.

**Firma:**
```python
@tool
def escalate_to_human(
    motivo: str,
    resumen_consulta: str,
    area_sugerida: str,
) -> dict:
    """
    Deriva la conversación a un agente humano cuando el sistema no puede
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
```

**Comportamiento:**
- Genera `escalation_id` con timestamp.
- Persiste en `data/escalations.jsonl`.
- Retorna confirmación para que el agente informe al empleado.

**Logging:** cada escalamiento se loggea con motivo y área.

### 6.4 Nota sobre la separación de tools

La decisión arquitectónica de tener `create_ticket` y `escalate_to_human` como tools separadas (en vez de una sola tool de "acción") es deliberada y refleja distinciones operativas reales:

- `create_ticket` → acción ejecutable con SLA definido (ej. IT atiende tickets de acceso en 4h)
- `escalate_to_human` → conversación derivada a una persona para juicio contextual

Separarlas permite métricas distintas (tasa de escalamiento vs tasa de creación de tickets) y rutas distintas en los sistemas destino (cola de tickets vs cola de conversaciones asignadas).

---

## 7. Construcción del agente (LangGraph)

### 7.1 System prompt del agente

Archivo: `agent/system_prompt.md`

Estructura:

```
Eres el asistente interno de Amaru Soluciones S.A.C., una empresa peruana
de consultoría en transformación digital con 85 empleados. Tu rol es
ayudar a los empleados con consultas sobre políticas internas,
procedimientos, y solicitudes operativas.

Tienes acceso a 3 herramientas:

1. search_knowledge_base: para buscar en la documentación interna
2. create_ticket: para crear solicitudes operativas
3. escalate_to_human: para derivar a un humano cuando no puedes resolver

REGLAS DE DECISIÓN:

1. Si la pregunta es sobre información (políticas, beneficios, procedimientos,
   procesos), SIEMPRE llama primero a search_knowledge_base.

2. Si search_knowledge_base devuelve resultados relevantes, responde al
   empleado con esa información, citando el documento fuente y su versión.
   Ejemplo: "Según la Política de Vacaciones (v2.3, vigente desde enero
   2025), tienes derecho a..."

3. Si search_knowledge_base no devuelve resultados relevantes (found=False),
   escala a humano con motivo 'sin_informacion'.

4. Si la pregunta requiere una acción operativa (solicitar algo, reportar
   algo), usa create_ticket con la categoría apropiada.

5. Si la consulta involucra temas sensibles (quejas, denuncias, conflictos,
   salud mental, remuneración personal), escala a humano con motivo
   'tema_sensible' SIN intentar responder, incluso si tienes información.

6. Si el empleado pide explícitamente hablar con un humano, escala
   inmediatamente con motivo 'solicitud_explicita'.

7. Nunca inventes información. Si no sabes algo y la herramienta no lo
   resuelve, escala.

8. Cita siempre las fuentes de la documentación cuando respondas con
   información de la base de conocimiento. Incluye nombre del documento
   y versión.

9. Mantén un tono profesional pero cercano, apropiado para comunicación
   interna en una empresa peruana.

10. Responde siempre en español.

FORMATO DE RESPUESTA:

- Si respondes con información: breve + cita de fuente
- Si creas ticket: confirma el ticket_id y el SLA esperado por categoría
- Si escalas: explica al empleado que se ha derivado la consulta y el
  área asignada
```

### 7.2 Construcción del grafo

Archivo: `agent/graph.py`

```python
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.knowledge_base import search_knowledge_base
from tools.ticketing import create_ticket
from tools.escalation import escalate_to_human

def build_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=1.0,  # Gemini 3+ requiere temperature >= 1.0; valores bajos
                          # causan loops infinitos y degradación de razonamiento
                          # (fuerte recomendación oficial de Google / LangChain).
        max_output_tokens=2048,
    )

    tools = [search_knowledge_base, create_ticket, escalate_to_human]

    with open("agent/system_prompt.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    return agent
```

**Nota crítica sobre `temperature`:** A diferencia de otros LLMs donde `temperature=0` se usa para decisiones deterministas de tool selection, Gemini 3+ requiere `temperature=1.0` por política oficial de Google. LangChain incluso fuerza automáticamente este valor si no se especifica explícitamente. Setear `temperature=0` con Gemini 3 causa loops infinitos y falla en tareas complejas. Este es un cambio de intuición respecto a Claude/GPT: la determinismo del tool selection depende del prompt y del training del modelo, no del parámetro temperature.

### 7.3 Ejecución del agente

```python
from langchain_core.messages import HumanMessage

agent = build_agent()

result = agent.invoke({
    "messages": [HumanMessage(content=user_input)]
})

# El resultado contiene toda la conversación incluyendo tool calls.
# La respuesta final al usuario es el último AIMessage sin tool_calls.
```

### 7.4 Streaming (opcional para v1, deseable para UX)

Si hay tiempo, implementar streaming con `agent.stream()` para mostrar razonamiento en tiempo real en la CLI. No es bloqueante para el prototipo.

---

## 8. Capa de interfaz: CLI

### 8.1 Archivo principal

`main.py`

### 8.2 Comportamiento

- Imprime banner con nombre de empresa ficticia y versión del sistema.
- Loop interactivo: pide input del empleado, pasa al agente, imprime respuesta.
- Comandos especiales:
  - `/exit` o `/quit`: salir
  - `/reset`: limpiar historial de conversación actual
  - `/debug`: alternar modo verbose (muestra tool calls y razonamiento del agente)
  - `/stats`: muestra tickets creados y escalamientos en la sesión actual
- Si el agente llama a una tool, muestra en modo debug qué tool y con qué argumentos.

### 8.3 Formato de salida

En modo normal:
```
[Amaru Asistente]: [respuesta del agente]
```

En modo debug:
```
[DEBUG] → tool_call: search_knowledge_base(query="...")
[DEBUG] ← 3 resultados, top_score=0.78
[Amaru Asistente]: [respuesta del agente]
```

---

## 9. Logging y observabilidad

### 9.1 Estrategia

Logging estructurado en JSON, una línea por evento, escrito a `logs/agent.jsonl`.

### 9.2 Eventos a loggear

| Evento | Campos |
|---|---|
| `conversation_start` | timestamp, session_id |
| `user_message` | session_id, content, turn_number |
| `agent_response` | session_id, content, turn_number, num_tool_calls |
| `tool_call` | session_id, tool_name, arguments, turn_number |
| `tool_result` | session_id, tool_name, result_summary, duration_ms |
| `error` | session_id, error_type, message, traceback |

### 9.3 Por qué importa

Los logs son el artefacto principal que Bruno va a revisar para entender qué hizo el agente y dónde falló. Sin logs estructurados no hay aprendizaje sistemático, solo "pareció funcionar".

---

## 10. Estructura del repositorio

```
proyecto_agente/
├── AGENTS.md                    # Contexto persistente para que puedas desarrollar el sistema
├── README.md                    # Instrucciones de setup y uso
├── pyproject.toml (o requirements.txt)
├── .env.example
├── .gitignore
├── main.py                      # Entry point CLI
├── agent/
│   ├── __init__.py
│   ├── graph.py                 # Construcción del agente LangGraph
│   └── system_prompt.md         # Prompt del sistema
├── tools/
│   ├── __init__.py
│   ├── knowledge_base.py        # Tool 1: search_knowledge_base
│   ├── ticketing.py             # Tool 2: create_ticket
│   └── escalation.py            # Tool 3: escalate_to_human
├── rag/
│   ├── __init__.py
│   ├── ingest.py                # Pipeline de ingesta
│   └── retriever.py             # Wrapper de Chroma para query
├── scripts/
│   ├── ingest_documents.py      # Script ejecutable para ingesta inicial
│   └── reset_data.py            # Limpia tickets/escalations/logs
├── data/
│   ├── documents/               # Documentos de Amaru (.md, .pdf, .docx) + metadata.json (input)
│   ├── chroma_db/               # Persistencia del vector store (output)
│   ├── tickets.jsonl            # Tickets creados (output)
│   └── escalations.jsonl        # Escalamientos (output)
├── logs/
│   └── agent.jsonl              # Logs estructurados
└── tests/
    ├── test_tools.py            # Tests unitarios de las 3 tools
    └── test_agent_scenarios.py  # Tests de escenarios end-to-end
```

---

## 11. Escenarios de prueba (aceptación del prototipo)

El prototipo se considera funcional si maneja correctamente los siguientes 6 escenarios:

### Escenario A: Respuesta directa desde RAG
**Input:** "¿Cuántos días de vacaciones tengo derecho al año?"
**Comportamiento esperado:** agente llama `search_knowledge_base`, recibe chunks de política de vacaciones, responde con información específica citando el documento y versión.

### Escenario B: Creación de ticket operativo
**Input:** "Necesito acceso al software Figma para el proyecto del cliente X."
**Comportamiento esperado:** agente llama `create_ticket` con categoría `it_software`, responde con ticket_id y SLA.

### Escenario C: Escalamiento por falta de información
**Input:** "¿Cuál es el bono de desempeño específico de mi posición como Analista Senior de Datos?"
**Comportamiento esperado:** agente llama `search_knowledge_base`, no encuentra información específica por rol, llama `escalate_to_human` con motivo `sin_informacion` y área `rrhh`.

### Escenario D: Escalamiento por tema sensible
**Input:** "Quiero reportar una situación de acoso laboral que estoy viviendo con mi jefe."
**Comportamiento esperado:** agente escala inmediatamente con motivo `tema_sensible` y área `canal_etico`, SIN intentar responder desde el RAG aunque haya un documento de código de conducta.

### Escenario E: Respuesta compuesta (RAG + ticket)
**Input:** "Quiero solicitar home office los próximos 3 viernes, ¿qué tengo que hacer?"
**Comportamiento esperado:** agente llama `search_knowledge_base` para explicar la política, responde con la información, y luego llama `create_ticket` con categoría `rrhh_solicitud` para registrar la solicitud formal.

### Escenario F: Solicitud explícita de humano
**Input:** "Prefiero hablar con alguien de RRHH directamente."
**Comportamiento esperado:** agente escala inmediatamente con motivo `solicitud_explicita` y área `rrhh`.

---

## 12. Configuración de entorno

### 12.1 Variables de entorno (`.env`)

```
GOOGLE_API_KEY=...              # API key de Google AI Studio (ai.dev)
OPENAI_API_KEY=sk-...           # Solo para embeddings
LOG_LEVEL=INFO
CHROMA_PERSIST_DIR=./data/chroma_db
```

### 12.2 Dependencias principales (`requirements.txt`)

```
langgraph>=1.0.0
langchain>=0.3.0
langchain-google-genai>=4.1.1
langchain-openai>=0.2.0
langchain-chroma>=0.1.0
langchain-community>=0.3.0
chromadb>=0.5.0
python-dotenv>=1.0.0
pydantic>=2.0.0
tiktoken>=0.7.0
pypdf>=4.0.0
docx2txt>=0.9
unstructured>=0.15.0
```

### 12.3 Comandos de setup

```bash
# 1. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables
cp .env.example .env
# editar .env con las API keys

# 4. Ingestar documentos (primera vez o después de cambios)
python scripts/ingest_documents.py

# 5. Ejecutar agente
python main.py
```

---

## 13. Convenciones de código

- **Estilo:** `ruff` para linting y formatting. Configuración en `pyproject.toml`.
- **Tipado:** type hints obligatorios en toda función pública.
- **Docstrings:** formato Google en todas las funciones con docstring.
- **Imports:** absolute imports, no relativos.
- **Nombres:** snake_case para funciones y variables, PascalCase para clases, UPPER_SNAKE para constantes.
- **Comentarios:** en español en archivos de negocio (tools, prompts); en inglés en infraestructura (graph, ingest).
- **Commits:** uno por archivo cambiado con mensaje descriptivo (facilita revisión posterior).

---

## 14. AGENTS.md del proyecto

Crear `AGENTS.md` en la raíz con el siguiente contenido:

```markdown
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
- Nunca agregar tools que modifiquen datos reales (solo crear tickets
  locales)
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
```

---

## 15. Plan de ejecución sugerido (3 días)

### Día 1: Fundación (~3h)

- Setup de repositorio, estructura de carpetas, `pyproject.toml` / `requirements.txt`
- Crear los 15 documentos en `data/documents/` con contenido realista en español
- Implementar pipeline de ingesta (`rag/ingest.py`) y ejecutar una vez
- Verificar queries directas al retriever sin agente (`rag/retriever.py::test_query()`)

**Criterio de éxito día 1:** Se puede hacer una query al vector store y recibir chunks relevantes con metadata.

### Día 2: Agente (~3h)

- Implementar las 3 tools con logging estructurado
- Escribir system prompt
- Construir el agente con `create_react_agent`
- CLI básica en `main.py`
- Ejecutar los 6 escenarios de prueba manualmente

**Criterio de éxito día 2:** Los 6 escenarios producen la secuencia correcta de tool calls y respuestas razonables.

### Día 3: Pulido y aprendizaje (~2h)

- Revisar logs de los 6 escenarios e identificar comportamientos inesperados
- Ajustar system prompt si hay bugs de decisión
- Agregar modo `/debug` y `/stats` en CLI
- Documentar en README qué aprendiste y qué preguntas nuevas quedaron
- Opcional: tests unitarios mínimos de las 3 tools

**Criterio de éxito día 3:** README con reflexiones de aprendizaje, listo para demostrar en reuniones.

---

## 16. Qué NO hacer

- No agregar más tools "porque se ve útil". Las 3 tools son el alcance.
- No migrar a `StateGraph` manual si `create_react_agent` funciona. Migración es para v2.
- No conectar a APIs externas reales (Slack, Linear, Jira). Todo es local.
- No agregar autenticación, multi-tenant ni memoria persistente.
- No implementar UI web. La CLI es suficiente.
- No optimizar prematuramente (rerankers, hybrid search, semantic chunking, cache). El objetivo es el loop, no la performance de retrieval.
- No generar documentos ficticios con información falsa sobre leyes peruanas reales que puedan confundir. Preferir inventar estructuras plausibles sin afirmar cumplimiento normativo específico.

---

## 17. Validación de integración (chequeo final)

Los componentes elegidos integran sin fricción porque:

1. **LangGraph + `create_react_agent` + tools Python decoradas con `@tool`** es el patrón nativo documentado en LangGraph v1.0+ para agentes ReAct estándar con hasta 15 tools (aquí usamos 3).

2. **Chroma + LangChain** tienen integración de primera clase vía `langchain_chroma.Chroma`. Persistencia local sin servidor adicional.

3. **OpenAI embeddings (text-embedding-3-small) + Chroma** es una combinación probada y sin fricción. 1536 dimensiones, multilingual razonable para español, costo despreciable en el volumen del prototipo (~$0.01 total para ingesta de 15 documentos).

4. **Google Gemini 3 Flash Preview como LLM del agente + LangChain `ChatGoogleGenerativeAI`** tiene soporte nativo para tool use desde `langchain-google-genai` 4.1.1+. Gemini 3 Flash está diseñado específicamente para agentic workflows y tiene pricing competitivo ($0.50/M input, $3/M output). **Importante:** requiere `temperature=1.0` (no 0), a diferencia de Claude/GPT.

5. **Chunking recursive 512/80 + RecursiveCharacterTextSplitter de LangChain** es el default validado de la industria para documentos de políticas en 2026.

6. **JSONL para tickets/escalations/logs** no tiene dependencias adicionales, es append-only (seguro ante fallos), y se puede leer con cualquier herramienta.

No hay incompatibilidades de versiones conocidas entre estos componentes a abril 2026. El único punto de atención es mantener LangGraph >=1.0 para usar la API estable de `create_react_agent` desde `langgraph.prebuilt`.

---

## 18. Siguiente paso post-prototipo

Una vez funcionando, las extensiones naturales (no parte de v1) son:

1. **Human-in-the-loop real** con `interrupt()` de LangGraph: antes de crear ticket de alta prioridad, pedir confirmación.
2. **Streaming de respuestas** a CLI para mejor UX.
3. **Migración a StateGraph manual** para agregar nodos custom (ej. nodo de validación pre-tool-call).
4. **Observabilidad con LangSmith** (opcional, requiere cuenta).
5. **Evals automatizadas** con dataset fijo de las 6+ preguntas de aceptación.
6. **Integración con Slack** como canal real de conversación.

Estas extensiones son material de posts futuros para LinkedIn y de conversaciones con Gonzalo o la PM de la clínica sobre capacidades agénticas.
