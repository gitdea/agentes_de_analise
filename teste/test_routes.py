
import sys
import os

# Adiciona a pasta backend ao caminho do Python para permitir a importação do módulo 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

import pytest
from fastapi.testclient import TestClient
from src.main import app

# Inicializa o cliente de testes da aplicação FastAPI
client = TestClient(app)

def test_analyze_endpoint_invalid_file_type():
    """
    Testa se o endpoint rejeita corretamente arquivos que não possuem o formato PDF.
    """
    response = client.post(
        "/documents/analyze",
        files={"file": ("teste.txt", b"conteudo de teste", "text/plain")},
        data={"question": "Qual é o resumo?"}
    )
    
    # Valida se o código de status retornado é 400 (Bad Request) e a mensagem de erro esperada
    assert response.status_code == 400
    assert "Apenas arquivos PDF são permitidos" in response.json()["detail"]

def test_analyze_endpoint_missing_question():
    """
    Testa se o endpoint valida e rejeita a ausência obrigatória do campo 'question'.
    """
    response = client.post(
        "/documents/analyze",
        files={"file": ("documento.pdf", b"%PDF-1.4 mock content", "application/pdf")}
    )
    
    # Valida se o FastAPI retorna o código 422 (Unprocessable Entity) devido à falta do campo obrigatório
    assert response.status_code == 422