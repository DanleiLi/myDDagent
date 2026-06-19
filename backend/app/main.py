import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.analysis import router as analysis_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.gaps import router as gaps_router
from app.api.projects import router as projects_router
from app.api.reports import router as reports_router
from app.api.schema import router as schema_router
from app.api.template import router as template_router
import uvicorn

# psycopg3 async requires SelectorEventLoop on Windows (not ProactorEventLoop)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    yield
    # Shutdown


app = FastAPI(title="Dossier", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(projects_router)
app.include_router(schema_router)
app.include_router(documents_router)
app.include_router(gaps_router)
app.include_router(chat_router)
app.include_router(template_router)
app.include_router(analysis_router)
app.include_router(reports_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
