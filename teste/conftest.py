
import os

# Define uma chave de API fictícia para o Pydantic não dar erro de validação nos testes
os.environ.setdefault("GROQ_API_KEY", "gsk_test_mock_api_key_for_pytest_12345")