
import math
import re
import unicodedata
from collections import Counter

# ALTERAÇÃO (RAG): estes números controlam a busca. Se as respostas vierem incompletas,
# aumente QTD_TRECHOS; se a Groq reclamar de excesso de texto, diminua.
TAMANHO_TRECHO = 1000      # caracteres de cada trecho
SOBREPOSICAO = 200         # quanto um trecho repete do anterior, para não cortar uma ideia no meio
QTD_TRECHOS = 6            # quantos trechos enviamos para os agentes
LIMITE_TEXTO_CURTO = 6000  # documentos até este tamanho vão inteiros, sem busca

# Palavras comuns que não ajudam a achar o trecho certo ("qual", "de", "o"...).
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "que", "qual", "quais", "quem", "quando", "onde",
    "como", "se", "ao", "ou", "foi", "ser", "sao", "tem", "ha", "me", "diga", "informe",
    "documento", "arquivo", "pdf",
}


def _tokenizar(texto: str) -> list[str]:
    """Deixa o texto em minúsculas, sem acentos, e separa em palavras úteis."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    palavras = re.findall(r"\w+", sem_acento)
    return [p for p in palavras if p not in STOPWORDS and len(p) > 1]


def dividir_em_trechos(texto: str, tamanho: int = TAMANHO_TRECHO, sobreposicao: int = SOBREPOSICAO) -> list[str]:
    """Quebra o texto em pedaços de ~'tamanho' caracteres, cortando no último espaço para não partir palavras."""
    texto = re.sub(r"\s+", " ", texto).strip()
    trechos = []
    inicio = 0
    while inicio < len(texto):
        fim = min(inicio + tamanho, len(texto))
        if fim < len(texto):
            ultimo_espaco = texto.rfind(" ", inicio, fim)
            if ultimo_espaco > inicio + tamanho // 2:
                fim = ultimo_espaco
        trechos.append(texto[inicio:fim].strip())
        if fim >= len(texto):
            break
        inicio = fim - sobreposicao  # volta um pouco para os trechos se sobreporem
    return trechos


def _pontuar_bm25(tokens_pergunta: list[str], trechos_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75) -> list[float]:
    """
    BM25: dá uma nota a cada trecho. A nota sobe quando o trecho tem as palavras da pergunta
    (principalmente as raras no documento) e é ponderada pelo tamanho do trecho.
    """
    n = len(trechos_tokens)
    tamanho_medio = (sum(len(t) for t in trechos_tokens) / n) or 1
    em_quantos = Counter()
    for tokens in trechos_tokens:
        for palavra in set(tokens):
            em_quantos[palavra] += 1

    notas = []
    for tokens in trechos_tokens:
        freq = Counter(tokens)
        nota = 0.0
        for palavra in set(tokens_pergunta):
            if freq[palavra] == 0:
                continue
            raridade = math.log(1 + (n - em_quantos[palavra] + 0.5) / (em_quantos[palavra] + 0.5))
            nota += raridade * freq[palavra] * (k1 + 1) / (
                freq[palavra] + k1 * (1 - b + b * len(tokens) / tamanho_medio)
            )
        notas.append(nota)
    return notas


def selecionar_trechos(texto: str, pergunta: str, quantidade: int = QTD_TRECHOS) -> str:
    """Devolve o texto que será enviado aos agentes: o documento inteiro, se for curto, ou só os trechos mais relevantes."""
    if len(texto) <= LIMITE_TEXTO_CURTO:
        return texto

    trechos = dividir_em_trechos(texto)
    if len(trechos) <= quantidade:
        return "\n\n".join(trechos)

    notas = _pontuar_bm25(_tokenizar(pergunta), [_tokenizar(t) for t in trechos])

    if max(notas) <= 0:
        # Pergunta genérica (ex.: "o que consta no PDF?"): nenhuma palavra bateu. Em vez de ficar
        # só com o começo, pegamos trechos espalhados pelo documento todo.
        passo = len(trechos) / quantidade
        escolhidos = sorted({int(i * passo) for i in range(quantidade)})
    else:
        melhores = sorted(range(len(trechos)), key=lambda i: notas[i], reverse=True)[:quantidade]
        escolhidos = sorted(melhores)  # volta para a ordem original do documento

    return "\n\n[...]\n\n".join(trechos[i] for i in escolhidos)