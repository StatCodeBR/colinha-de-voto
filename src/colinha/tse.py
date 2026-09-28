"""Fontes, leitura e normalização dos dados de candidaturas do TSE."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

from colinha.coleta import Fonte, extrair
from colinha.config import UFS, Config

CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"

# Marcadores de nulo usados pelo TSE (ver docs/fontes.md). "Não divulgável" aparece nos
# campos de candidaturas com dados protegidos por decisão judicial.
MARCADORES_NULO = frozenset({
    "", "#NULO#", "#NULO", "#NE#", "#NE", "-1", "-3", "-4", "NÃO DIVULGÁVEL", "Não divulgável",
})  # fmt: skip

# Colunas lidas dos CSVs de candidaturas e seus nomes normalizados. Só estas colunas são
# lidas: e-mail e título de eleitor nunca entram na memória.
COLUNAS_CAND = {
    "ANO_ELEICAO": "ano",
    "NR_TURNO": "turno",
    "SG_UF": "uf",
    "SG_UE": "sg_ue",
    "NM_UE": "nm_ue",
    "DS_CARGO": "cargo",
    "SQ_CANDIDATO": "sq_candidato",
    "NR_CANDIDATO": "numero",
    "NM_CANDIDATO": "nome_civil",
    "NM_URNA_CANDIDATO": "nome_urna",
    "NM_SOCIAL_CANDIDATO": "nome_social",
    "NR_CPF_CANDIDATO": "cpf",
    "DT_NASCIMENTO": "data_nascimento",
    "SG_PARTIDO": "partido",
    "SG_FEDERACAO": "federacao",
    "DS_GENERO": "genero",
    "DS_COR_RACA": "cor_raca",
    "DS_GRAU_INSTRUCAO": "grau_instrucao",
    "DS_OCUPACAO": "ocupacao",
    "DS_SITUACAO_CANDIDATURA": "situacao_candidatura",
    "DS_SIT_TOT_TURNO": "situacao_totalizacao",
}

# Arquivo complementar do ano da eleição: desde o layout novo, situação de julgamento,
# declaração de bens e reeleição saíram do consulta_cand e vieram para cá.
COLUNAS_COMPLEMENTAR = {
    "SQ_CANDIDATO": "sq_candidato",
    "DS_SITUACAO_JULGAMENTO": "situacao_julgamento",
    "DS_SITUACAO_JULGAMENTO_PLEITO": "situacao_julgamento_pleito",
    "ST_DECLARAR_BENS": "declarou_bens",
    "ST_REELEICAO": "busca_reeleicao",
}
OBRIGATORIAS_COMPLEMENTAR = frozenset({
    "SQ_CANDIDATO", "DS_SITUACAO_JULGAMENTO", "DS_SITUACAO_JULGAMENTO_PLEITO", "ST_DECLARAR_BENS",
})  # fmt: skip

# Obrigatórias em todos os anos (histórico e eleição).
OBRIGATORIAS = frozenset({
    "ANO_ELEICAO", "NR_TURNO", "SG_UF", "SG_UE", "NM_UE", "DS_CARGO", "SQ_CANDIDATO",
    "NR_CANDIDATO", "NM_CANDIDATO", "NM_URNA_CANDIDATO", "SG_PARTIDO",
    "DS_SITUACAO_CANDIDATURA", "DS_SIT_TOT_TURNO",
})  # fmt: skip

# Obrigatórias só no ano da eleição, porque alimentam a página do candidato. O nome social
# é obrigatório: sem a coluna não dá para saber quando esconder o nome civil.
OBRIGATORIAS_ELEICAO = frozenset({
    "NM_SOCIAL_CANDIDATO", "DT_NASCIMENTO", "DS_GENERO", "DS_COR_RACA",
    "DS_GRAU_INSTRUCAO", "DS_OCUPACAO",
})  # fmt: skip

# Situação de julgamento no ano da eleição -> apta. Apta é a candidatura que está na urna e
# pode receber votos, inclusive sub judice (com recurso ou pendente). Valor fora daqui
# interrompe o processamento.
APTIDAO = {
    "DEFERIDO": True,
    "DEFERIDO COM RECURSO": True,
    "DEFERIDO EM PRAZO RECURSAL OU COM RECURSO": True,
    "INDEFERIDO EM PRAZO RECURSAL OU COM RECURSO": True,
    "PEDIDO NÃO CONHECIDO EM PRAZO RECURSAL OU COM RECURSO": True,
    "PENDENTE DE JULGAMENTO": True,
    "INDEFERIDO": False,
    "PEDIDO NÃO CONHECIDO": False,
    "RENÚNCIA": False,
    "CANCELADO": False,
    "FALECIMENTO": False,
}

SIM_NAO = {"S": True, "N": False}


class ErroDados(Exception):
    """Os dados do TSE não têm o formato esperado."""


# --- Fontes -------------------------------------------------------------------------------


def fontes(cfg: Config) -> list[Fonte]:
    """Candidaturas de todos os anos; complementar, bens e redes do ano da eleição."""
    ano = cfg.eleicao.ano
    lista = [
        Fonte(f"consulta_cand_{a}.zip", f"{CDN}/consulta_cand/consulta_cand_{a}.zip")
        for a in cfg.eleicao.anos
    ]
    lista.append(
        Fonte(
            f"consulta_cand_complementar_{ano}.zip",
            f"{CDN}/consulta_cand_complementar/consulta_cand_complementar_{ano}.zip",
        )
    )
    lista.append(Fonte(f"bem_candidato_{ano}.zip", f"{CDN}/bem_candidato/bem_candidato_{ano}.zip"))
    lista.append(
        Fonte(
            f"rede_social_candidato_{ano}.zip",
            f"{CDN}/consulta_cand/rede_social_candidato_{ano}.zip",
        )
    )
    return lista


def padrao_csv(prefixo: str, ano: int) -> re.Pattern[str]:
    """CSVs por UF (e `BR`, de presidente). O consolidado `_BRASIL` fica de fora."""
    ufs = "|".join((*UFS, "BR"))
    return re.compile(rf"{prefixo}_{ano}_(?:{ufs})\.csv", re.IGNORECASE)


def extrair_ano(dir_raw: Path, prefixo: str, ano: int) -> list[Path]:
    return extrair(
        dir_raw / f"{prefixo}_{ano}.zip", dir_raw / f"{prefixo}_{ano}", padrao_csv(prefixo, ano)
    )


# --- Leitura ------------------------------------------------------------------------------


def colunas_do_arquivo(caminho: Path) -> list[str]:
    with caminho.open(encoding="latin-1") as f:
        cabecalho = f.readline().strip()
    return [c.strip().strip('"') for c in cabecalho.split(";")]


def ler_csv_tse(
    caminho: Path,
    ano: int,
    obrigatorias: frozenset[str],
    opcionais: frozenset[str] = frozenset(),
) -> pd.DataFrame:
    """Lê um CSV do TSE só com as colunas pedidas, tudo como texto e nulos convertidos.

    Falha nomeando ano, arquivo e colunas se faltar alguma obrigatória. Opcionais ausentes
    viram colunas nulas.
    """
    presentes = set(colunas_do_arquivo(caminho))
    faltando = sorted(obrigatorias - presentes)
    if faltando:
        raise ErroDados(f"{ano}, {caminho.name}: faltam as colunas obrigatórias {faltando}")
    usar = sorted((obrigatorias | opcionais) & presentes)
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin-1",
        dtype=str,
        usecols=usar,
        keep_default_na=False,
        na_filter=False,
    )
    df = df.apply(lambda s: s.str.strip())
    df = df.mask(df.isin(MARCADORES_NULO))
    for coluna in sorted(opcionais - presentes):
        df[coluna] = pd.Series(pd.NA, index=df.index, dtype="str")
    return df


# --- Normalização -------------------------------------------------------------------------


def _data_iso(serie: pd.Series) -> pd.Series:
    """dd/mm/aaaa -> aaaa-mm-dd. Valores fora do formato viram nulo."""
    datas = pd.to_datetime(serie, format="%d/%m/%Y", errors="coerce")
    return datas.dt.strftime("%Y-%m-%d").where(datas.notna())


def _sim_nao(serie: pd.Series) -> pd.Series:
    return serie.map(SIM_NAO).astype("boolean")


def datas_invalidas(original: pd.Series, convertida: pd.Series) -> int:
    """Quantas datas estavam preenchidas mas não puderam ser lidas."""
    return int((original.notna() & convertida.isna()).sum())


def normalizar_candidaturas(df: pd.DataFrame, ano: int, log=print) -> pd.DataFrame:
    """Renomeia para snake_case, tipa e deixa uma linha por candidatura (último turno)."""
    df = df.rename(columns=COLUNAS_CAND)
    anos = set(df["ano"].dropna().unique())
    if anos - {str(ano)}:
        raise ErroDados(f"{ano}: o arquivo traz linhas de outros anos: {sorted(anos)}")
    df["ano"] = ano
    turnos = pd.to_numeric(df["turno"], errors="coerce")
    if turnos.isna().any():
        ruins = sorted(df.loc[turnos.isna(), "turno"].astype(str).unique())
        raise ErroDados(f"{ano}: NR_TURNO ilegível: {ruins}")
    df["turno"] = turnos.astype("int64")

    nascimento = _data_iso(df["data_nascimento"])
    invalidas = datas_invalidas(df["data_nascimento"], nascimento)
    if invalidas:
        log(f"  aviso: {ano}: {invalidas} datas de nascimento em formato inesperado viraram nulo")
    df["data_nascimento"] = nascimento
    df["nome_exibido"] = df["nome_social"].fillna(df["nome_civil"])
    return deduplicar_turnos(df)


def deduplicar_turnos(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por (`ano`, `sq_candidato`), mantendo a do último turno disputado."""
    return (
        df.sort_values(["ano", "sq_candidato", "turno"], kind="stable")
        .drop_duplicates(["ano", "sq_candidato"], keep="last")
        .reset_index(drop=True)
    )


