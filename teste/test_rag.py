
import sys
import os

# Adiciona a pasta backend ao caminho do Python (mesmo truque do outro arquivo de testes)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from src.infrastructure.rag import (
    dividir_em_trechos,
    selecionar_trechos,
    TAMANHO_TRECHO,
    LIMITE_TEXTO_CURTO,
)

# Texto de enchimento longo, com uma informação importante escondida no meio.
ENCHIMENTO = "A contratada deve manter registros atualizados das atividades realizadas. " * 400
FATO = "A multa por rescisão antecipada é de 15% sobre o valor restante do contrato. "
TEXTO_LONGO = ENCHIMENTO + FATO + ENCHIMENTO


def test_texto_curto_vai_inteiro():
    """Documentos pequenos não precisam de busca: devem seguir completos."""
    texto = "Contrato curto. O valor é R$ 100,00."
    assert selecionar_trechos(texto, "Qual é o valor?") == texto


def test_trechos_respeitam_o_tamanho_maximo():
    """Nenhum trecho pode passar do tamanho configurado."""
    trechos = dividir_em_trechos(TEXTO_LONGO)
    assert len(trechos) > 1
    assert all(len(t) <= TAMANHO_TRECHO for t in trechos)


def test_busca_encontra_a_informacao_no_meio_do_documento():
    """O ponto principal do RAG: achar o trecho certo mesmo em um texto grande."""
    assert len(TEXTO_LONGO) > LIMITE_TEXTO_CURTO
    resultado = selecionar_trechos(TEXTO_LONGO, "Qual é a multa por rescisão antecipada?")
    assert "15%" in resultado


def test_pergunta_generica_ainda_devolve_texto():
    """Se nenhuma palavra da pergunta aparece, o sistema ainda deve devolver trechos do documento."""
    resultado = selecionar_trechos(TEXTO_LONGO, "o que consta no pdf?")
    assert resultado.strip() != ""