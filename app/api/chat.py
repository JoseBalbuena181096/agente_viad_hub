import json
import base64
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage

from app.schemas.chat import ChatRequest
from app.graph.checkpointer import get_checkpointer
from app.graph.builder import build_graph
from app.services.supabase import get_supabase
from app.services.llm import safe_text

router = APIRouter(tags=["chat"])


def _process_files(files) -> tuple[list, str | None]:
    """Process file attachments into multimodal content and text context."""
    multimodal_parts = []
    text_context_parts = []

    if not files:
        return multimodal_parts, None

    for f in files:
        mime = f.mime_type.lower()

        if mime.startswith("image/"):
            # Images go directly to Gemini as multimodal content
            multimodal_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{f.mime_type};base64,{f.data}"},
            })

        elif mime == "application/pdf":
            # Extract text from PDF
            try:
                import pdfplumber
                import io
                pdf_bytes = base64.b64decode(f.data)
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    text = "\n".join(
                        page.extract_text() or "" for page in pdf.pages
                    )
                if text.strip():
                    text_context_parts.append(
                        f"[Archivo PDF: {f.filename}]\n{text[:5000]}"
                    )
            except Exception as e:
                text_context_parts.append(
                    f"[Error al procesar PDF {f.filename}: {e}]"
                )

        else:
            # Code/text files
            try:
                decoded = base64.b64decode(f.data).decode("utf-8", errors="replace")
                text_context_parts.append(
                    f"[Archivo: {f.filename}]\n```\n{decoded[:3000]}\n```"
                )
            except Exception:
                pass

    file_context = "\n\n".join(text_context_parts) if text_context_parts else None
    return multimodal_parts, file_context


@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with SSE streaming."""

    try:
        # Ensure conversation exists
        conversation_id = request.conversation_id
        supabase = get_supabase()

        if not conversation_id:
            # Create new conversation
            conv_response = supabase.table("conversations").insert({
                "user_id": request.user_id,
                "title": "Nueva conversación",
            }).execute()
            conversation_id = conv_response.data[0]["id"]

        # Process file attachments
        multimodal_parts, file_context = _process_files(request.files)

        # Build the human message
        if multimodal_parts:
            # Multimodal message (text + images)
            content = [{"type": "text", "text": request.query}] + multimodal_parts
            human_message = HumanMessage(content=content)
        else:
            human_message = HumanMessage(content=request.query)

        # Build and run graph
        checkpointer = await get_checkpointer()
        graph = build_graph(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": conversation_id}}

        input_state = {
            "messages": [human_message],
            "user_id": request.user_id,
            "conversation_id": conversation_id,
            "file_context": file_context,
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Error initializing chat: {error_msg}")
        async def error_generator(msg=error_msg):
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Error al iniciar chat: {msg}"}),
            }
            yield {"event": "done", "data": "{}"}
        return EventSourceResponse(error_generator())

    async def event_generator():
        # Send conversation_id immediately (useful when auto-created)
        print(f"[STREAM] Starting for conversation {conversation_id}")
        yield {
            "event": "metadata",
            "data": json.dumps({"conversation_id": conversation_id}),
        }

        try:
            token_count = 0
            async for event in graph.astream_events(
                input_state,
                config=config,
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    # Only stream tokens from the "generate" node
                    # Skip tokens from save_message (title gen) and tools (generate_prompt)
                    node = event.get("metadata", {}).get("langgraph_node")
                    if node != "generate":
                        continue
                    chunk = event["data"].get("chunk")
                    if chunk and chunk.content:
                        text = safe_text(chunk.content)
                        if text:
                            token_count += 1
                            yield {
                                "event": "token",
                                "data": json.dumps({"content": text}),
                            }

                elif kind == "on_tool_start":
                    print(f"[STREAM] Tool call: {event.get('name', '')}")
                    yield {
                        "event": "tool_call",
                        "data": json.dumps({
                            "tool": event.get("name", ""),
                            "args": event.get("data", {}).get("input", {}),
                        }),
                    }

                elif kind == "on_tool_end":
                    output = event.get("data", {}).get("output", "")
                    print(f"[STREAM] Tool result: {event.get('name', '')}")
                    yield {
                        "event": "tool_result",
                        "data": json.dumps({
                            "tool": event.get("name", ""),
                            "result": str(output)[:500],
                        }),
                    }

            print(f"[STREAM] Completed. Tokens sent: {token_count}")

        except Exception as e:
            print(f"[STREAM] Error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())
