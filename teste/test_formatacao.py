
import sys
import os

# Adiciona a pasta backend ao caminho do Python (mesmo truque dos outros arquivos de teste)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from src.infrastructure.agent_service import limpar_html


def test_remove_br_das_celulas_da_tabela():
    """O <br> não pode aparecer na resposta, em nenhuma variação de escrita."""
    texto = "| 1 | • Item A <br>• Item B<BR/>Item C |"
    resultado = limpar_html(texto)
    assert "<br" not in resultado.lower()
    assert "Item A" in resultado and "Item B" in resultado and "Item C" in resultado


def test_mantem_a_estrutura_da_tabela():
    """A limpeza não pode quebrar as barras verticais da tabela em Markdown."""
    texto = "| Cláusula | Texto |\n|---|---|\n| 1 | A <br>B |"
    resultado = limpar_html(texto)
    assert resultado.count("\n") == texto.count("\n")
    assert resultado.splitlines()[2].startswith("| 1 |")


def test_texto_sem_tags_nao_muda():
    """Texto normal, mesmo com os sinais < e >, deve ficar igual."""
    texto = "O valor é 2 < 3 e 5 > 4, sem tags."
    assert limpar_html(texto) == texto


def test_nao_perde_asterisco_de_italico():
    """Um trecho em itálico logo depois do <br> não pode perder o asterisco de abertura."""
    resultado = limpar_html("1.1 Texto A<br>*1.2* Texto B")
    assert "*1.2*" in resultado
    assert "<br" not in resultado.lower()