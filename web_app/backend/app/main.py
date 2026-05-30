"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web_app.backend.app.database import close_db
from web_app.backend.app.services.cache_service import close_redis
from web_app.backend.app.services.rag_service import rag_service
from web_app.backend.app.routes import chat, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('[INIT] RAG Service...')
    await rag_service.initialize()
    yield
    print('[SHUTDOWN] Cleaning up...')
    await close_db()
    await close_redis()


app = FastAPI(title='RAG API', version='2.0.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:19123'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(chat.router)
app.include_router(admin.router)


@app.get('/api/health')
async def health():
    return {'status': 'ok', 'service': 'rag-api'}
