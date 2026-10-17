
# Agentes de Análise de Documentos

Projeto para ler e analisar PDFs com inteligência artificial. Você envia o arquivo, escreve uma pergunta e recebe a resposta com base no que está no documento. Funciona com PDFs digitais e escaneados, e cada análise fica registrada em um banco de dados e em uma planilha do Google Sheets.

👉 **Teste online:** [clique aqui para testar](https://nc6glffthdanpfvm739guz.streamlit.app/)

> **Demonstração pública:** não envie documentos com dados pessoais ou sigilosos. O nome do arquivo, a pergunta e a resposta ficam registrados.
>
> As respostas são geradas por IA e podem conter erros. Confira no documento original o que for importante.

## O que o projeto faz?
* **Lê PDFs digitais e escaneados:** primeiro tenta extrair o texto do PDF. Se não houver texto selecionável, usa OCR para ler as páginas como imagem.
* **Responde a sua pergunta com base no documento:** em PDFs longos, o sistema não manda tudo para a IA. Ele divide o texto em trechos, escolhe os que mais combinam com a pergunta e envia só esses (essa técnica se chama RAG).
* **Usa três etapas de IA em sequência:** o Extrator tira os dados dos trechos, o Validador confere esses dados contra o texto original e o Analista escreve a resposta final.
* **Guarda o histórico:** cada análise (arquivo, pergunta e resposta) é salva em um banco PostgreSQL e adicionada a uma planilha do Google Sheets.
* **Tem limites de uso:** PDFs de até 10 MB e 100 páginas. Em PDF escaneado, o OCR lê as 20 primeiras páginas.
* **Tem testes automatizados:** testes com `pytest` cobrem as regras de entrada da API, a busca de trechos e a limpeza da resposta.

## Como a busca de trechos funciona?
1. O texto é extraído de todas as páginas do PDF.
2. Documentos curtos (até 6.000 caracteres) vão inteiros para a IA.
3. Nos longos, o texto é dividido em trechos de cerca de 1.000 caracteres, com uma sobreposição para não cortar uma ideia no meio.
4. Cada trecho recebe uma nota (BM25): ela sobe quando o trecho tem as palavras da pergunta, principalmente as que aparecem pouco no documento.
5. Os 6 trechos com a maior nota vão para os agentes.

**Exemplo de teste:** contrato fictício de 80 páginas, pergunta *"Qual é a multa por rescisão antecipada?"*
* Antes, lendo só os primeiros 4.000 caracteres: *"não há informação sobre a multa"*.
* Depois, com a busca de trechos: *15% sobre o valor restante do contrato (cláusula 47.6)*.

## Quais tecnologias foram usadas?
* **Python e FastAPI:** a API que recebe o PDF e a pergunta.
* **Streamlit:** a interface para enviar o documento e ver a resposta.
* **Groq:** o modelo de linguagem usado pelos três agentes.
* **Neon (PostgreSQL) e SQLAlchemy:** o banco de dados na nuvem e o acesso a ele.
* **Pytesseract, PDF2Image e Pypdf:** leitura do PDF e OCR.
* **Gspread:** a integração com o Google Sheets.
* **Pytest:** os testes automatizados.
* **Render:** onde a API está publicada.

## Como rodar no seu computador?

Você precisa de Python 3.10 ou superior, do Tesseract (com o idioma português) e do Poppler.

```bash
# 1. API
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Crie o arquivo `backend/.env` com as suas chaves:

```
GROQ_API_KEY=sua_chave_da_groq
DATABASE_URL=sua_url_do_postgresql
```

```bash
# 2. Interface (em outro terminal, na raiz do projeto)
pip install streamlit
streamlit run frontend/app.py
```

Por padrão, a interface chama a API publicada no Render. Para usar a API local, defina a variável `BACKEND_URL` como `http://localhost:8000`.

Para gravar na planilha, é preciso um `credentials.json` de uma conta de serviço do Google e uma planilha chamada **CRM de Documentos** compartilhada com ela. Se isso não estiver configurado, a análise funciona normalmente e só a gravação na planilha falha.

> Nunca envie o `.env` nem o `credentials.json` para o GitHub.

Para rodar os testes:

```bash
pip install -r backend/requirements-dev.txt
pytest
```

## O que o projeto ainda não faz bem?
* **Pedidos gerais**, como "faça um resumo do documento", ficam incompletos em PDFs longos, porque só 6 trechos chegam à IA. Ele funciona melhor com perguntas sobre um dado concreto, como "qual é o prazo?".
* **A busca compara palavras, e não o significado.** Se a pergunta usar palavras diferentes das do texto, ela pode não achar o trecho certo.
* **A IA pode errar ou misturar informações parecidas.** Os prompts exigem que ela use só os trechos recebidos, e o Validador confere os dados, mas isso diminui o problema sem eliminá-lo.
* Se a gravação no banco ou na planilha falhar, o erro aparece só no log e a API ainda responde normalmente.
* No plano gratuito do Render, a primeira requisição demora enquanto o servidor "acorda".

## Próximos passos
* Resumo de documentos longos, lendo por partes.
* Busca por significado, com embeddings e `pgvector`.
* Mostrar de qual página veio cada informação.
* Registrar os erros com `logging` e avisar na resposta quando a gravação falhar.

---

*Projeto construído, depurado e colocado no ar com muita resiliência, código e chocolates!*

**Andrea Cruz Leonardo** · [LinkedIn](https://www.linkedin.com/in/andrea-cruz-leonardo/) · [GitHub](https://github.com/gitdea)