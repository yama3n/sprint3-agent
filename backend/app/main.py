from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.auth import router as auth_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "FastAPI Backend Ready"}