def juntar_complementar(cand: pd.DataFrame, compl: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta às candidaturas do ano da eleição os campos do arquivo complementar.

    `situacao_julgamento` é a situação no pleito (a decisão mais recente) e, quando ela é
    nula, a situação de julgamento do pedido.
    """
    compl = compl.rename(columns=COLUNAS_COMPLEMENTAR)[list(COLUNAS_COMPLEMENTAR.values())]
    repetidos = compl["sq_candidato"].duplicated()
    if repetidos.any():
        raise ErroDados(f"complementar com SQ_CANDIDATO repetido: {repetidos.sum()} linhas")
    sem_compl = set(cand["sq_candidato"]) - set(compl["sq_candidato"])
    if sem_compl:
        raise ErroDados(f"{len(sem_compl)} candidaturas sem linha no arquivo complementar")
    compl = compl.assign(
        situacao_julgamento=compl["situacao_julgamento_pleito"].fillna(
            compl["situacao_julgamento"]
        ),
        declarou_bens=_sim_nao(compl["declarou_bens"]),
        busca_reeleicao=_sim_nao(compl["busca_reeleicao"]),
    ).drop(columns="situacao_julgamento_pleito")
    return cand.merge(compl, on="sq_candidato", how="left", validate="one_to_one")


def marcar_aptidao(df: pd.DataFrame) -> pd.DataFrame:
    """Campo `apto` a partir da situação de julgamento. Falha com valores desconhecidos."""
    situacao = df["situacao_julgamento"]
    desconhecidos = sorted(set(situacao.dropna()) - set(APTIDAO))
    if desconhecidos or situacao.isna().any():
        extra = ["(nulo)"] if situacao.isna().any() else []
        raise ErroDados(f"situação de julgamento sem mapeamento: {desconhecidos + extra}")
    df = df.copy()
    df["apto"] = situacao.map(APTIDAO).astype(bool)
    return df


def candidaturas_exibiveis(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Candidaturas do ano da eleição aos cargos titulares configurados, com `apto`."""
    doano = df[df["ano"] == cfg.eleicao.ano]
    ausentes = sorted(set(cfg.eleicao.cargos) - set(doano["cargo"].dropna()))
    if ausentes:
        raise ErroDados(
            f"{cfg.eleicao.ano}: cargos do config.toml sem nenhuma candidatura: {ausentes}. "
            f"Cargos no arquivo: {sorted(doano['cargo'].dropna().unique())}"
        )
    return marcar_aptidao(doano[doano["cargo"].isin(cfg.eleicao.cargos)]).reset_index(drop=True)


def carregar_candidaturas(csvs: list[Path], ano: int, eleicao: bool, log=print) -> pd.DataFrame:
    obrigatorias = OBRIGATORIAS | (OBRIGATORIAS_ELEICAO if eleicao else frozenset())
    opcionais = frozenset(COLUNAS_CAND) - obrigatorias
    partes = [ler_csv_tse(c, ano, obrigatorias, opcionais) for c in csvs]
    return normalizar_candidaturas(pd.concat(partes, ignore_index=True), ano, log=log)


# --- Bens e redes sociais -----------------------------------------------------------------


def valor_em_centavos(texto: str) -> int:
    """'1.234,56' ou '1234,56' ou '1234.56' -> 123456."""
    t = texto.strip()
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        valor = Decimal(t)
    except InvalidOperation as e:
        raise ErroDados(f"valor de bem ilegível: {texto!r}") from e
    return int((valor * 100).to_integral_value())


def total_bens(df_bens: pd.DataFrame) -> pd.DataFrame:
    """Soma dos bens por candidatura, em centavos. Quem não tem bens não aparece aqui."""
    if df_bens["VR_BEM_CANDIDATO"].isna().any():
        raise ErroDados("arquivo de bens com valor nulo; conferir antes de somar")
    centavos = df_bens["VR_BEM_CANDIDATO"].map(valor_em_centavos)
    return (
        pd.DataFrame({"sq_candidato": df_bens["SQ_CANDIDATO"], "centavos": centavos})
        .groupby("sq_candidato", as_index=False)
        .agg(bens_total_centavos=("centavos", "sum"), bens_quantidade=("centavos", "size"))
    )


def redes_sociais(df_redes: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por rede social informada: `sq_candidato`, `url`."""
    return (
        df_redes.rename(columns={"SQ_CANDIDATO": "sq_candidato", "DS_URL": "url"})[
            ["sq_candidato", "url"]
        ]
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )


# --- Processamento ------------------------------------------------------------------------


def processar(cfg: Config, log=print) -> None:
    """Extrai os zips e grava as tabelas normalizadas em data/interim/.

    O histórico é sempre nacional: um candidato de uma UF pode ter concorrido em outra, e a
    unicidade da chave de vínculo só vale olhando todas as UFs.
    """
    raw, interim = cfg.dir_raw, cfg.dir_interim
    interim.mkdir(parents=True, exist_ok=True)
    ano = cfg.eleicao.ano

    compl = pd.concat(
        [
            ler_csv_tse(
                c,
                ano,
                OBRIGATORIAS_COMPLEMENTAR,
                frozenset(COLUNAS_COMPLEMENTAR) - OBRIGATORIAS_COMPLEMENTAR,
            )
            for c in extrair_ano(raw, "consulta_cand_complementar", ano)
        ],
        ignore_index=True,
    )

    tabelas = []
    for a in cfg.eleicao.anos:
        csvs = extrair_ano(raw, "consulta_cand", a)
        df = carregar_candidaturas(csvs, a, eleicao=(a == ano), log=log)
        if a == ano:
            df = juntar_complementar(df, compl)
        log(f"{a}: {len(df)} candidaturas em {len(csvs)} arquivos")
        tabelas.append(df)
    candidaturas = pd.concat(tabelas, ignore_index=True)
    candidaturas_exibiveis(candidaturas, cfg)  # valida cargos e situação antes de gravar
    candidaturas.to_parquet(interim / "candidaturas.parquet", index=False)

    bens = [
        ler_csv_tse(c, ano, frozenset({"SQ_CANDIDATO", "VR_BEM_CANDIDATO"}))
        for c in extrair_ano(raw, "bem_candidato", ano)
    ]
    total_bens(pd.concat(bens, ignore_index=True)).to_parquet(
        interim / f"bens_{ano}.parquet", index=False
    )

    redes = [
        ler_csv_tse(c, ano, frozenset({"SQ_CANDIDATO", "DS_URL"}))
        for c in extrair_ano(raw, "rede_social_candidato", ano)
    ]
    redes_sociais(pd.concat(redes, ignore_index=True)).to_parquet(
        interim / f"redes_sociais_{ano}.parquet", index=False
    )
