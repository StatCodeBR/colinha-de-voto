"""Saídas públicas em data/processed/: índice por UF, detalhe por candidato, manifesto e
resumo.

Privacidade: todo registro público é montado campo a campo nas funções `item_indice` e
`detalhe` (allowlist). Nunca se parte da tabela completa removendo colunas: uma coluna
nova do TSE não chega à saída sem alguém acrescentá-la aqui.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from colinha import tse
from colinha.coleta import Manifesto
from colinha.config import Config
from colinha.tse import ErroDados
from colinha.vinculo import CONFIRMADO, normalizar_nome

ROTULOS_FONTE = {
    "consulta_cand": "Candidaturas",
    "consulta_cand_complementar": "Candidaturas, dados complementares",
    "bem_candidato": "Bens declarados",
    "rede_social_candidato": "Redes sociais",
}


def _valor(v: Any) -> Any:
    """Nulos do pandas viram None; tipos numpy viram tipos do Python."""
    if v is None or v is pd.NA or (isinstance(v, float) and pd.isna(v)):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


# --- Identificadores ----------------------------------------------------------------------


def atribuir_ids(exib: pd.DataFrame) -> pd.Series:
    """`{uf}/{numero}` para a candidatura apta; inaptas com número repetido levam o
    `sq_candidato` junto (design D3). Índice: `sq_candidato`."""
    grupo = exib.groupby(["uf", "numero"])
    aptas = grupo["apto"].transform("sum")
    repetido = grupo["apto"].transform("size") > 1
    if (aptas > 1).any():
        casos = exib.loc[aptas > 1, ["uf", "numero"]].drop_duplicates().values.tolist()
        raise ErroDados(f"número repetido entre candidaturas aptas: {casos}")
    base = exib["uf"].str.lower() + "/" + exib["numero"]
    ids = base.where(exib["apto"] | ~repetido, base + "-" + exib["sq_candidato"])
    return pd.Series(ids.to_numpy(), index=exib["sq_candidato"].to_numpy())


def arquivo_detalhe(id_publico: str) -> str:
    return id_publico.split("/", 1)[1] + ".json"


# --- Fontes -------------------------------------------------------------------------------


def _fonte(manifesto: Manifesto, prefixo: str, ano: int) -> dict[str, Any]:
    nome = f"{prefixo}_{ano}.zip"
    entrada = manifesto.get(nome)
    if entrada is None:
        raise ErroDados(f"{nome} não está no manifesto de data/raw/")
    return {
        "nome": f"TSE, {ROTULOS_FONTE[prefixo]} {ano}",
        "url": entrada["url"],
        "extraido_em": entrada["baixado_em"],
    }


def fontes(cfg: Config, manifesto: Manifesto) -> dict[str, list[dict[str, Any]]]:
    ano = cfg.eleicao.ano
    return {
        "candidatura": [
            _fonte(manifesto, "consulta_cand", ano),
            _fonte(manifesto, "consulta_cand_complementar", ano),
        ],
        "bens": [_fonte(manifesto, "bem_candidato", ano)],
        "redes_sociais": [_fonte(manifesto, "rede_social_candidato", ano)],
        "trajetoria": [
            _fonte(manifesto, "consulta_cand", a) for a in sorted(cfg.eleicao.anos_historico)
        ],
    }


# --- Registros ----------------------------------------------------------------------------


def idade(nascimento: str | None, referencia: date) -> int | None:
    if nascimento is None or pd.isna(nascimento):
        return None
    n = date.fromisoformat(nascimento)
    return referencia.year - n.year - ((referencia.month, referencia.day) < (n.month, n.day))


def item_indice(c: dict[str, Any], id_publico: str) -> dict[str, Any]:
    """Registro leve do índice da UF. Allowlist."""
    return {
        "id": id_publico,
        "nome_urna": c["nome_urna"],
        "numero": c["numero"],
        "cargo": c["cargo"],
        "partido": c["partido"],
        "genero": _valor(c["genero"]),
        "historico": c["historico"],
        "busca_reeleicao": _valor(c["busca_reeleicao"]),
        "apto": bool(c["apto"]),
    }


def detalhe(
    c: dict[str, Any],
    id_publico: str,
    trajetoria: list[dict[str, Any]],
    redes: list[str],
    cfg: Config,
    fontes_: dict[str, Any],
    gerado_em: str,
) -> dict[str, Any]:
    """Detalhe do candidato. Allowlist: o nome civil só entra como nome exibido, e só
    quando não há nome social (design D8)."""
    centavos = _valor(c["bens_total_centavos"])
    anos = cfg.eleicao.anos_historico
    return {
        "id": id_publico,
        "gerado_em": gerado_em,
        "ano_eleicao": cfg.eleicao.ano,
        "uf": c["uf"],
        "numero": c["numero"],
        "cargo": c["cargo"],
        "nome_urna": c["nome_urna"],
        "nome_exibido": c["nome_exibido"],
        "partido": c["partido"],
        "federacao": _valor(c["federacao"]),
        "perfil": {
            "idade": idade(_valor(c["data_nascimento"]), cfg.eleicao.data_primeiro_turno),
            "genero": _valor(c["genero"]),
            "cor_raca": _valor(c["cor_raca"]),
            "grau_instrucao": _valor(c["grau_instrucao"]),
            "ocupacao": _valor(c["ocupacao"]),
        },
        "situacao": {
            "apto": bool(c["apto"]),
            "descricao": c["situacao_julgamento"],
        },
        "bens": {
            "declarou_bens": _valor(c["declarou_bens"]),
            "total": None if centavos is None else centavos / 100,
            "quantidade": None if centavos is None else int(c["bens_quantidade"]),
        },
        "redes_sociais": redes,
        "historico": {
            "classe": c["historico"],
            "ha_registros_em_verificacao": bool(c["ha_registros_em_verificacao"]),
            "busca_reeleicao": _valor(c["busca_reeleicao"]),
            "cobertura": {"inicio": min(anos), "fim": max(anos)},
        },
        "trajetoria": trajetoria,
        "fontes": fontes_,
    }


def trajetorias(
    vinculos: pd.DataFrame, passado: pd.DataFrame, resultados: pd.DataFrame, anos: tuple[int, ...]
) -> dict[str, list[dict[str, Any]]]:
    """Candidaturas anteriores confirmadas, da mais recente para a mais antiga. Allowlist:
    sem nome, porque o nome de uma eleição anterior pode ser um nome civil antigo."""
    conf = vinculos[(vinculos["nivel"] == CONFIRMADO) & vinculos["ano_passado"].isin(anos)]
    p = passado.merge(resultados, on=["ano", "sq_candidato"])
    t = conf.merge(
        p, left_on=["ano_passado", "sq_passado"], right_on=["ano", "sq_candidato"]
    ).sort_values(["sq_atual", "ano", "cargo"], ascending=[True, False, True])
    saida: dict[str, list[dict[str, Any]]] = {}
    for r in t.itertuples():
        saida.setdefault(r.sq_atual, []).append(
            {
                "ano": int(r.ano),
                "cargo": r.cargo,
                "uf": r.uf,
                "local": r.nm_ue,
                "partido": r.partido,
                "resultado": r.resultado,
            }
        )
    return saida


# --- Escrita ------------------------------------------------------------------------------


def _gravar(caminho: Path, dados: Any) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


def montar_tabela(cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Candidaturas exibíveis com histórico e bens, mais vínculos, passado e resultados."""
    interim = cfg.dir_interim
    ano = cfg.eleicao.ano
    cand = pd.read_parquet(interim / "candidaturas.parquet")
    exib = tse.candidaturas_exibiveis(cand, cfg).drop(columns=["busca_reeleicao"])
    exib = exib.merge(
        pd.read_parquet(interim / "historico.parquet"), on="sq_candidato", how="left"
    ).merge(pd.read_parquet(interim / f"bens_{ano}.parquet"), on="sq_candidato", how="left")
    passado = cand[cand["ano"].isin(cfg.eleicao.anos_historico)]
    return (
        exib,
        pd.read_parquet(interim / "vinculos.parquet"),
        passado,
        pd.read_parquet(interim / "resultados.parquet"),
    )


