import cv2
import numpy as np
import pytesseract
from fastapi import APIRouter, File, HTTPException, UploadFile
from pyzbar.pyzbar import decode
import re

stock_router = APIRouter(
    prefix="/stock",
    tags=["stock"],
    responses={404: {"description": "Not found"}}
)

def extrair_destinatario(linhas):
    destinatario = "Não identificado"
    
    for i, linha in enumerate(linhas):
        linha_upper = linha.upper()
        
        # Procura se a linha contém algo parecido com destinatario ou recebedor
        if "DEST" in linha_upper or "RECEB" in linha_upper or "CLIENTE" in linha_upper:
            # Vamos olhar as próximas 3 linhas para achar o nome
            for j in range(1, 4):
                if i + j < len(linhas):
                    candidato = linhas[i + j].strip()
                    
                    # Remove caracteres estranhos, números isolados e pontuações do Tesseract
                    candidato_limpo = re.sub(r'[^A-ZÀ-Ú\s]', '', candidato).strip()
                    
                    # Se a linha limpa tiver tamanho razoável para um nome (mais de 6 letras)
                    if len(candidato_limpo) > 6:
                        # Ignora se por acaso pegou palavras repetidas de endereço
                        if not any(termo in candidato_limpo for termo in ["RUA", "AVENIDA", "BAIRRO", "CEP", "SP", "MG", "RJ"]):
                            destinatario = candidato_limpo
                            return destinatario
                            
    # Fallback: Se não achou a palavra "destinatario", procura a primeira linha que pareça um nome completo (duas ou mais palavras maiúsculas)
    for linha in linhas:
        linha_limpa = re.sub(r'[^A-ZÀ-Ú\s]', '', linha).strip()
        partes = linha_limpa.split()
        if len(partes) >= 2 and len(linha_limpa) > 8:
            if not any(termo in linha_limpa for termo in ["RUA", "AVENIDA", "BAIRRO", "CEP", "DESTINATARIO", "REMETENTE"]):
                return linha_limpa

    return destinatario


@stock_router.post("/scan-image")
async def scan_image(file: UploadFile = File(...)):
    try:
        # Lê os bytes do arquivo enviado pelo Angular
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Não foi possível processar a imagem enviada.")
        
        # 1. Converter para tons de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. Leitura do ID pelo código de barras
        decoded_objects = decode(gray)
        id_etiqueta = "N/A"
        
        if decoded_objects:
            id_etiqueta = decoded_objects[0].data.decode("utf-8")
        
        # 3. Tratamento de imagem para otimizar o OCR (Bilateral Filter + Otsu)
        blur = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 4. OCR com Tesseract (Focado em blocos de texto)
        custom_config = r'--oem 3 --psm 6'
        texto_extraido = pytesseract.image_to_string(thresh, lang='por', config=custom_config)
        
        # Separa o texto em linhas limpas
        linhas = [linha.strip() for linha in texto_extraido.split('\n') if linha.strip()]

        # Dicionário para armazenar o endereço organizado
        endereco_organizado = {
            "destinatario": extrair_destinatario(linhas), # <--- CHAMADA CORRETA AQUI
            "rua": "Não identificado",
            "bairro": "Não identificado",
            "cidade_uf": "Não identificado",
            "cep": "Não identificado"
        }

        # Expressão regular para encontrar CEP (ex: 37470-000 ou 37470000)
        padrao_cep = re.compile(r'\b\d{5}-?\d{3}\b')
        
        # Expressão regular para encontrar Cidade/UF (ex: São Lourenço/MG ou Extrema/MG)
        padrao_cidade_uf = re.compile(r'([A-ZÀ-Úa-zà-ú\s]+)\s*[/]\s*([A-Z]{2})')

        for i, linha in enumerate(linhas):
            linha_upper = linha.upper()

            # 1. Tenta capturar o CEP
            match_cep = padrao_cep.search(linha)
            if match_cep and endereco_organizado["cep"] == "Não identificado":
                endereco_organizado["cep"] = match_cep.group(0)
                match_cid = padrao_cidade_uf.search(linha)
                if match_cid:
                    endereco_organizado["cidade_uf"] = match_cid.group(0)

            # 3. Tenta capturar a Rua/Avenida com base em termos comuns
            if any(termo in linha_upper for termo in ["AVENIDA", "RUA", "ALAMEDA", "RODOVIA", "TRAVESSA", "PQ", "PARTE"]):
                if "DESTINATARIO" not in linha_upper and "REMETENTE" not in linha_upper:
                    endereco_organizado["rua"] = linha

        # Caso a cidade/uf não tenha sido pega na mesma linha do CEP, varre procurando o formato Cidade/UF
        if endereco_organizado["cidade_uf"] == "Não identificado":
            for linha in linhas:
                match_cid = padrao_cidade_uf.search(linha)
                if match_cid:
                    endereco_organizado["cidade_uf"] = match_cid.group(0)
                    break

        return {
            "success": True,
            "id": id_etiqueta,
            "endereco_organizado": endereco_organizado,
            "texto_bruto": linhas
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")