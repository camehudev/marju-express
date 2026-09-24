import httpx
import numpy as np
import cv2
from fastapi import APIRouter, File, HTTPException, UploadFile

stock_router = APIRouter(
    prefix="/stock",
    tags=["stock"],
    responses={404: {"description": "Not found"}}
)

# URL do Webhook do seu n8n
N8N_WEBHOOK_URL = "https://pessoal-n8n-start.sjj3wv.easypanel.host/webhook/84ed9913-5511-42a1-b4df-79997f7a4def"

@stock_router.post("/scan-image")
async def scan_image(file: UploadFile = File(...)):
    try:
        # Lê os bytes da imagem enviada pelo app mobile
        contents = await file.read()
        
        # (Opcional) Validação rápida com OpenCV para garantir que é uma imagem válida
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Arquivo de imagem inválido.")

        # Repassa a imagem para o n8n via HTTP POST de forma assíncrona
        async with httpx.AsyncClient() as client:
            files = {"file": (file.filename, contents, file.content_type)}
            response = await client.post(N8N_WEBHOOK_URL, files=files, timeout=30.0)
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Erro ao comunicar com o fluxo do n8n.")
            
            # Pega a resposta que o n8n processou (ex: com o Gemini) e devolve para o app
            dados_n8n = response.json()

        return {
            "success": True,
            "message": "Processado com sucesso via FastAPI + n8n",
            "resultado": dados_n8n
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")