from fastapi import FastAPI
import uvicorn

app = FastAPI()


app = FastAPI(
    title="Marju Express",
    description="Sistema de controle de estoque para mercadorias (Shein, TikTok, etc.)",
    version="1.0.0"
)

@app.get("/")
def ler_raiz():
    return {"mensagem": " Hellow Word! Bem-vindo ao Marju Express API! 🚀"}


# uvicorn main:app --reload
