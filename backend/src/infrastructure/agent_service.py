
import io
import re
import pypdf
import pytesseract
from pdf2image import convert_from_bytes
from groq import Groq
from src.infrastructure.config import settings
# ALTERAÇÃO (RAG) - MUDANÇA 1: importa a função que escolhe os trechos mais relevantes do documento.
# O arquivo rag.py fica na mesma pasta (src/infrastructure).
from src.infrastructure.rag import selecionar_trechos

# ALTERAÇÃO (limite do OCR): o OCR é a etapa mais lenta, porque converte cada página em imagem.
# Em PDF escaneado lemos no máximo estas páginas, para não estourar o tempo no Render gratuito.
MAX_PAGINAS_OCR = 20

# ALTERAÇÃO (limpeza do <br>) - MUDANÇA 8: mesmo com a regra "nunca use tags HTML" no prompt, o modelo às vezes
# escreve <br> dentro das células das tabelas, e na tela isso aparece como texto feio. Como o prompt
# não garante 100%, limpamos a resposta no código antes de devolvê-la.
def limpar_html(texto: str) -> str:
    """Troca <br> por um separador legível e remove outras tags HTML que o modelo possa ter escrito."""
    # <br> (e variações como <br/> ou <BR>) vira " • ". Se logo depois já vinha um marcador de lista
    # (•, - ou *), ele é absorvido, para não ficar "• •".
    texto = re.sub(r"\s*<br\s*/?>\s*(?:[•\-\*](?=\s))?\s*", " • ", texto, flags=re.IGNORECASE)
    # Remove tags de tabela, parágrafo e lista, mantendo o texto de dentro delas.
    texto = re.sub(r"</?(?:table|thead|tbody|tr|td|th|p|div|span|ul|ol|li)[^>]*>", "", texto, flags=re.IGNORECASE)
    return texto

