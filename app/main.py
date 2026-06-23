from fastapi import FastAPI
from app.routers import pedidos
from app.database import connect_db, close_db

app = FastAPI(title="API de Pedidos", version="1.0.0")

app.include_router(pedidos.router)

@app.on_event("startup")
async def startup():
    await connect_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db()

@app.get("/health")
async def health():
    return {"status": "ok"}
