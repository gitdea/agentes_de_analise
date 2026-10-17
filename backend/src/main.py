
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.interfaces.routes import router as document_router

# ALTERAÇÃO: a descrição agora bate com o que o código faz (o CrewAI não é usado). Os "agentes" são
# três etapas de IA via Groq, e o RAG escolhe os trechos do documento por busca BM25.
app = FastAPI(
    title="Agentes de Análise API",
    description="API de análise de PDFs com agentes de IA (Groq), OCR e busca de trechos relevantes (RAG)",
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
    # ALTERAÇÃO: tirei "funcionar perfeitamente", porque esta rota só mostra que a API está no ar
    # e não verifica o banco nem a Groq.
    return {
        "status": "online",
        "project": "Agentes de Análise",
        "message": "API de análise de documentos no ar."
    }