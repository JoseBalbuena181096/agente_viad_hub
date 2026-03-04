import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.graph.checkpointer import close_checkpointer
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.api.vectorize import router as vectorize_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("VIAD Bot starting...")
    yield
    # Shutdown
    await close_checkpointer()
    print("VIAD Bot shutdown complete")


app = FastAPI(
    title="VIAD Bot API",
    description="Agente conversacional experto en IA Generativa para el CEO IA Hub",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Vercel preview deployments and custom domains
_default_origins = [
    "https://ceo-ia-hub-tu7s.vercel.app",
    "http://localhost:3000",
]
_extra = os.getenv("CORS_ORIGINS", "")
if _extra:
    _default_origins.extend([o.strip() for o in _extra.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
API_PREFIX = "/api/v1"

app.include_router(health_router)
app.include_router(chat_router, prefix=API_PREFIX)
app.include_router(conversations_router, prefix=API_PREFIX)
app.include_router(vectorize_router, prefix=API_PREFIX)
