
import io
import os
import json
import gspread
import pypdf
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from src.infrastructure.agent_service import AgentOrchestrator
from src.infrastructure.database import SessionLocal, AnaliseModel, init_db

# ALTERAÇÃO (limites da demonstração): como o link é público, qualquer pessoa pode enviar
# um PDF enorme. Estes limites protegem o servidor gratuito do Render e a cota da Groq.
MAX_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_PAGINAS = 100              # páginas do PDF

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

        # ALTERAÇÃO: lê no máximo MAX_BYTES + 1 bytes. Assim, um arquivo gigante não é carregado
        # inteiro na memória só para descobrirmos depois que era grande demais.
        file_bytes = file.file.read(MAX_BYTES + 1)

        if not file_bytes:
            raise HTTPException(status_code=400, detail="O ficheiro enviado está vazio.")

        # ALTERAÇÃO: se leu mais que o limite, o arquivo passa de 10 MB.
        # O código 413 significa "conteúdo grande demais".
        if len(file_bytes) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="O arquivo passa de 10 MB, o limite da demonstração.")

        # ALTERAÇÃO: conta as páginas antes de gastar tempo com OCR e IA. Se o PDF estiver
        # corrompido ou protegido por senha, o pypdf dá erro e devolvemos 400 com mensagem clara.
        try:
            total_paginas = len(pypdf.PdfReader(io.BytesIO(file_bytes)).pages)
        except Exception:
            raise HTTPException(status_code=400, detail="Não foi possível ler o PDF. Ele pode estar corrompido ou protegido por senha.")

        if total_paginas > MAX_PAGINAS:
            raise HTTPException(status_code=413, detail=f"O PDF tem {total_paginas} páginas. O limite da demonstração é {MAX_PAGINAS}.")

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
