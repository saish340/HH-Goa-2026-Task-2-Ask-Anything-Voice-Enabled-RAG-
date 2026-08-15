from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import app as api_app

app = FastAPI(title="HH Goa Ask Anything")
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
