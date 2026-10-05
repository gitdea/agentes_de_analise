
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instância global das configurações para usar em todo o projeto
settings = Settings()