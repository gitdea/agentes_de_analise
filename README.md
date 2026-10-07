# Agentes de Análise de Documentos

Este projeto nasceu para facilitar a leitura e a análise de documentos em PDF. Você envia o arquivo, faz uma pergunta e recebe a resposta com base no conteúdo do documento. Para isso, combinei inteligência artificial, OCR e banco de dados em um sistema que guarda o histórico de cada análise.

> Demonstração pública: não envie documentos com dados pessoais ou sigilosos. Os arquivos, as perguntas e as respostas ficam registrados.

## O que este projeto faz?
* **Análise com Agentes de IA:** três agentes trabalham em sequência (Extrator, Validador e Analista) para extrair os dados do documento, conferir a consistência e responder à sua pergunta.
* **OCR para PDFs escaneados:** se o PDF não tem texto selecionável, o sistema aplica OCR automaticamente e lê o conteúdo das páginas.
* **Integração com Google Sheets:** cada análise é adicionada automaticamente a uma planilha (através do `gspread`).
* **Registro e Persistência:** o histórico (arquivo, pergunta e resposta) é salvo em um banco PostgreSQL.
* **Testes automatizados:** testes com `pytest` validam as regras de entrada da API.

## Quais tecnologias foram usadas?
* **Python e FastAPI:** a API que recebe o PDF e a pergunta.
* **Streamlit:** a interface para enviar o documento e ver a resposta.
* **Groq:** o modelo de linguagem (LLM) usado pelos três agentes, via API.
* **Neon (PostgreSQL) e SQLAlchemy:** o banco de dados na nuvem e o acesso a ele.
* **Pytesseract, PDF2Image e Pypdf:** leitura do PDF e OCR.
* **Gspread:** a integração com o Google Sheets.
* **Pytest:** os testes automatizados.
* **Render:** onde a API está publicada.

---

## Teste a Aplicação em Tempo Real


 **aplicação online:** [Clica aqui para testar](https://nc6glffthdanpfvm739guz.streamlit.app/)
 
---

*Projeto construído, depurado e colocado no ar com muita resiliência, código e chocolates!*
