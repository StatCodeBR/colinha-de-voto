import re
from pathlib import Path

import pandas as pd
import pytest

from colinha import site
from colinha.site import textos
from tests.test_saida import gerar_tudo

CSS = Path(__file__).parents[1] / "src" / "colinha" / "static" / "css" / "site.css"

# --- Textos -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cargo", "genero", "esperado"),
    [
        ("VEREADOR", "FEMININO", "Vereadora"),
        ("VEREADOR", "MASCULINO", "Vereador"),
        ("VEREADOR", None, "Vereador(a)"),
        ("DEPUTADO ESTADUAL", "FEMININO", "Deputada estadual"),
        ("1º SUPLENTE", "FEMININO", "1ª suplente de senador"),
    ],
)
def test_cargo_com_flexao(cargo, genero, esperado):
    assert textos.cargo(cargo, genero) == esperado


def test_resultado_com_flexao():
    assert textos.resultado("eleito", "FEMININO") == "Eleita"
    assert textos.resultado("nao_eleito", "MASCULINO") == "Não eleito"


@pytest.mark.parametrize(
    "funcao", [lambda: textos.cargo("XERIFE", None), lambda: textos.situacao("NOVA")]
)
def test_valor_desconhecido_falha(funcao):
    with pytest.raises(textos.ErroTexto):
        funcao()


def test_sem_registro_sempre_com_janela():
    assert textos.etiqueta_historico("sem_registro", None, "de 2014 a 2024") == (
        "Nenhuma candidatura encontrada de 2014 a 2024"
    )


def test_formatos():
    assert textos.titulo("SÃO JOÃO DA BARRA") == "São João da Barra"
    assert textos.titulo("VICE-PREFEITO") == "Vice-Prefeito"
    assert textos.titulo("SANTA BÁRBARA D'OESTE") == "Santa Bárbara d'Oeste"
    assert textos.titulo("ITAPORANGA D'AJUDA") == "Itaporanga d'Ajuda"
    assert textos.titulo(None) == "Não informado"
    assert textos.frase("ENSINO MÉDIO COMPLETO") == "Ensino médio completo"
    assert textos.frase(None) == "Não informado"
    assert textos.federacao("13-PT/65-PC do B/43-PV") == "PT/PC do B/PV"
    assert textos.reais(5119829.39) == "R$ 5.119.829,39"
    assert textos.data_br("2026-09-27T16:14:42-03:00") == "27/09/2026"
    assert textos.idade(None) == "Não informado"


def test_bens_nao_declarados_nao_viram_zero():
    assert textos.bens(False, None, None) == "Não declarou bens ao TSE"
    assert textos.bens(None, None, None) == "Não informado"
    assert textos.bens(True, 0.0, 1) == "R$ 0,00, soma de 1 bem declarado"
    assert textos.bens(True, 1500.5, 2) == "R$ 1.500,50, soma de 2 bens declarados"


@pytest.mark.parametrize(
    ("url", "esperado"),
    [
        ("HTTPS://WWW.INSTAGRAM.COM/FULANA", "https://www.instagram.com/FULANA"),
        ("instagram.com/fulana", "https://instagram.com/fulana"),
        ("@fulana", None),
        ("javascript:alert(1)", None),
    ],
)
def test_link_de_rede_social(url, esperado):
    link = textos.link_rede(url)
    assert (link and link["href"]) == esperado


# --- Contraste (WCAG AA) ------------------------------------------------------------------


def _tokens() -> dict[str, str]:
    return dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6})", CSS.read_text()))


