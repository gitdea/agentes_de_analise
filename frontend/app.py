
import streamlit as st
import requests
import time
import os

# ALTERAÇÃO (limites): estes valores precisam ser iguais aos da API (MAX_BYTES no routes.py).
# Checar no front evita enviar à toa um arquivo que o servidor vai recusar.
MAX_MB = 10

# Configuração da página
st.set_page_config(
    page_title="Leitor Inteligente de Documentos", 
    page_icon="📄", 
    layout="centered"
)

# CSS PERSONALIZADO PARA O MODO ESCURO (BLACK THEME) 
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #F8FAFC;
    }

    /* Fundo preto elegante para toda a aplicação */
    .stApp {
        background-color: #09090B;
    }

    /* Estilo do Título Principal */
    h1 {
        color: #F8FAFC !important;
        font-weight: 700;
        letter-spacing: -0.5px;
        font-size: 2.2rem !important;
        margin-bottom: 0.2rem;
    }

    /* Subtítulo mais suave */
    p.subtitle {
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Botão Principal com estilo moderno e transição suave */
    .stButton > button {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        transition: all 0.3s ease;
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# CORPO DA APLICAÇÃO 
st.title("📄 Seu leitor inteligente de documentos")
# ALTERAÇÃO: trocamos "base exata no arquivo" por "com base no conteúdo". Em documentos longos o
# sistema envia à IA só os trechos mais relevantes (RAG), então "exata" prometia mais do que o código faz.
st.markdown('<p class="subtitle">Envie seu documento e faça uma pergunta. A resposta é gerada com base no conteúdo do arquivo.</p>', unsafe_allow_html=True)

# ALTERAÇÃO (privacidade): a demonstração é pública e cada análise (arquivo, pergunta e resposta) é gravada.
st.info("Demonstração pública: não envie documentos com dados pessoais ou sigilosos. O nome do arquivo, a pergunta e a resposta ficam registrados.")

# Seção de Upload e Pergunta
uploaded_file = st.file_uploader("Escolha ou arraste o seu arquivo PDF", type=["pdf"])
# ALTERAÇÃO (limites): avisa os limites antes de a pessoa enviar. Valem os mesmos números da API.
st.caption(f"Limites da demonstração: até {MAX_MB} MB e 100 páginas. Em PDF escaneado, o sistema lê as 20 primeiras páginas.")

user_question = st.text_input("O que você gostaria de saber sobre este documento?", "")
# ALTERAÇÃO (dicas): o RAG acha os trechos pelas palavras da pergunta, então perguntas sobre um dado
# concreto funcionam melhor. A pessoa continua livre para perguntar o que quiser.
st.caption("Funciona melhor com perguntas sobre um dado concreto, como \"qual é o prazo?\" ou \"quem são as partes?\". Pedidos de resumo geral podem ficar incompletos em documentos longos.")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Executar Análise com IA"):
    if uploaded_file and user_question:

        # ALTERAÇÃO (limites): se o arquivo passa do limite, avisa e para aqui, sem chamar a API.
        if uploaded_file.size > MAX_MB * 1024 * 1024:
            st.warning(f"⚠️ O arquivo passa de {MAX_MB} MB, o limite da demonstração.")
            st.stop()
        
        analysis_output = ""
        # ALTERAÇÃO (erros): marca se houve erro, para mostrar a mensagem como aviso e não como "resposta".
        deu_erro = False
        
        # Bloco de status visual para acompanhar a execução dos agentes de IA
        with st.status("🚀 Os agentes de inteligência artificial estão em ação...", expanded=True) as status:
            
            st.write("🔍 **Agente 1 (Extrator):** Lendo o documento e extraindo as entidades...")
            time.sleep(0.5)
            
            st.write("🛡 **Agente 2 (Validador):** Auditando a consistência dos dados...")
            time.sleep(0.5)
            
            st.write("💡 **Agente 3 (Analista):** Preparando a resposta estruturada...")
            
            # Prepara os parâmetros para o envio via requisição HTTP para o FastAPI
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            data = {"question": user_question}
            
            # Obtém a URL da API (verifica BACKEND_URL nas secrets, depois API_URL, ou usa o Render como padrão)
            try:
                API_URL = st.secrets.get("BACKEND_URL", st.secrets.get("API_URL", os.getenv("BACKEND_URL", "https://agentes-de-analise.onrender.com")))
            except Exception:
                API_URL = os.getenv("BACKEND_URL", "https://agentes-de-analise.onrender.com")
            
            try:
                # Realiza a chamada HTTP para o backend FastAPI no Render com timeout alargado (300s)
                response = requests.post(f"{API_URL}/documents/analyze", files=files, data=data, timeout=300)
                
                if response.status_code == 200:
                    result = response.json()
                    status.update(label="✅ Análise concluída com sucesso pelos agentes!", state="complete", expanded=False)
                    analysis_output = result.get("analysis_result", "Nenhuma resposta encontrada.")
                else:
                    deu_erro = True
                    status.update(label="❌ Não foi possível concluir a análise.", state="error", expanded=True)
                    # Se o Render retornar página HTML de erro (502, 503, etc.)
                    if "<html" in response.text.lower() or response.status_code in [502, 503, 504]:
                        analysis_output = "⚠️ O servidor está reiniciando (no plano gratuito ele \"dorme\" sem uso). Aguarde alguns segundos e clique novamente em executar."
                    else:
                        # ALTERAÇÃO (erros): para os erros da validação da API (400 e 413) mostramos só a mensagem
                        # ("O PDF tem 150 páginas...") e não o JSON inteiro. Para os demais erros, uma mensagem
                        # genérica, para não expor detalhes internos do servidor.
                        try:
                            detalhe = response.json().get("detail", "")
                        except ValueError:
                            detalhe = ""
                        if response.status_code in (400, 413) and isinstance(detalhe, str) and detalhe:
                            analysis_output = f"⚠️ {detalhe}"
                        else:
                            analysis_output = "⚠️ Ocorreu um erro ao processar o documento. Tente novamente em instantes."
                    
            except Exception:
                deu_erro = True
                status.update(label="❌ Falha de conexão com o servidor.", state="error", expanded=True)
                # ALTERAÇÃO (erros): não mostramos o endereço interno da API nem o texto do erro.
                analysis_output = "⚠️ Não foi possível conectar ao servidor. Ele pode estar acordando; tente novamente em alguns segundos."

        # RESPOSTA FINAL (Apresentada de forma limpa e visível abaixo) 
        if analysis_output:
            st.markdown("---")
            if deu_erro:
                st.warning(analysis_output)
            else:
                st.markdown("### 📋 Resposta da Análise")
                st.markdown(analysis_output)

    else:
        st.warning("⚠️ Por favor, envie um arquivo PDF e escreva uma pergunta antes de avançar.")