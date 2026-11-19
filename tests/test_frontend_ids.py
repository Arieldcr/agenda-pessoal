import re
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "frontend"


def ler(nome):
    return (PASTA / nome).read_text(encoding="utf-8")


def test_todos_os_ids_usados_no_javascript_existem_no_html():
    ids_no_html = set(re.findall(r'\sid="([^"]+)"', ler("index.html")))
    ids_usados = set(re.findall(r'getElementById\("([^"]+)"\)', ler("app.js")))

    assert ids_usados - ids_no_html == set()


def test_html_nao_repete_ids():
    ids = re.findall(r'\sid="([^"]+)"', ler("index.html"))

    repetidos = {identificador for identificador in ids if ids.count(identificador) > 1}
    assert repetidos == set()