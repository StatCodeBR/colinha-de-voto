"""Vínculo entre candidaturas do ano da eleição e de anos anteriores, e classificação do
histórico. Regras em openspec/changes/01-add-pipeline-tse/design.md (D4 a D6)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from colinha.config import Config
from colinha.tse import ErroDados

CONFIRMADO, PROVAVEL, AMBIGUO = "confirmado", "provavel", "ambiguo"

# Resultado do último turno (DS_SIT_TOT_TURNO normalizado) -> resultado publicado.
RESULTADOS = {
    "ELEITO": "eleito",
    "ELEITO POR QP": "eleito",
    "ELEITO POR MEDIA": "eleito",
    "SUPLENTE": "suplente",
    "NAO ELEITO": "nao_eleito",
    "2O TURNO": "segundo_turno_sem_resultado",
}

COLUNAS_MANUAL = [
    "sq_candidato_atual",
    "ano_passado",
    "sq_candidato_passado",
    "decisao",
    "revisado_por",
    "revisado_em",
    "nota",
]

# Partículas ignoradas ao comparar palavras de nomes.
PARTICULAS = frozenset({"DA", "DAS", "DE", "DO", "DOS", "E"})

_MARCAS = re.compile(r"[̀-ͯ]")
_NAO_LETRA = re.compile(r"[^A-Z]+")
_ESPACOS = re.compile(r"\s+")


# --- Normalização -------------------------------------------------------------------------


def normalizar_nome(nome: str) -> str:
    """Maiúsculas, sem acento, só letras e espaços, espaços colapsados."""
    texto = _MARCAS.sub("", unicodedata.normalize("NFKD", nome)).upper()
    return _NAO_LETRA.sub(" ", texto).strip()


def normalizar_nomes(nomes: pd.Series) -> pd.Series:
    """`normalizar_nome` vetorizado, para as tabelas inteiras."""
    return (
        nomes.str.normalize("NFKD")
        .str.replace(_MARCAS, "", regex=True)
        .str.upper()
        .str.replace(_NAO_LETRA, " ", regex=True)
        .str.strip()
    )


def normalizar_texto(texto: str) -> str:
    """Maiúsculas, sem acento, espaços colapsados; mantém dígitos ("2º" vira "2O")."""
    sem_acento = _MARCAS.sub("", unicodedata.normalize("NFKD", texto)).upper()
    return _ESPACOS.sub(" ", sem_acento).strip()


def cpf_valido(cpfs: pd.Series) -> pd.Series:
    """11 dígitos, não todos iguais e com dígitos verificadores corretos."""
    valido = pd.Series(False, index=cpfs.index)
    formato = cpfs.fillna("").str.fullmatch(r"\d{11}")
    if not formato.any():
        return valido
    d = np.array([list(map(int, c)) for c in cpfs[formato]])
    r1 = (d[:, :9] @ np.arange(10, 1, -1)) * 10 % 11 % 10
    r2 = (d[:, :10] @ np.arange(11, 1, -1)) * 10 % 11 % 10
    repetido = (d == d[:, :1]).all(axis=1)
    valido[formato] = (r1 == d[:, 9]) & (r2 == d[:, 10]) & ~repetido
    return valido


def nomes_compativeis(a: str, b: str) -> bool:
    """Os nomes normalizados têm ao menos uma palavra em comum, fora as partículas."""
    return bool((set(a.split()) - PARTICULAS) & (set(b.split()) - PARTICULAS))


# --- Resultado ----------------------------------------------------------------------------


def mapear_resultado(df: pd.DataFrame) -> pd.Series:
    """`situacao_totalizacao` -> resultado. Falha listando valores fora do mapeamento."""
    normal = df["situacao_totalizacao"].map(normalizar_texto, na_action="ignore")
    desconhecidos = normal.notna() & ~normal.isin(list(RESULTADOS))
    if desconhecidos.any():
        valores = (
            df.loc[desconhecidos, ["ano", "situacao_totalizacao"]]
            .drop_duplicates()
            .sort_values(["ano", "situacao_totalizacao"])
            .itertuples(index=False)
        )
        lista = ", ".join(f"{ano}: {valor!r}" for ano, valor in valores)
        raise ErroDados(f"resultado sem mapeamento: {lista}")
    return normal.map(RESULTADOS).fillna("sem_resultado")


# --- Vínculo ------------------------------------------------------------------------------


def _preparar(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sq": df["sq_candidato"],
            "ano": df["ano"],
            "uf": df["uf"],
            "nome": normalizar_nomes(df["nome_civil"]),
            "nascimento": df["data_nascimento"],
            "cpf": df["cpf"].where(cpf_valido(df["cpf"])),
        }
    ).reset_index(drop=True)


def _pares(atual: pd.DataFrame, passado: pd.DataFrame, chave: list[str]) -> pd.DataFrame:
    return atual.merge(passado, on=chave, suffixes=("_atual", "_passado"))


def vincular(atual: pd.DataFrame, passado: pd.DataFrame) -> pd.DataFrame:
    """Pares (candidatura atual, candidatura anterior) com nível e regra.

    `atual` e `passado` são candidaturas normalizadas (ver `tse`); `passado` pode ter
    vários anos. A unicidade da chave nome + nascimento é contada no ano da eleição e em
    cada ano anterior.
    """
    a = _preparar(atual)
    p = _preparar(passado)
    colunas = ["sq_atual", "ano_passado", "sq_passado", "nivel", "regra"]

    # 1. CPF válido e igual dos dois lados. Se nem o nome (nenhuma palavra em comum) nem o
    # nascimento batem, o CPF provavelmente foi digitado errado em um dos anos: vai para
    # revisão. Só nascimento igual cobre quem mudou de nome civil.
    por_cpf = _pares(a.dropna(subset=["cpf"]), p.dropna(subset=["cpf"]), ["cpf"])
    compativel = [
        nomes_compativeis(x, y) or (pd.notna(nx) and nx == ny)
        for x, y, nx, ny in zip(
            por_cpf["nome_atual"],
            por_cpf["nome_passado"],
            por_cpf["nascimento_atual"],
            por_cpf["nascimento_passado"],
            strict=True,
        )
    ]
    por_cpf = por_cpf.assign(
        nivel=np.where(compativel, CONFIRMADO, AMBIGUO),
        regra=np.where(compativel, "cpf", "cpf_divergente"),
    )

    # 2. Nome + nascimento, só quando algum lado não tem CPF (se os dois têm, o CPF decide).
    chave = ["nome", "nascimento"]
    a_n = a.dropna(subset=chave)
    p_n = p.dropna(subset=chave)
    rep_atual = a_n.groupby(chave)["sq"].transform("size")
    rep_passado = p_n.groupby(["ano", *chave])["sq"].transform("size")
    a_n = a_n.assign(rep_atual=rep_atual)
    p_n = p_n.assign(rep_passado=rep_passado)
    por_nome = _pares(a_n, p_n, chave)
    por_nome = por_nome[por_nome["cpf_atual"].isna() | por_nome["cpf_passado"].isna()]
    unico = (por_nome["rep_atual"] == 1) & (por_nome["rep_passado"] == 1)
    por_nome = por_nome.assign(nivel=np.where(unico, CONFIRMADO, AMBIGUO), regra="nome_nascimento")

    # 3. Mesmo nome e UF, sem nascimento para comparar em algum dos lados.
    sem_nasc = pd.concat(
        [
            _pares(a[a["nascimento"].isna()], p, ["nome", "uf"]),
            _pares(a, p[p["nascimento"].isna()], ["nome", "uf"]),
        ]
    )
    sem_nasc = sem_nasc[sem_nasc["cpf_atual"].isna() | sem_nasc["cpf_passado"].isna()]
    sem_nasc = sem_nasc.assign(nivel=PROVAVEL, regra="nome_uf")

    todos = pd.concat([df[colunas] for df in (por_cpf, por_nome, sem_nasc)], ignore_index=True)
    # Um par encontrado por mais de uma regra fica com a mais forte (ordem acima).
    todos = todos.drop_duplicates(["sq_atual", "ano_passado", "sq_passado"])
    return todos.astype({"ano_passado": "int64"}).reset_index(drop=True)


# --- Correções manuais --------------------------------------------------------------------


def ler_manual(caminho: Path) -> pd.DataFrame:
    """`data/manual/vinculos.csv`. Arquivo ausente equivale a nenhuma correção."""
    if not caminho.exists():
        return pd.DataFrame(columns=COLUNAS_MANUAL, dtype="str")
    df = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    if list(df.columns) != COLUNAS_MANUAL:
        raise ErroDados(f"{caminho.name}: cabeçalho deveria ser {','.join(COLUNAS_MANUAL)}")
    return df


def aplicar_manual(
    vinculos: pd.DataFrame, manual: pd.DataFrame, atual: pd.DataFrame, passado: pd.DataFrame
) -> pd.DataFrame:
    """Aplica as decisões humanas depois das regras: confirmar ou rejeitar um par."""
    if manual.empty:
        return vinculos
    m = manual.assign(decisao=manual["decisao"].str.strip().str.lower())
    ruins = sorted(set(m["decisao"]) - {"confirmar", "rejeitar"})
    if ruins:
        raise ErroDados(f"vinculos.csv: decisão desconhecida {ruins} (use confirmar ou rejeitar)")
    try:
        m["ano_passado"] = m["ano_passado"].astype("int64")
    except ValueError as e:
        raise ErroDados(f"vinculos.csv: ano_passado inválido: {e}") from e
    par = ["sq_candidato_atual", "ano_passado", "sq_candidato_passado"]
    conflito = m.groupby(par)["decisao"].nunique() > 1
    if conflito.any():
        pares = list(conflito[conflito].index)
        raise ErroDados(f"vinculos.csv: par confirmado e rejeitado ao mesmo tempo: {pares}")

    m = m.drop_duplicates(par).rename(
        columns={"sq_candidato_atual": "sq_atual", "sq_candidato_passado": "sq_passado"}
    )
    chave = ["sq_atual", "ano_passado", "sq_passado"]

    existentes_atual = set(atual["sq_candidato"])
    existentes_passado = set(zip(passado["ano"], passado["sq_candidato"], strict=True))
    confirmar = m[m["decisao"] == "confirmar"]
    inexistentes = [
        (r.sq_atual, r.ano_passado, r.sq_passado)
        for r in confirmar.itertuples()
        if r.sq_atual not in existentes_atual
        or (r.ano_passado, r.sq_passado) not in existentes_passado
    ]
    if inexistentes:
        raise ErroDados(
            f"vinculos.csv: confirmação de candidaturas que não existem: {inexistentes}"
        )

    restantes = vinculos.merge(m[chave], on=chave, how="left", indicator=True)
    restantes = restantes[restantes["_merge"] == "left_only"].drop(columns="_merge")
    manuais = confirmar[chave].assign(nivel=CONFIRMADO, regra="manual")
    return pd.concat([restantes, manuais], ignore_index=True)


# --- Histórico ----------------------------------------------------------------------------


def classificar(
    sq_atuais: pd.Series, vinculos: pd.DataFrame, resultados: pd.DataFrame, anos: tuple[int, ...]
) -> pd.DataFrame:
    """Classe do histórico de cada candidatura atual, só com anos da janela.

    `resultados` tem `ano`, `sq_candidato` e `resultado` das candidaturas anteriores.
    """
    v = vinculos[vinculos["ano_passado"].isin(anos)]
    confirmados = v[v["nivel"] == CONFIRMADO].merge(
        resultados.rename(columns={"ano": "ano_passado", "sq_candidato": "sq_passado"}),
        on=["ano_passado", "sq_passado"],
        how="left",
    )
    com_confirmado = set(confirmados["sq_atual"])
    eleitos = set(confirmados.loc[confirmados["resultado"] == "eleito", "sq_atual"])
    pendentes = set(v.loc[v["nivel"] != CONFIRMADO, "sq_atual"])

    def classe(sq: str) -> str:
        if sq in eleitos:
            return "eleito"
        if sq in com_confirmado:
            return "concorreu"
        if sq in pendentes:
            return "em_verificacao"
        return "sem_registro"

    return pd.DataFrame(
        {
            "sq_candidato": sq_atuais.to_numpy(),
            "historico": [classe(sq) for sq in sq_atuais],
            "ha_registros_em_verificacao": [
                sq in com_confirmado and sq in pendentes for sq in sq_atuais
            ],
        }
    )


# --- Revisão ------------------------------------------------------------------------------

_EVIDENCIAS = ["ano", "uf", "nm_ue", "cargo", "numero", "partido", "nome_civil", "data_nascimento"]


def revisao(vinculos: pd.DataFrame, atual: pd.DataFrame, passado: pd.DataFrame) -> pd.DataFrame:
    """Pares pendentes com as evidências dos dois lados. Sem CPF: só se ele foi informado."""
    pend = vinculos[vinculos["nivel"] != CONFIRMADO]

    def lado(df: pd.DataFrame, sufixo: str) -> pd.DataFrame:
        ev = df[["sq_candidato", *_EVIDENCIAS]].assign(
            nome_normalizado=normalizar_nomes(df["nome_civil"]),
            cpf_informado=np.where(cpf_valido(df["cpf"]), "sim", "não"),
        )
        return ev.add_suffix(sufixo)

    rev = pend.merge(
        lado(atual, "_atual"), left_on="sq_atual", right_on="sq_candidato_atual"
    ).merge(
        lado(passado, "_passado"),
        left_on=["ano_passado", "sq_passado"],
        right_on=["ano_passado", "sq_candidato_passado"],
    )
    colunas = [
        "uf_atual", "nivel", "regra", "sq_candidato_atual", "ano_passado",
        "sq_candidato_passado", "uf_passado",
        *(f"{c}_{lado}" for c in ["nome_civil", "nome_normalizado", "data_nascimento",
                                   "cpf_informado", "nm_ue", "cargo", "numero", "partido"]
          for lado in ("atual", "passado")),
    ]  # fmt: skip
    return rev[colunas].sort_values(["uf_atual", "nome_normalizado_atual", "ano_passado"])


# --- Execução -----------------------------------------------------------------------------


def executar(cfg: Config, log=print) -> None:
    """Lê as candidaturas normalizadas, vincula, aplica correções e classifica."""
    cand = pd.read_parquet(cfg.dir_interim / "candidaturas.parquet")
    atual = cand[cand["ano"] == cfg.eleicao.ano]
    passado = cand[cand["ano"].isin(cfg.eleicao.anos_historico)]
    resultados = passado[["ano", "sq_candidato"]].assign(resultado=mapear_resultado(passado))

    vinculos = vincular(atual, passado)
    vinculos = aplicar_manual(vinculos, ler_manual(cfg.dir_manual / "vinculos.csv"), atual, passado)
    historico = classificar(atual["sq_candidato"], vinculos, resultados, cfg.eleicao.anos_historico)

    vinculos.to_parquet(cfg.dir_interim / "vinculos.parquet", index=False)
    historico.to_parquet(cfg.dir_interim / "historico.parquet", index=False)
    resultados.to_parquet(cfg.dir_interim / "resultados.parquet", index=False)
    cfg.dir_processed.mkdir(parents=True, exist_ok=True)
    revisao(vinculos, atual, passado).to_csv(
        cfg.dir_processed / "revisao_vinculos.csv", index=False, encoding="utf-8"
    )

    niveis = vinculos["nivel"].value_counts().to_dict()
    classes = historico["historico"].value_counts().to_dict()
    log(f"vínculos: {niveis}")
    log(f"histórico: {classes}")
