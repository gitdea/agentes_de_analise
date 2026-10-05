
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.interfaces.routes import router as document_router

app = FastAPI(
    title="Agentes de Análise API",
    description="API de multi-agentes (CrewAI + OCR) para análise inteligente de PDFs",
    version="1.0.0"
)

# Configurar CORS para permitir ligações do frontend (Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registar as rotas da aplicação
app.include_router(document_router)

@app.get("/")
def root():
    return {
        "status": "online",
        "project": "Agentes de Análise",
        "message": "API de multi-agentes a funcionar perfeitamente!"
    }