def _luminancia(hexa: str) -> float:
    canais = [int(hexa[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(a: str, b: str) -> float:
    la, lb = sorted([_luminancia(a), _luminancia(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize(
    ("texto", "fundo"),
    [
        ("texto", "papel"),
        ("texto-suave", "papel"),
        ("tinta", "papel"),
        ("texto", "cinza-urna"),
        ("texto-suave", "cinza-urna"),
        ("tinta", "cinza-urna"),
        ("#ffffff", "confirma"),
        ("#ffffff", "corrige"),
    ],
)
def test_contraste_aa(texto, fundo):
    t = _tokens()
    cor = lambda nome: nome if nome.startswith("#") else t[nome]  # noqa: E731
    assert contraste(cor(texto), cor(fundo)) >= 4.5


# --- Geração ------------------------------------------------------------------------------


@pytest.fixture
def dist(raiz: Path) -> Path:
    cfg = gerar_tudo(raiz)
    site.gerar(cfg, log=lambda m: None)
    return site.dir_dist(cfg)


def _secoes(html: str) -> list[str]:
    return re.findall(r'<h2 id="([^"]+)"', html)


def test_todas_as_paginas_de_candidato_tem_as_mesmas_secoes(dist: Path):
    paginas = [dist / "rr" / "1111", dist / "rr" / "22", dist / "br" / "10"]
    secoes = {tuple(_secoes((p / "index.html").read_text())) for p in paginas}
    assert secoes == {("t-trajetoria", "t-dados")}


def test_nenhum_cpf_nem_recurso_externo_no_site(dist: Path, raiz: Path):
    cpfs = set(pd.read_parquet(raiz / "data" / "interim" / "candidaturas.parquet")["cpf"].dropna())
    for arquivo in dist.rglob("*"):
        if arquivo.suffix not in {".html", ".json", ".js", ".css", ".xml", ".txt"}:
            continue
        texto = arquivo.read_text(encoding="utf-8")
        assert not any(c in texto for c in cpfs), arquivo
        if arquivo.suffix == ".html":
            carregados = re.findall(r'<script[^>]+src="([^"]+)"', texto) + re.findall(
                r'<link[^>]+rel="(?:stylesheet|preload)"[^>]+href="([^"]+)"', texto
            )
            assert carregados and all(u.startswith("/") for u in carregados), arquivo


def test_paginas_e_arquivos_gerados(dist: Path):
    for rota in [
        "index.html",
        "rr/index.html",
        "rr/deputado-federal/index.html",
        "rr/senador/index.html",
        "rr/presidente/index.html",
        "colinha/index.html",
        "metodologia/index.html",
        "404.html",
        "robots.txt",
        "sitemap.xml",
        "dados/RR.json",
        "dados/BR.json",
        "static/fontes/atkinson-hyperlegible-next.woff2",
    ]:
        assert (dist / rota).exists(), rota


def test_pagina_do_candidato(dist: Path):
    html = (dist / "rr" / "1111" / "index.html").read_text()
    assert 'aria-label="número 1111"' in html
    assert "Deputada federal em Roraima" in html  # gênero declarado: feminino
    assert "Ficou como suplente" in html  # trajetória confirmada de 2022
    assert "Fonte: TSE, dados extraídos em 28/09/2026" in html
    assert '<meta property="og:title" content="ANA 1111: deputada federal em Roraima' in html
    assert "mailto:" in html and "Encontrou um erro?" in html
    assert "ANA, candidata a deputada federal em Roraima" in html  # meta descrição
    assert "dados abertos do TSE (Tribunal Superior Eleitoral)" in html


def test_candidato_sem_registro_mostra_a_janela(dist: Path):
    html = (dist / "rr" / "22" / "index.html").read_text()
    assert "Nenhuma candidatura encontrada de 2022 a 2022." in html
    assert "primeira candidatura" not in html.lower()


def test_csp_do_nginx_cobre_o_script_inline():
    import base64
    import hashlib

    raiz = Path(__file__).parents[1]
    base = (raiz / "src" / "colinha" / "templates" / "base.html").read_text()
    inline = re.findall(r"<script>(.*?)</script>", base)
    assert len(inline) == 1
    digest = base64.b64encode(hashlib.sha256(inline[0].encode()).digest()).decode()
    assert f"'sha256-{digest}'" in (raiz / "deploy" / "nginx.conf").read_text()


# --- Preposição da UF e link "Voltar" (change add-botao-voltar) --------------------------


@pytest.mark.parametrize(
    ("uf", "em", "de"),
    [
        ("SP", "em São Paulo", "de São Paulo"),
        ("RJ", "no Rio de Janeiro", "do Rio de Janeiro"),
        ("BA", "na Bahia", "da Bahia"),
        ("DF", "no Distrito Federal", "do Distrito Federal"),
        ("BR", "no Brasil", "do Brasil"),
    ],
)
def test_preposicao_da_uf(uf, em, de):
    assert textos.em_uf(uf) == em
    assert textos.de_uf(uf) == de


def test_toda_uf_tem_artigo():
    assert set(textos.ARTIGO_UF) == set(textos.NOMES_UF)


@pytest.mark.parametrize(
    ("args", "href", "texto"),
    [
        (("uf", "RR"), "/", "Voltar para a escolha de estado"),
        (("lista", "RR", "DEPUTADO FEDERAL"), "/rr/", "Voltar para Roraima"),
        (("lista", "BA", "SENADOR"), "/ba/", "Voltar para a Bahia"),
        (("lista", "RJ", "SENADOR"), "/rj/", "Voltar para o Rio de Janeiro"),
        (
            ("candidato", "RR", "DEPUTADO FEDERAL"),
            "/rr/deputado-federal/",
            "Voltar para deputado federal em Roraima",
        ),
        (
            ("candidato", "RJ", "SENADOR"),
            "/rj/senador/",
            "Voltar para senador no Rio de Janeiro",
        ),
        (("candidato", "BR", "PRESIDENTE"), "/", "Voltar para a escolha de estado"),
        (("colinha",), "/", "Voltar para a escolha de estado"),
        (("metodologia",), "/", "Voltar para a escolha de estado"),
    ],
)
def test_destino_do_voltar(args, href, texto):
    assert textos.voltar(*args) == {"href": href, "texto": texto}


def test_pagina_sem_destino_falha():
    with pytest.raises(textos.ErroTexto):
        textos.voltar("inicio")


def _voltar(html: str) -> list[tuple[str, str]]:
    return re.findall(
        r'<p class="voltar"><a href="([^"]+)" data-voltar[^>]*>'
        r'<span aria-hidden="true">← </span>([^<]+)</a>',
        html,
    )


def test_toda_subpagina_tem_um_link_voltar(dist: Path):
    esperado = {
        "rr/index.html": ("/", "Voltar para a escolha de estado"),
        "rr/deputado-federal/index.html": ("/rr/", "Voltar para Roraima"),
        "rr/presidente/index.html": ("/rr/", "Voltar para Roraima"),
        "rr/1111/index.html": ("/rr/deputado-federal/", "Voltar para deputado federal em Roraima"),
        "br/10/index.html": ("/", "Voltar para a escolha de estado"),
        "colinha/index.html": ("/", "Voltar para a escolha de estado"),
        "metodologia/index.html": ("/", "Voltar para a escolha de estado"),
    }
    for rota, destino in esperado.items():
        assert _voltar((dist / rota).read_text()) == [destino], rota
    assert "data-voltar-presidente" in (dist / "br" / "10" / "index.html").read_text()
    assert "data-voltar-presidente" not in (dist / "rr" / "1111" / "index.html").read_text()
    for rota in ["index.html", "404.html"]:
        assert "data-voltar" not in (dist / rota).read_text(), rota


def test_metodologia_explica_a_contagem_de_acessos(dist: Path):
    html = (dist / "metodologia" / "index.html").read_text()
    paragrafo = html.split("<h2>Contagem de acessos</h2>")[1].split("<h2>")[0]
    for ponto in ["não usa cookies", "gravado incompleto", "30 dias", "quais candidatos"]:
        assert ponto in paragrafo, ponto


def test_nenhum_script_de_contagem(dist: Path):
    scripts = set()
    for arquivo in dist.rglob("*.html"):
        for src in re.findall(r'<script[^>]+src="([^"?]+)', arquivo.read_text()):
            scripts.add(src)
    assert scripts <= {"/static/js/busca.js", "/static/js/colinha.js", "/static/js/compartilhar.js"}


def test_registro_do_nginx_nao_grava_dado_identificavel():
    conf = (Path(__file__).parents[1] / "deploy" / "nginx.conf").read_text()
    formato = conf.split("log_format anonimo")[1].split(";")[0]
    assert formato.lstrip().startswith("'$ip_anonimo ")
    for proibido in [
        "$remote_addr",
        "$http_x_forwarded_for",
        "$http_cookie",
        "$request ",
        "$request_uri",
        "$args",
        "$http_referer",
    ]:
        assert proibido not in formato, proibido
    acessos = re.findall(r"^\s*access_log\s+([^;]+);", conf, re.M)
    assert acessos == ["/var/log/colinha/acessos-$dia.log anonimo"]
