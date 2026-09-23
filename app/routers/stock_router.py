import cv2
import numpy as np
import pytesseract
from fastapi import APIRouter, File, HTTPException, UploadFile
from pyzbar.pyzbar import decode

stock_router = APIRouter(
    prefix="/stock",
    tags=["stock"],
    responses={404: {"description": "Not found"}}
)

@stock_router.get("/")
async def listar_estoque():
    return {"status": 200, "mensagem": "Bem-vindo ao Marju Express API! 🚀"}

@stock_router.post("/scan-image")
async def scan_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Não foi possível processar a imagem enviada.")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Leitura do Código de Barras (ID)
        decoded_objects = decode(gray)
        id_etiqueta = "N/A"
        if decoded_objects:
            id_etiqueta = decoded_objects[0].data.decode("utf-8")
        else:
            return {"success": False, "message": "Nenhum código de barras encontrado na etiqueta."}
        
        # 2. Tratamento para OCR
        blur = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Extrai o texto linha por linha para facilitar a filtragem
        texto_extraido = pytesseract.image_to_string(thresh, lang='por', config='--oem 3 --psm 6')
        linhas = [linha.strip() for linha in texto_extraido.split('\n') if linha.strip()]
        
        # 3. Filtragem Inteligente (Focando em Destinatário e Remetente)
        destinatario_encontrado = "Não identificado"
        remetente_encontrado = "Não identificado"
        
        # Varre as linhas procurando palavras-chave características de etiquetas
        for i, linha in enumerate(linhas):
            linha_upper = linha.upper()
            
            # Tenta capturar o remetente com base em termos comuns
            if "REMETENTE" in linha_upper or "FORNECEDOR" in linha_upper or "ULTRA" in linha_upper or "INTENSE" in linha_upper:
                if i + 1 < len(linhas):
                    remetente_encontrado = linhas[i+1]
            
            # Tenta capturar o destinatário (geralmente vem após o nome ou em maiúsculas destacadas)
            if "DESTINATARIO" in linha_upper or "RECEBEDOR" in linha_upper:
                if i + 1 < len(linhas):
                    destinatario_encontrado = linhas[i+1]

        return {
            "success": True,
            "id": id_etiqueta,
            "dados_extraidos": {
                "destinatario": destinatario_encontrado,
                "remetente": remetente_encontrado
            },
            "linhas_brutas_encontradas": linhas # Mantido para você ajustar os filtros se necessário
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")