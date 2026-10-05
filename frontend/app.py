
import streamlit as st
import requests
import time

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
st.markdown('<p class="subtitle">Envie seu documento e faça qualquer pergunta. Nós responderemos com base exata no arquivo.</p>', unsafe_allow_html=True)

# Seção de Upload e Pergunta
uploaded_file = st.file_uploader("Escolha ou arraste o seu arquivo PDF", type=["pdf"])

user_question = st.text_input("O que você gostaria de saber sobre este documento?", "")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Executar Análise com IA"):
    if uploaded_file and user_question:
        
        analysis_output = ""
        
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
            
            try:
                # Realiza a chamada HTTP para o backend FastAPI
                response = requests.post("http://127.0.0.1:8000/documents/analyze", files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    status.update(label="✅ Análise concluída com sucesso pelos agentes!", state="complete", expanded=False)
                    analysis_output = result.get("analysis_result", "Nenhuma resposta encontrada.")
                else:
                    status.update(label="❌ Erro na execução dos agentes.", state="error", expanded=True)
                    analysis_output = f"Erro do servidor: {response.text}"
                    
            except Exception as e:
                status.update(label="❌ Falha de ligação ao backend.", state="error", expanded=True)
                analysis_output = f"Não foi possível conectar ao FastAPI em localhost:8000. Erro: {str(e)}"

        # RESPOSTA FINAL (Apresentada de forma limpa e visível abaixo) 
        if analysis_output:
            st.markdown("---")
            st.markdown("### 📋 Resposta da Análise")
            st.markdown(analysis_output)

    else:
        st.warning(" Por favor, envie um arquivo PDF e escreva uma pergunta antes de avançar.")