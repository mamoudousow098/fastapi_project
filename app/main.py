from fastapi import FastAPI
from app.api.v1.api import api_router



#app = FastAPI(title="FastAPI REST API")


app = FastAPI(
    title="Broker EME API",
    version="1.0.0",
    root_path="/broker-eme"   # ✅ CONTEXT PATH
)

app.include_router(api_router, prefix="/api/v1")


#app.include_router(api_router, prefix="/api/v1")
