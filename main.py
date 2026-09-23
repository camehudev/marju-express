from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Marju Express",
    description="Sistema de controle de estoque para mercadorias (Shein, TikTok, etc.)",
    version="1.0.0"
)

from app.routers.auth_router import auth_router
from app.routers.stock_router import stock_router

app.include_router(auth_router)
app.include_router(stock_router)







# uvicorn main:app --reload