def resumo(exib: pd.DataFrame, vinculos: pd.DataFrame, gerado_em: str, cfg: Config) -> dict:
    niveis = vinculos.merge(
        exib[["sq_candidato", "uf"]], left_on="sq_atual", right_on="sq_candidato"
    )

    def contagens(uf: str | None) -> dict[str, Any]:
        e = exib if uf is None else exib[exib["uf"] == uf]
        v = niveis if uf is None else niveis[niveis["uf"] == uf]
        return {
            "candidaturas": len(e),
            "aptas": int(e["apto"].sum()),
            "historico": {k: int(n) for k, n in e["historico"].value_counts().items()},
            "vinculos": {k: int(n) for k, n in v["nivel"].value_counts().items()},
        }

    return {
        "gerado_em": gerado_em,
        "ano_eleicao": cfg.eleicao.ano,
        "cobertura": {
            "inicio": min(cfg.eleicao.anos_historico),
            "fim": max(cfg.eleicao.anos_historico),
        },
        "total": contagens(None),
        "ufs": {uf: contagens(uf) for uf in sorted(exib["uf"].unique())},
    }


def gerar(cfg: Config, ufs: tuple[str, ...], log=print) -> None:
    """Grava índice e detalhes das UFs pedidas (e sempre o `BR`), manifesto e resumo."""
    gerado_em = datetime.now().astimezone().isoformat(timespec="seconds")
    manifesto = Manifesto(cfg.dir_raw / "manifest.json")
    fontes_ = fontes(cfg, manifesto)
    exib, vinculos, passado, resultados = montar_tabela(cfg)
    ids = atribuir_ids(exib)
    trajs = trajetorias(vinculos, passado, resultados, cfg.eleicao.anos_historico)
    redes_df = pd.read_parquet(cfg.dir_interim / f"redes_sociais_{cfg.eleicao.ano}.parquet")
    redes = redes_df.groupby("sq_candidato")["url"].apply(list).to_dict()

    ordem = exib.assign(_chave=exib["nome_urna"].map(normalizar_nome)).sort_values(
        ["_chave", "numero"]
    )
    for uf in dict.fromkeys((*ufs, "BR")):
        pasta = cfg.dir_processed / uf
        if pasta.exists():
            shutil.rmtree(pasta)
        linhas = ordem[ordem["uf"] == uf].drop(columns="_chave").to_dict("records")
        indice = []
        for c in linhas:
            id_publico = ids[c["sq_candidato"]]
            indice.append(item_indice(c, id_publico))
            _gravar(
                pasta / "candidatos" / arquivo_detalhe(id_publico),
                detalhe(
                    c,
                    id_publico,
                    trajs.get(c["sq_candidato"], []),
                    redes.get(c["sq_candidato"], []),
                    cfg,
                    fontes_,
                    gerado_em,
                ),
            )
        _gravar(pasta / "indice.json", {"uf": uf, "gerado_em": gerado_em, "candidatos": indice})
        log(f"{uf}: {len(indice)} candidaturas")

    _gravar(
        cfg.dir_processed / "manifesto.json",
        {"gerado_em": gerado_em, "ano_eleicao": cfg.eleicao.ano, "fontes": fontes_},
    )
    _gravar(cfg.dir_processed / "resumo.json", resumo(exib, vinculos, gerado_em, cfg))


