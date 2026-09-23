from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Marju Express",
    description="Sistema de controle de estoque para mercadorias (Shein, TikTok, etc.)",
    version="1.0.0"
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, pode substituir por "http://localhost:4200" ou o domínio do seu frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

from app.routers.auth_router import auth_router
from app.routers.stock_router import stock_router

app.include_router(auth_router)
app.include_router(stock_router)







# uvicorn main:app --reload
