
import os
import gspread
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from src.infrastructure.agent_service import AgentOrchestrator

# Configuração do roteador do FastAPI para o módulo de documentos
router = APIRouter(prefix="/documents", tags=["Documents"])

def salvar_no_google_sheets(nome_entidade: str, detalhes: str, resumo: str):
    """
    Função para gravar automaticamente os dados no Google Sheets (CRM).
    Procura o arquivo credentials.json de forma segura na raiz ou na pasta backend.
    """
    try:
        # Descobre o diretório base do projeto automaticamente
        current_dir = os.path.dirname(os.path.abspath(__file__)) # Caminho atual: src/interfaces
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # Raiz do projeto (agentes_de_analise)
        
        # Define os caminhos possíveis para o arquivo de credenciais
        path_backend = os.path.join(project_root, "backend", "credentials.json")
        path_root = os.path.join(project_root, "credentials.json")
        
        # Verifica onde o arquivo de credenciais está localizado
        if os.path.exists(path_backend):
            cred_path = path_backend
        elif os.path.exists(path_root):
            cred_path = path_root
        else:
            # Caminho de contingência (fallback) caso o script seja executado de outro diretório
            cred_path = "credentials.json"

        # Realiza a autenticação na API do Google Sheets
        gc = gspread.service_account(filename=cred_path)
        
        # Abre a planilha de controle (CRM de Documentos)
        sh = gc.open("CRM de Documentos")
        worksheet = sh.sheet1
        
        # Prepara os dados e insere uma nova linha na planilha
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([data_atual, nome_entidade, detalhes, resumo])
        
        print("✅ Dados salvos com sucesso no Google Sheets!")
        return True
    except Exception as e:
        print(f"❌ Erro detalhado ao gravar no Google Sheets: {e}")
        return False

@router.post("/analyze")
def analyze_pdf_with_agents(
    file: UploadFile = File(...), 
    question: str = Form(...)
):
    """
    Endpoint síncrono responsável por executar os agentes de análise e persistir os resultados no Google Sheets.
    """
    try:
        # Valida se o arquivo enviado possui a extensão PDF
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")

        # Lê os bytes do arquivo enviado de forma síncrona
        file_bytes = file.file.read()
        
        # Valida se o arquivo não está vazio
        if not file_bytes:
            raise HTTPException(status_code=400, detail="O arquivo enviado está vazio.")

        # 1. Executa o fluxo de processamento e análise utilizando os agentes (CrewAI)
        analysis_result = AgentOrchestrator.run_analysis_workflow(file_bytes, question)

        # 2. Formata os resultados e realiza a gravação segura no Google Sheets
        resumo_str = str(analysis_result) if analysis_result else "Sem resumo gerado."
        
        salvar_no_google_sheets(
            nome_entidade=file.filename,
            detalhes=f"Questão: {question}",
            resumo=resumo_str
        )

        # Retorna a resposta de sucesso com os detalhes da análise
        return {
            "status": "success",
            "filename": file.filename,
            "question": question,
            "analysis_result": analysis_result
        }

    except HTTPException:
        raise  # Propaga exceções HTTP controladas (como o erro 400) mantendo o código de status original
    except Exception as e:
        # Trata quaisquer outros erros inesperados durante o processamento
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento: {str(e)}")