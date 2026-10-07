
import os
import json
import gspread
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from src.infrastructure.agent_service import AgentOrchestrator
from src.infrastructure.database import SessionLocal, AnaliseModel, init_db

router = APIRouter(prefix="/documents", tags=["Documents"])

# Inicializar a tabela na base de dados ao arrancar (se não existir)
try:
    init_db()
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível inicializar a base de dados: {e}")

def salvar_no_neon(nome_ficheiro: str, questao: str, resumo: str):
    """
    Grava os dados da análise na base de dados PostgreSQL (Neon) ou SQLite local.
    """
    db = SessionLocal()
    try:
        nova_analise = AnaliseModel(
            nome_ficheiro=nome_ficheiro,
            questao=questao,
            resumo_agente=resumo
        )
        db.add(nova_analise)
        db.commit()
        db.refresh(nova_analise)
        print("✅ Dados guardados com sucesso na Base de Dados!")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao guardar na Base de Dados: {e}")
        return False
    finally:
        db.close()

def salvar_no_google_sheets(nome_entidade: str, detalhes: str, resumo: str):
    """
    Função para gravar automaticamente os dados no Google Sheets (CRM).
    Lê o ficheiro secreto do Render ou o ficheiro local de desenvolvimento.
    """
    try:
        render_secret_path = "/etc/secrets/credentials.json"
        local_path = "credentials.json"
        
        if os.path.exists(render_secret_path):
            cred_path = render_secret_path
        elif os.path.exists(local_path):
            cred_path = local_path
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            path_backend = os.path.join(project_root, "backend", "credentials.json")
            cred_path = path_backend if os.path.exists(path_backend) else "credentials.json"

        gc = gspread.service_account(filename=cred_path)
        sh = gc.open("CRM de Documentos")
        worksheet = sh.sheet1
        
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([data_atual, nome_entidade, detalhes, resumo])
        
        print("✅ Dados guardados com sucesso no Google Sheets!")
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
    Endpoint síncrono que executa os agentes, persiste na Base de Dados e no Google Sheets.
    """
    try:
        if not file.filename.lower().endswith(".pdf"):
           raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")
        file_bytes = file.file.read()
        
        if not file_bytes:
            raise HTTPException(status_code=400, detail="O ficheiro enviado está vazio.")

        analysis_result = AgentOrchestrator.run_analysis_workflow(file_bytes, question)

        resumo_str = str(analysis_result) if analysis_result else "Sem resumo gerado."
        
        # 2. Persistência Dupla: Base de Dados + Google Sheets (CRM)
        salvar_no_neon(
            nome_ficheiro=file.filename,
            questao=question,
            resumo=resumo_str
        )
        
        salvar_no_google_sheets(
            nome_entidade=file.filename,
            detalhes=f"Questão: {question}",
            resumo=resumo_str
        )

        return {
            "status": "success",
            "filename": file.filename,
            "question": question,
            "analysis_result": analysis_result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento: {str(e)}")
