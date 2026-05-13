import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import cluster, ingest, namespaces, recommendations, workloads
from storage.database import SessionLocal, init_db

app = FastAPI(
    title="KubeWise API",
    description=(
        "KubeWise — Kubernetes cost and performance optimization platform. "
        "Advisory-only: no changes are ever auto-applied to your cluster."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*")
_origins = ["*"] if ALLOWED_ORIGINS == "*" else ALLOWED_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cluster.router)
app.include_router(namespaces.router)
app.include_router(workloads.router)
app.include_router(recommendations.router)
app.include_router(ingest.router)


@app.on_event("startup")
def on_startup():
    init_db()
    if os.getenv("SEED_DEMO_DATA", "true").lower() == "true":
        from storage.seed import seed
        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "kubewise-api"}


@app.get("/", tags=["health"])
def root():
    return {
        "service": "KubeWise API",
        "version": "0.1.0",
        "docs": "/docs",
        "advisory_only": True,
    }
