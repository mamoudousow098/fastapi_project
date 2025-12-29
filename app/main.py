from fastapi import FastAPI
from app.api.v1.api import api_router




app = FastAPI(
    title="Broker EME API",
    version="1.0.0",
    root_path="/broker-eme"
)

app.include_router(api_router, prefix="/api/v1")
