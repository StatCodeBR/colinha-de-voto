"""Gerador do site estático: lê data/processed/ e escreve site/dist/.

As páginas recebem textos já prontos (ver `textos`), para que os templates só
posicionem conteúdo e todas as regras de linguagem fiquem testáveis em Python.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import unicodedata
from importlib import resources
from pathlib import Path
from typing import Any
from urllib.parse import quote

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from colinha.config import UFS, Config
from colinha.site import textos
from colinha.vinculo import MANDATO_ANOS

MAX_REDES = 20  # links de redes sociais exibidos por candidato (mesmo limite para todos)


def dir_dist(cfg: Config) -> Path:
    return cfg.raiz / "site" / "dist"


def _ler(caminho: Path) -> Any:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _busca(*partes: str | None) -> str:
    """Texto para a busca: minúsculas e sem acento, como o JS normaliza a consulta."""
    texto = " ".join(p for p in partes if p)
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return sem_acento.lower()


# --- Fontes -------------------------------------------------------------------------------


def texto_fontes(fontes: list[dict[str, Any]]) -> dict[str, Any]:
    """"Fonte: TSE, dados extraídos em 27/09/2026", com os links dos arquivos."""
    datas = sorted({textos.data_br(f["extraido_em"]) for f in fontes})
    return {
        "texto": f"Fonte: TSE, dados extraídos em {' e '.join(datas)}",
        "links": [{"nome": f["nome"], "url": f["url"]} for f in fontes],
    }


# --- Candidato ----------------------------------------------------------------------------


def ano_mandato(cfg: Config, cargo: str) -> int:
    return cfg.eleicao.ano - MANDATO_ANOS.get(cargo, 4)


def texto_reeleicao(d: dict[str, Any], cfg: Config) -> str | None:
    if not d["historico"]["busca_reeleicao"]:
        return None
    g = d["perfil"]["genero"]
    return (
        f"{textos.flexao(g, 'Eleito', 'Eleita', 'Eleito(a)')} "
        f"{textos.cargo(d['cargo'], g).lower()} em {ano_mandato(cfg, d['cargo'])}"
    )


def pagina_candidato(d: dict[str, Any], cfg: Config) -> dict[str, Any]:
    """Tudo que a página do candidato mostra, já em texto."""
    g = d["perfil"]["genero"]
    h = d["historico"]
    cob = h["cobertura"]
    janela = f"de {cob['inicio']} a {cob['fim']}"
    cargo_txt = textos.cargo(d["cargo"], g)
    uf_nome = textos.NOMES_UF[d["uf"]]

    trajetoria = [
        {
            "ano": t["ano"],
            "cargo": textos.cargo(t["cargo"], g),
            "local": textos.titulo(t["local"]),
            "partido": t["partido"] or textos.NAO_INFORMADO,
            "resultado": textos.resultado(t["resultado"], g),
        }
        for t in d["trajetoria"]
    ]
    if h["classe"] == "sem_registro":
        aviso_trajetoria = f"Nenhuma candidatura encontrada {janela}."
    elif h["classe"] == "em_verificacao":
        aviso_trajetoria = (
            f"Encontramos registros possíveis {janela} que ainda estão em verificação. "
            "Eles só aparecem aqui depois de conferidos."
        )
    elif h["ha_registros_em_verificacao"]:
        aviso_trajetoria = "Outros registros possíveis estão em verificação."
    else:
        aviso_trajetoria = None

    redes = [r for r in (textos.link_rede(u) for u in d["redes_sociais"]) if r]
    federacao = textos.federacao(d["federacao"])
    titulo = f"{d['nome_urna']} {d['numero']}: {cargo_txt.lower()} em {uf_nome}"
    candidata = textos.flexao(g, "candidato", "candidata", "candidato(a)")
    local_eleicao = "no Brasil" if d["uf"] == "BR" else f"em {uf_nome}"
    return {
        "id": d["id"],
        "url": f"/{d['id']}/",
        "uf": d["uf"],
        "uf_nome": uf_nome,
        "chave_colinha": d["uf"],
        "numero": d["numero"],
        "cargo": d["cargo"],
        "cargo_texto": cargo_txt,
        "cabecalho": f"{cargo_txt} {local_eleicao}",
        "nome_urna": d["nome_urna"],
        "nome_exibido": d["nome_exibido"],
        "partido": d["partido"],
        "federacao": federacao,
        "apto": d["situacao"]["apto"],
        "situacao": textos.situacao(d["situacao"]["descricao"]),
        "reeleicao": texto_reeleicao(d, cfg),
        "trajetoria": trajetoria,
        "aviso_trajetoria": aviso_trajetoria,
        "cobertura": f"Pesquisamos candidaturas {janela} nos dados abertos do TSE.",
        "perfil": [
            ("Idade", textos.idade(d["perfil"]["idade"])),
            ("Gênero", textos.frase(g)),
            ("Cor ou raça", textos.frase(d["perfil"]["cor_raca"])),
            ("Grau de instrução", textos.frase(d["perfil"]["grau_instrucao"])),
            ("Ocupação declarada", textos.frase(d["perfil"]["ocupacao"])),
            (
                "Bens declarados",
                textos.bens(
                    d["bens"]["declarou_bens"], d["bens"]["total"], d["bens"]["quantidade"]
                ),
            ),
        ],
        "redes": redes[:MAX_REDES],
        "redes_restantes": max(0, len(d["redes_sociais"]) - min(len(redes), MAX_REDES)),
        "fonte_candidatura": texto_fontes(d["fontes"]["candidatura"] + d["fontes"]["bens"]),
        "fonte_redes": texto_fontes(d["fontes"]["redes_sociais"]),
        "fonte_trajetoria": texto_fontes(d["fontes"]["trajetoria"]),
        "titulo": titulo,
        "descricao": (
            f"Trajetória eleitoral e dados declarados ao TSE de {d['nome_urna']}, "
            f"{candidata} a {textos.CARGO_GENERICO[d['cargo']]} {local_eleicao}, "
            f"número {d['numero']}."
        ),
    }


def janela(d: dict[str, Any]) -> str:
    cob = d["historico"]["cobertura"]
    return f"de {cob['inicio']} a {cob['fim']}"


def linha_lista(d: dict[str, Any], cfg: Config) -> dict[str, Any]:
    """Linha da lista por cargo, com os atributos usados pelos filtros."""
    g = d["perfil"]["genero"]
    return {
        "id": d["id"],
        "url": f"/{d['id']}/",
        "uf": d["uf"],
        "numero": d["numero"],
        "nome_urna": d["nome_urna"],
        "partido": d["partido"],
        "cargo": d["cargo"],
        "genero": g or "",
        "historico": d["historico"]["classe"],
        "etiqueta": textos.etiqueta_historico(d["historico"]["classe"], g, janela(d)),
        "reeleicao": texto_reeleicao(d, cfg),
        "apto": d["situacao"]["apto"],
        "situacao": None if d["situacao"]["apto"] else textos.situacao(d["situacao"]["descricao"]),
        "busca": _busca(d["nome_urna"], d["numero"], d["partido"]),
    }


# --- Escrita ------------------------------------------------------------------------------


def versao_estaticos(pasta: Path) -> str:
    """Hash curto do conteúdo de static/, para invalidar o cache do navegador."""
    h = hashlib.sha256()
    for arquivo in sorted(p for p in pasta.rglob("*") if p.is_file()):
        h.update(arquivo.relative_to(pasta).as_posix().encode())
        h.update(arquivo.read_bytes())
    return h.hexdigest()[:10]


def _ambiente(cfg: Config, manifesto: dict[str, Any], versao: str) -> Environment:
    env = Environment(
        loader=PackageLoader("colinha", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(
        projeto=cfg.projeto,
        ano=cfg.eleicao.ano,
        atualizado_em=textos.data_br(manifesto["gerado_em"]),
        email_erro=cfg.projeto.email_contato,
        vagas=cfg.eleicao.vagas_colinha,
        rotulos={c: textos.CARGOS[c][0] for c in cfg.eleicao.cargos},
        versao=versao,
    )
    env.filters["quote"] = lambda s: quote(str(s), safe="")
    return env


def _gravar(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def gerar(cfg: Config, log=print) -> None:
    """Regenera site/dist/ inteiro a partir de data/processed/."""
    proc = cfg.dir_processed
    dist = dir_dist(cfg)
    if dist.exists():
        shutil.rmtree(dist)
    estaticos = resources.files("colinha") / "static"
    with resources.as_file(estaticos) as origem:
        shutil.copytree(origem, dist / "static")

    manifesto = _ler(proc / "manifesto.json")
    env = _ambiente(cfg, manifesto, versao_estaticos(dist / "static"))
    base = cfg.projeto.url_base.rstrip("/")
    urls: list[str] = []

    def pagina(rota: str, template: str, **contexto: Any) -> None:
        caminho = dist / rota.strip("/") / "index.html" if rota != "/" else dist / "index.html"
        contexto.setdefault("url_canonica", f"{base}{rota}")
        _gravar(caminho, env.get_template(template).render(**contexto))
        urls.append(f"{base}{rota}")

    def detalhes(uf: str) -> list[dict[str, Any]]:
        indice = _ler(proc / uf / "indice.json")
        (dist / "dados").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(proc / uf / "indice.json", dist / "dados" / f"{uf}.json")
        return [
            _ler(proc / uf / "candidatos" / (c["id"].split("/", 1)[1] + ".json"))
            for c in indice["candidatos"]
        ]

    presidentes = detalhes("BR")
    for d in presidentes:
        pagina(f"/{d['id']}/", "candidato.html", c=pagina_candidato(d, cfg))

    ufs = [uf for uf in UFS if (proc / uf / "indice.json").exists()]
    cargos_por_uf: dict[str, list[str]] = {}
    for uf in ufs:
        todos = detalhes(uf)
        for d in todos:
            pagina(f"/{d['id']}/", "candidato.html", c=pagina_candidato(d, cfg))
        presentes = {d["cargo"] for d in todos} | {"PRESIDENTE"}
        cargos = [c for c in cfg.eleicao.ordem_urna if c in presentes]
        cargos_por_uf[uf] = cargos
        resumo_cargos = []
        for cargo in cargos:
            lista = presidentes if cargo == "PRESIDENTE" else [d for d in todos if d["cargo"] == cargo]
            linhas = [linha_lista(d, cfg) for d in lista]
            slug = textos.slug_cargo(cargo)
            partidos = sorted({x["partido"] for x in linhas})
            pagina(
                f"/{uf.lower()}/{slug}/",
                "lista.html",
                uf=uf,
                uf_nome=textos.NOMES_UF[uf],
                cargo=cargo,
                cargo_generico=textos.CARGO_GENERICO[cargo],
                ano_mandato=ano_mandato(cfg, cargo),
                janela=f"de {min(cfg.eleicao.anos_historico)} a {max(cfg.eleicao.anos_historico)}",
                linhas=linhas,
                partidos=partidos,
                aptas=sum(x["apto"] for x in linhas),
            )
            resumo_cargos.append(
                {
                    "texto": textos.CARGOS[cargo][0],
                    "url": f"/{uf.lower()}/{slug}/",
                    "aptas": sum(x["apto"] for x in linhas),
                    "vagas": cfg.eleicao.vagas_colinha[cargo],
                }
            )
        pagina(f"/{uf.lower()}/", "uf.html", uf=uf, uf_nome=textos.NOMES_UF[uf], cargos=resumo_cargos)
        log(f"site {uf}: {len(todos)} candidaturas")

    config_colinha = {
        "ordem": list(cfg.eleicao.ordem_urna),
        "vagas": cfg.eleicao.vagas_colinha,
        "rotulos": {c: textos.CARGOS[c][0] for c in cfg.eleicao.ordem_urna},
        "cargosPorUf": cargos_por_uf,
        "nomesUf": {uf: textos.NOMES_UF[uf] for uf in ufs},
    }
    pagina(
        "/",
        "inicio.html",
        ufs=[(uf, textos.NOMES_UF[uf], uf in ufs) for uf in UFS],
    )
    pagina("/colinha/", "colinha.html", config_colinha=config_colinha)
    pagina(
        "/metodologia/",
        "metodologia.html",
        fontes=[
            {**f, "extraido_em": textos.data_br(f["extraido_em"])}
            for grupo in manifesto["fontes"].values()
            for f in grupo
        ],
        cobertura=cfg.eleicao.anos_historico,
        resumo=_ler(proc / "resumo.json"),
    )
    _gravar(dist / "404.html", env.get_template("404.html").render(url_canonica=f"{base}/"))
    _gravar(dist / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    _gravar(
        dist / "sitemap.xml",
        env.get_template("sitemap.xml").render(urls=urls),
    )
    log(f"site: {len(urls)} páginas em {dist}")