class AgentOrchestrator:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """
        Extrai texto de um PDF. Tenta primeiro texto nativo (pypdf). 
        Se não encontrar texto (ex: documento digitalizado ou imagem), 
        executa OCR automaticamente via pdf2image e pytesseract.
        """
        text = ""
        # 1. Tenta extração de texto nativo
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            print(f"Erro ao ler PDF com pypdf: {e}")

        # 2. Se o PDF não tiver texto nativo (scans/imagens), aplica OCR
        if not text.strip():
            print("⚠️ PDF sem camada de texto nativa detetada. A iniciar OCR (Pytesseract)...")
            try:
                # Converte o PDF em imagens página por página
                # ALTERAÇÃO (limite do OCR) - MUDANÇA 4: first_page e last_page limitam quantas páginas
                # viram imagem. Sem isso, um PDF escaneado de 100 páginas travaria o servidor.
                images = convert_from_bytes(file_bytes, first_page=1, last_page=MAX_PAGINAS_OCR)
                for i, image in enumerate(images):
                    ocr_text = pytesseract.image_to_string(image, lang='por+eng')
                    text += f"\n--- Página {i+1} (OCR) ---\n" + ocr_text + "\n"
            except Exception as ocr_error:
                print(f"❌ Erro ao processar OCR com Tesseract: {ocr_error}")

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

        # Extrai o texto bruto do PDF (com suporte a OCR de retaguarda)
        raw_text = AgentOrchestrator.extract_text_from_pdf(file_bytes)
        if not raw_text.strip():
            raise Exception("Não foi possível extrair texto legível do PDF nem por OCR.")

        # ALTERAÇÃO (RAG) - MUDANÇA 2: em vez de cortar o texto nos 4000 primeiros caracteres,
        # escolhemos os trechos do documento inteiro que mais se parecem com a pergunta do usuário.
        # Documentos curtos seguem inteiros; nos longos, só os trechos mais relevantes vão para a IA.
        contexto = selecionar_trechos(raw_text, user_question)
        print(f"📚 [RAG] Texto extraído: {len(raw_text)} caracteres. Enviados aos agentes: {len(contexto)}.")

        # Inicializa o cliente da Groq e define o modelo de linguagem utilizado
        client = Groq(api_key=str(settings.GROQ_API_KEY))
        model_name = "openai/gpt-oss-120b"

        try:
            # AGENTE 1: EXTRATOR 
            print("🔍 [Agente 1: Extrator] Extraindo dados estruturados...")
            # ALTERAÇÃO (RAG) - MUDANÇA 3: o Extrator agora recebe a pergunta e os trechos relevantes
            # ({contexto}), no lugar de raw_text[:4000]. Assim ele extrai o que ajuda a responder,
            # mesmo que a informação esteja no meio ou no fim do documento.
            # ALTERAÇÃO (anti-invenção) - MUDANÇA 5: depois de ver a IA inventar multas e anexos que não
            # existiam no PDF, o prompt ganhou regras: usar só o que está nos trechos, copiar números
            # exatamente e dizer "NÃO CONSTA" quando a informação não aparecer.
            prompt_extract = f"""
            Você é um agente especialista em extração de dados. Abaixo estão TRECHOS de um documento (não o documento inteiro), selecionados por serem os mais relevantes para a pergunta do usuário. Extraia as informações que ajudem a responder à pergunta (nomes, CPFs, valores, datas, prazos, cláusulas, etc.).
            REGRAS OBRIGATÓRIAS:
            - Use SOMENTE o que está escrito nos trechos. NUNCA invente valores, percentuais, datas, nomes, cláusulas ou anexos.
            - Copie números e nomes exatamente como aparecem, citando o número da cláusula quando houver.
            - Se a informação pedida não aparecer nos trechos, escreva: NÃO CONSTA NOS TRECHOS ANALISADOS.
            Pergunta do usuário: '{user_question}'
            ---
            {contexto}
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
            print("🛡 [Agente 2: Validador] Auditando e verificando a consistência...")
            # ALTERAÇÃO (anti-invenção) - MUDANÇA 6: o Validador agora também recebe os trechos originais.
            # Antes ele só via a saída do Extrator e não tinha como detectar um dado inventado. Agora ele
            # confere cada dado contra o texto e remove o que não estiver escrito nos trechos.
            prompt_validate = f"""
            Você é um agente auditor rigoroso. Abaixo estão os TRECHOS originais do documento e os dados que o Agente 1 extraiu deles. Confira cada dado extraído contra os trechos.
            REGRAS OBRIGATÓRIAS:
            - Mantenha apenas os dados que aparecem nos trechos. Remova qualquer valor, percentual, cláusula ou anexo que não esteja escrito neles.
            - Você viu apenas trechos, e não o documento inteiro: NUNCA conclua que algo não existe no documento. Diga apenas que não consta nos trechos analisados.
            - Prepare um resumo validado, sem acrescentar informações novas.
            TRECHOS ORIGINAIS:
            ---
            {contexto}
            ---
            DADOS EXTRAÍDOS PELO AGENTE 1:
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
            # ALTERAÇÃO (anti-invenção) - MUDANÇA 7: o Analista só pode usar os dados validados e
            # não pode afirmar que algo "não existe no documento", porque ele nunca vê o documento inteiro.
            prompt_answer = f"""
            Você é um assistente executivo sênior. Com base nos dados já auditados e validados abaixo, responda de forma direta, limpa e estruturada à seguinte pergunta do usuário: '{user_question}'
            
            REGRAS DE FORMATAÇÃO OBRIGATÓRIAS:
            - NUNCA use tags HTML como <table>, <tr>, <td>, <br> ou semelhantes.
            - Utilize EXCLUSIVAMENTE a sintaxe de tabelas nativa do Markdown (usando barras verticais |).
            - Use listas com asteriscos (*) para os pontos críticos e recomendações.

            REGRAS DE CONTEÚDO OBRIGATÓRIAS:
            - Baseie-se SOMENTE nos dados validados. Não invente informações e não acrescente observações ou recomendações que não estejam neles.
            - Os dados vêm de trechos selecionados do documento, não do documento completo. Nunca afirme que o documento não contém algo; diga que não encontrou nos trechos analisados.
            ---
            {validated_data}
            ---
            """
            res_answer = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt_answer}],
                temperature=0.1
            )
            # ALTERAÇÃO (limpeza do <br>): passa a resposta pela limpeza antes de salvar e devolver.
            final_answer = limpar_html(res_answer.choices[0].message.content)
            print("✅ [Agente 3: Analista] Resposta final gerada com sucesso!")
            print("==============================================\n")

            return str(final_answer)

        except Exception as e:
            print(f"❌ ERRO NO FLUXO DE AGENTES: {str(e)}")
            raise Exception(f"Erro na comunicação com a API da Groq: {str(e)}")