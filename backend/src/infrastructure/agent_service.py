
import io
import pypdf
from groq import Groq
from src.infrastructure.config import settings

class AgentOrchestrator:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """
        Método estático responsável por extrair todo o texto legível de um arquivo PDF
        a partir de seus bytes, utilizando a biblioteca pypdf.
        """
        text = ""
        try:
            # Lê o conteúdo binário do PDF em memória
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            # Itera por todas as páginas do documento acumulando o texto extraído
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            print(f"Erro ao ler PDF com pypdf: {e}")
        return text

    @staticmethod
    def run_analysis_workflow(file_bytes: bytes, user_question: str) -> str:
        """
        Método responsável por executar o fluxo completo de análise multiagente,
        envolvendo extração, validação e geração da resposta final por inteligência artificial.
        """
        print("\n==============================================")
        print("🤖 [ORQUESTRADOR] Iniciando fluxo multiagente...")
        print("==============================================")

        # Extrai o texto bruto do PDF enviado
        raw_text = AgentOrchestrator.extract_text_from_pdf(file_bytes)
        if not raw_text.strip():
            raise Exception("Não foi possível extrair texto legível do PDF.")

        # Inicializa o cliente da Groq e define o modelo de linguagem utilizado
        client = Groq(api_key=str(settings.GROQ_API_KEY))
        model_name = "openai/gpt-oss-120b"

        try:
            # AGENTE 1: EXTRATOR 
            print("🔍 [Agente 1: Extrator] Extraindo dados estruturados...")
            prompt_extract = f"""
            Você é um agente especialista em extração de dados. Analise o documento abaixo e extraia de forma limpa todas as informações estruturadas relevantes (nomes, CPFs, valores, datas, etc.):
            ---
            {raw_text[:4000]}
            ---
            """
            res_extract = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt_extract}],
                temperature=0.1
            )
            extracted_data = res_extract.choices[0].message.content
            print("✅ [Agente 1: Extrator] Concluído!")

            # AGENTE 2: VALIDADOR / AUDITOR 
            print("🛡️️ [Agente 2: Validador] Auditando e verificando a consistência...")
            prompt_validate = f"""
            Você é um agente auditor rigoroso. Revise os dados extraídos abaixo pelo Agente 1, verifique se há inconsistências ou dados em falta, e prepare um resumo validado:
            ---
            {extracted_data}
            ---
            """
            res_validate = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt_validate}],
                temperature=0.1
            )
            validated_data = res_validate.choices[0].message.content
            print("✅ [Agente 2: Validador] Concluído!")

            # AGENTE 3: ANALISTA / RESPOSTA FINAL
            print("💡 [Agente 3: Analista] Redigindo a resposta final formatada...")
            prompt_answer = f"""
            Você é um assistente executivo sênior. Com base nos dados já auditados e validados abaixo, responda de forma direta, limpa e estruturada à seguinte pergunta do usuário: '{user_question}'
            
            REGRAS DE FORMATAÇÃO OBRIGATÓRIAS:
            - NUNCA use tags HTML como <table>, <tr>, <td>, <br> ou semelhantes.
            - Utilize EXCLUSIVAMENTE a sintaxe de tabelas nativa do Markdown (usando barras verticais |).
            - Use listas com asteriscos (*) para os pontos críticos e recomendações.
            ---
            {validated_data}
            ---
            """
            res_answer = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt_answer}],
                temperature=0.1
            )
            final_answer = res_answer.choices[0].message.content
            print("✅ [Agente 3: Analista] Resposta final gerada com sucesso!")
            print("==============================================\n")

            return str(final_answer)

        except Exception as e:
            print(f"❌ ERRO NO FLUXO DE AGENTES: {str(e)}")
            raise Exception(f"Erro na comunicação com a API da Groq: {str(e)}")