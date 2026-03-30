from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import auth, data
from utils.mongodb import init_mongo

app = FastAPI(title="Work Intelligence Hub API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_mongo()


app.include_router(auth.router)
app.include_router(data.router)


@app.get("/")
def root():
    return {"message": "Work Intelligence Hub FastAPI backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    from utils.mongodb import mongo_client

    if mongo_client is None:
        return {"status": "db_unavailable"}
    try:
        mongo_client.admin.command("ping")
        return {"status": "db_available"}
    except Exception as exc:
        return {"status": "db_unavailable", "error": str(exc)}

