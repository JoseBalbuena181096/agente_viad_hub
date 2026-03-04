# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VIAD Bot** — Conversational AI agent backend for the VIAD HUB platform of Consorcio Educativo de Oriente (CEO). Built with FastAPI + LangGraph + Google Gemini 3 Flash Preview. Provides SSE-streamed chat responses, RAG-based library/video search, and prompt generation. All responses are in **Spanish**.

**Production:** https://web-production-ccc6a.up.railway.app
**Frontend:** https://ceo-ia-hub-tu7s.vercel.app (repo: ceo_ia_hub)

## Commands

- `uvicorn main:app --reload --port 8000` — Start dev server
- `pip install -r requirements.txt` — Install dependencies

No test scripts configured.

## Tech Stack

- **FastAPI 0.128.3** — ASGI web framework
- **LangGraph 1.0.9** — Agent orchestration (StateGraph with conditional edges)
- **LangChain 1.2.10** + **langchain-google-genai 4.2.1** — LLM integration
- **Google Gemini 3 Flash Preview** — LLM (temperature=1.0, streaming, convert_system_message_to_human=True)
- **Google Gemini Embedding 001** — Embeddings (3072 dimensions)
- **Supabase 2.27.3** — Database via REST API (not direct PostgreSQL from Railway due to IPv4/IPv6 incompatibility)
- **sse-starlette 2.2.1** — Server-Sent Events streaming
- **Uvicorn** — ASGI server (1 worker for MemorySaver consistency)
- **pdfplumber** — PDF text extraction for file attachments
- **Pillow** — Image processing

## Architecture

### LangGraph Agent Flow

```
setup → generate → [tools_condition] → tools → generate (loop)
                                     → save_message → END
```

- **setup** (`app/graph/nodes/setup.py`) — Loads user profile (name, department) from Supabase. Processes file attachments (PDF text, images).
- **generate** (`app/graph/nodes/generate.py`) — Main LLM node. Uses system prompt + tools. Bound tools: `search_library`, `search_videos`, `generate_prompt`.
- **tools** — LangGraph `ToolNode` that executes the called tools.
- **save_message** (`app/graph/nodes/save_message.py`) — Persists user + AI messages to Supabase `messages` table. Auto-generates conversation title on first message.

### State

`AgentState` (`app/core/state.py`) — TypedDict with:
- `messages` — LangChain message list (managed by LangGraph)
- `user_id`, `conversation_id` — Identifiers
- `user_name`, `user_department` — From profiles table
- `is_first_message` — For greeting/title logic
- `file_context` — Extracted text from attachments

### Checkpointer

`app/graph/checkpointer.py` — Uses `MemorySaver` (in-memory). Messages are separately persisted to Supabase via REST API in the `save_message` node, so conversation history survives restarts (loaded from `messages` table).

**Why not PostgresSaver:** Supabase Session Pooler has SSL connection issues from Railway's network. The pooler's circuit breaker activates after failed connection attempts. MemorySaver with REST API persistence is the working solution.

### Tools

- `search_library` (`app/tools/search_library.py`) — RAG similarity search on prompt embeddings. Returns top 3 results with title, category, content, similarity score.
- `search_videos` (`app/tools/search_videos.py`) — RAG similarity search on video embeddings. Returns top 3 results with title, category, URL, similarity score.
- `generate_prompt` (`app/tools/generate_prompt.py`) — Generates a professional prompt using Gemini. Takes task_description, target_tool, department.

### Services

- `app/services/llm.py` — Singleton LLM and embeddings instances. `safe_text()` handles Gemini's list-of-blocks content format.
- `app/services/supabase.py` — Supabase REST client using service role key.
- `app/services/rag.py` — Similarity search via Supabase RPC (`match_prompt_embeddings`, `match_video_embeddings`).
- `app/services/embeddings.py` — Generates embeddings using Gemini Embedding 001.
- `app/services/vectorize.py` — Batch vectorization of prompts and videos.

### SSE Streaming

`app/api/chat.py` — Uses `astream_events(version="v2")`. **Critical:** Only tokens from the `generate` node are streamed to the client. Tokens from `save_message` (title generation) and tools (`generate_prompt`) are filtered out by checking `event.metadata.langgraph_node`.

Events emitted: `metadata`, `token`, `tool_call`, `tool_result`, `error`, `done`.

### System Prompt

`app/core/prompts.py` — Contains:
- `VIAD_BOT_SYSTEM_PROMPT` — Full agent personality, interaction rules, response formats, CEO institutional knowledge, tool usage rules, and anti-duplication rules. Uses `{user_name}` and `{user_department}` placeholders.
- `TITLE_GENERATOR_PROMPT` — Generates short (≤50 chars) conversation titles.

## API Routes

All chat/conversation routes are prefixed with `/api/v1`. Health check has no prefix.

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/chat` | SSE streaming chat |
| GET | `/api/v1/conversations` | List user conversations |
| GET | `/api/v1/conversations/{id}/messages` | Get conversation messages |
| POST | `/api/v1/conversations` | Create conversation |
| PATCH | `/api/v1/conversations/{id}` | Update title |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation (cascade) |
| POST | `/api/v1/vectorize/batch` | Vectorize all prompts and videos |

## CORS Configuration

- Explicit origins: `ceo-ia-hub-tu7s.vercel.app`, `localhost:3000`
- Regex: `https://.*\.vercel\.app` (all Vercel preview deployments)
- Extra origins via `CORS_ORIGINS` env var (comma-separated)

## Deployment (Railway)

- **Builder:** Nixpacks
- **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
- **Health check:** `/health` (30s timeout)
- **Restart:** ON_FAILURE, max 5 retries
- **Auto-deploy:** Push to `main` branch

### Environment Variables

Required:
- `GOOGLE_API_KEY` — Google AI API key (for Gemini)
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key (bypasses RLS)

Optional:
- `SUPABASE_DB_URL` — Direct PostgreSQL URL (unused currently, for future PostgresSaver)
- `CORS_ORIGINS` — Additional allowed origins (comma-separated)

## Key Technical Notes

- **Gemini 3 Flash Preview** requires `temperature=1.0` and `convert_system_message_to_human=True`. Content is returned as `list[dict]` not `str` — always use `safe_text()`.
- **1 worker only** — MemorySaver is per-process. Multiple workers would cause conversation context loss between requests.
- **sse-starlette** uses `\r\n` line endings — frontend must normalize to `\n` before parsing SSE blocks.
- **Supabase connection** is REST-only from Railway. Direct PostgreSQL connection fails due to IPv4/IPv6 + SSL + circuit breaker issues with Supabase Session Pooler.
- **Embeddings** are 3072-dimensional vectors (Gemini Embedding 001). Stored in `prompt_embeddings` and `video_embeddings` tables with `VECTOR(3072)` columns.
