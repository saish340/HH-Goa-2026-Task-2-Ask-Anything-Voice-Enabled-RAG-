from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import app as api_app
from backend.app.harness.orchestrator import warmup


@asynccontextmanager
async def lifespan(_: FastAPI):
    # uvicorn serves the OUTER app, so startup warmup must live here — the
    # on_event startup registered on the mounted sub-app (routes.py) is not
    # invoked, which otherwise makes the very first /api/ask pay the full
    # model+index cold start (~80s). warmup() is idempotent and cheap when
    # artifacts are missing (demo mode).
    try:
        warmup()
    except Exception as exc:  # never block serving on warmup failure
        import logging

        logging.getLogger(__name__).warning("Startup warmup failed: %s", exc)
    yield


app = FastAPI(title="HH Goa Ask Anything", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/api", api_app)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "HH Goa Ask Anything backend is running."}