# --- Verificação de privacidade -----------------------------------------------------------


def checar_privacidade(cfg: Config) -> list[str]:
    """Procura em data/processed/ CPFs de data/interim/ e nomes civis de quem tem nome
    social. Devolve a lista de problemas (vazia se nada vazou)."""
    cand = pd.read_parquet(cfg.dir_interim / "candidaturas.parquet")
    cpfs = set(cand["cpf"].dropna())
    atual = cand[cand["ano"] == cfg.eleicao.ano]
    # Nome civil protegido: há nome social diferente dele, e ele não é o nome de urna
    # (que a própria pessoa escolheu para aparecer na urna).
    protegido = (
        atual["nome_social"].notna()
        & (atual["nome_civil"] != atual["nome_social"])
        & (atual["nome_civil"] != atual["nome_urna"])
    )
    civis = set(atual.loc[protegido, "nome_civil"].dropna())
    problemas = []
    for arquivo in sorted(cfg.dir_processed.rglob("*")):
        if not arquivo.is_file():
            continue
        texto = arquivo.read_text(encoding="utf-8")
        onze = set(re.findall(r"(?<!\d)\d{11}(?!\d)", texto))
        if onze & cpfs:
            problemas.append(f"{arquivo}: {len(onze & cpfs)} CPF(s)")
        if arquivo.suffix == ".json" and any(nome in texto for nome in civis):
            problemas.append(f"{arquivo}: nome civil de candidatura com nome social")
    return problemas
