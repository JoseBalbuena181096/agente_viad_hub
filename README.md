# VIAD Bot — Agente Conversacional de IA Generativa

Backend del chatbot conversacional para el **VIAD HUB** del Consorcio Educativo de Oriente (CEO). Agente inteligente que busca en la biblioteca de prompts y videos, genera prompts personalizados y responde consultas sobre IA Generativa.

**Producción:** [web-production-ccc6a.up.railway.app](https://web-production-ccc6a.up.railway.app)
**Frontend:** [ceo-ia-hub-tu7s.vercel.app](https://ceo-ia-hub-tu7s.vercel.app) (repo: ceo_ia_hub)

## Tech Stack

- **FastAPI** — API REST + SSE streaming
- **LangGraph** — Orquestación del agente (StateGraph)
- **LangChain** — Integración con Gemini, tools, embeddings
- **Google Gemini 3 Flash Preview** — LLM principal (temperatura 1.0, streaming)
- **Google Gemini Embedding 001** — Embeddings de 3072 dimensiones
- **Supabase** — Base de datos (REST API) para mensajes, conversaciones y vectores
- **sse-starlette** — Server-Sent Events para streaming de tokens
- **Uvicorn** — Servidor ASGI

## Arquitectura del Agente

```
Usuario → POST /api/v1/chat (SSE)
               │
               ▼
         ┌──────────┐
         │  setup   │ ← Carga perfil del usuario (nombre, departamento)
         └────┬─────┘
              ▼
         ┌──────────┐     ┌────────────────┐
         │ generate │────▶│    tools       │
         │ (Gemini) │◀────│ search_library │
         └────┬─────┘     │ search_videos  │
              │           │ generate_prompt│
              ▼           └────────────────┘
         ┌──────────────┐
         │ save_message │ ← Guarda en Supabase + genera título
         └──────┬───────┘
                ▼
               END
```

### Flujo del agente:

1. **setup** — Carga nombre y departamento del usuario desde Supabase
2. **generate** — Gemini decide si responder directamente o usar herramientas
3. **tools** — Si necesita buscar, ejecuta las herramientas (RAG con similarity search)
4. **generate** — Procesa resultados de herramientas y genera respuesta final
5. **save_message** — Persiste mensajes en Supabase y genera título automático

### Herramientas (Tools):

| Tool | Descripción |
|---|---|
| `search_library` | Busca prompts similares usando embeddings (top 3) |
| `search_videos` | Busca videos similares usando embeddings (top 3) |
| `generate_prompt` | Genera un prompt profesional personalizado con Gemini |

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/chat` | Chat con streaming SSE |
| GET | `/api/v1/conversations?user_id=` | Listar conversaciones |
| GET | `/api/v1/conversations/{id}/messages` | Mensajes de una conversación |
| POST | `/api/v1/conversations` | Crear conversación |
| PATCH | `/api/v1/conversations/{id}` | Actualizar título |
| DELETE | `/api/v1/conversations/{id}` | Eliminar conversación |
| POST | `/api/v1/vectorize/batch` | Vectorizar prompts y videos |

### Eventos SSE del chat:

| Evento | Descripción |
|---|---|
| `metadata` | `conversation_id` (al inicio) |
| `token` | Token de texto del LLM |
| `tool_call` | Nombre y args de herramienta invocada |
| `tool_result` | Resultado de herramienta |
| `error` | Mensaje de error |
| `done` | Fin del stream |

## Inicio rápido

### Requisitos

- Python 3.11+
- Proyecto en Supabase con tablas y embeddings configurados
- API Key de Google (Gemini)

### Instalación

```bash
git clone https://github.com/JoseBalbuena181096/agente_viad_hub.git
cd agente_viad_hub
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Variables de entorno

Crear `.env` en la raíz:

```env
GOOGLE_API_KEY=tu-google-api-key
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
```

### Desarrollo

```bash
uvicorn main:app --reload --port 8000
```

## Estructura del proyecto

```
agente_viad_hub/
├── main.py                    # FastAPI app, CORS, rutas
├── Procfile                   # Comando de inicio (Railway)
├── railway.json               # Configuración Railway
├── requirements.txt           # Dependencias Python
├── runtime.txt                # Versión Python
└── app/
    ├── api/
    │   ├── health.py          # GET /health
    │   ├── chat.py            # POST /api/v1/chat (SSE streaming)
    │   ├── conversations.py   # CRUD conversaciones y mensajes
    │   └── vectorize.py       # POST /api/v1/vectorize/batch
    ├── core/
    │   ├── config.py          # Settings (env vars)
    │   ├── state.py           # AgentState (TypedDict para LangGraph)
    │   └── prompts.py         # System prompts del bot
    ├── graph/
    │   ├── builder.py         # Construcción del StateGraph
    │   ├── checkpointer.py    # MemorySaver (checkpointer en memoria)
    │   └── nodes/
    │       ├── setup.py       # Carga perfil usuario
    │       ├── generate.py    # Nodo principal (Gemini + tools)
    │       └── save_message.py # Persistencia en Supabase
    ├── schemas/
    │   ├── chat.py            # ChatRequest schema
    │   ├── conversation.py    # Conversation schemas
    │   └── vectorize.py       # Vectorize schemas
    ├── services/
    │   ├── llm.py             # Gemini LLM + embeddings + safe_text()
    │   ├── supabase.py        # Cliente Supabase (REST API)
    │   ├── embeddings.py      # Generación de embeddings
    │   ├── rag.py             # Similarity search via RPC
    │   └── vectorize.py       # Batch vectorization service
    └── tools/
        ├── search_library.py  # Tool: buscar prompts (RAG)
        ├── search_videos.py   # Tool: buscar videos (RAG)
        └── generate_prompt.py # Tool: generar prompt con Gemini
```

## Despliegue (Railway)

El proyecto se despliega automáticamente en Railway al hacer push a `main`.

- **Builder:** Nixpacks
- **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
- **Health check:** `/health`
- **Workers:** 1 (MemorySaver requiere proceso único para consistencia de contexto)

### Variables de entorno en Railway:

- `GOOGLE_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DB_URL` (opcional, para PostgresSaver futuro)
- `CORS_ORIGINS` (opcional, orígenes adicionales separados por coma)

## Notas técnicas

- **MemorySaver:** El checkpointer usa memoria en proceso. Los mensajes se persisten en Supabase via REST API, pero el contexto del thread LangGraph se pierde si Railway reinicia.
- **Gemini 3 Flash Preview:** Requiere `temperature=1.0`. Retorna contenido como lista de bloques `[{"type": "text", "text": "..."}]` — se maneja con `safe_text()`.
- **Stream filtering:** Solo se envían tokens del nodo `generate` al cliente. Los tokens del título (save_message) y de generate_prompt (tools) se filtran por `metadata.langgraph_node`.
- **CORS:** Permite `*.vercel.app` via regex + orígenes explícitos.
- **Embeddings:** Google Gemini Embedding 001, dimensiones 3072, similarity search via RPC en Supabase.
