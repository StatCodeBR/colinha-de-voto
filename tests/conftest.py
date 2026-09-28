"""Fixtures sintéticas no formato do TSE. Nenhum dado real de pessoa."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

CABECALHO_CAND = [
    "DT_GERACAO", "ANO_ELEICAO", "NR_TURNO", "SG_UF", "SG_UE", "NM_UE", "DS_CARGO",
    "SQ_CANDIDATO", "NR_CANDIDATO", "NM_CANDIDATO", "NM_URNA_CANDIDATO",
    "NM_SOCIAL_CANDIDATO", "NR_CPF_CANDIDATO", "NM_EMAIL", "NR_TITULO_ELEITORAL_CANDIDATO",
    "DT_NASCIMENTO", "SG_PARTIDO", "DS_GENERO", "DS_COR_RACA", "DS_GRAU_INSTRUCAO",
    "DS_OCUPACAO", "DS_SITUACAO_CANDIDATURA", "DS_SIT_TOT_TURNO",
]  # fmt: skip

CABECALHO_COMPL = [
    "ANO_ELEICAO", "SQ_CANDIDATO", "DS_SITUACAO_JULGAMENTO", "DS_SITUACAO_JULGAMENTO_PLEITO",
    "ST_DECLARAR_BENS", "ST_REELEICAO", "NM_MUNICIPIO_NASCIMENTO",
]  # fmt: skip

PADRAO_CAND = {
    "DT_GERACAO": "01/09/2026",
    "NR_TURNO": "1",
    "SG_UF": "RR",
    "SG_UE": "RR",
    "NM_UE": "RORAIMA",
    "DS_CARGO": "DEPUTADO FEDERAL",
    "NM_SOCIAL_CANDIDATO": "#NULO#",
    "NR_CPF_CANDIDATO": "00000000191",
    "NM_EMAIL": "fulano@example.com",
    "NR_TITULO_ELEITORAL_CANDIDATO": "000000000191",
    "DT_NASCIMENTO": "01/02/1980",
    "SG_PARTIDO": "PXX",
    "DS_GENERO": "FEMININO",
    "DS_COR_RACA": "PARDA",
    "DS_GRAU_INSTRUCAO": "SUPERIOR COMPLETO",
    "DS_OCUPACAO": "PROFESSOR DE ENSINO MÉDIO",
    "DS_SITUACAO_CANDIDATURA": "#NE",
    "DS_SIT_TOT_TURNO": "#NULO",
}


def gerar_cpf(base: int) -> str:
    """CPF sintético com dígitos verificadores válidos."""
    d = [int(c) for c in f"{base:09d}"]
    for pesos in (range(10, 1, -1), range(11, 1, -1)):
        d.append(sum(x * p for x, p in zip(d, pesos, strict=False)) * 10 % 11 % 10)
    return "".join(map(str, d))


def linha_cand(ano: int, sq: str, numero: str, nome: str, **extra: str) -> dict[str, str]:
    return {
        **PADRAO_CAND,
        "ANO_ELEICAO": str(ano),
        "SQ_CANDIDATO": sq,
        "NR_CANDIDATO": numero,
        "NM_CANDIDATO": nome,
        "NM_URNA_CANDIDATO": nome.split()[0],
        **extra,
    }


def linha_compl(sq: str, **extra: str) -> dict[str, str]:
    return {
        "ANO_ELEICAO": "2026",
        "SQ_CANDIDATO": sq,
        "DS_SITUACAO_JULGAMENTO": "DEFERIDO",
        "DS_SITUACAO_JULGAMENTO_PLEITO": "DEFERIDO",
        "ST_DECLARAR_BENS": "S",
        "ST_REELEICAO": "#NE",
        "NM_MUNICIPIO_NASCIMENTO": "BOA VISTA",
        **extra,
    }


def escrever_csv(caminho: Path, cabecalho: list[str], linhas: list[dict[str, str]]) -> Path:
    """CSV como o TSE publica: `;`, aspas em tudo, latin-1."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = [";".join(f'"{c}"' for c in cabecalho)]
    texto += [";".join(f'"{linha.get(c, "")}"' for c in cabecalho) for linha in linhas]
    caminho.write_bytes(("\r\n".join(texto) + "\r\n").encode("latin-1"))
    return caminho


def escrever_zip(caminho: Path, arquivos: dict[str, Path]) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho, "w") as z:
        for nome, origem in arquivos.items():
            z.write(origem, nome)
    return caminho


CONFIG_TESTE = """
[projeto]
nome = "Colinha do Voto"
subtitulo = "teste"
url_base = "https://exemplo.invalid"
email_contato = "contato@exemplo.invalid"
url_statcode = "https://exemplo.invalid"
repositorio = ""

[eleicao]
ano = 2026
data_primeiro_turno = "2026-10-04"
anos_historico = [2022]
cargos = ["DEPUTADO FEDERAL", "SENADOR", "PRESIDENTE"]
vagas_colinha = { "DEPUTADO FEDERAL" = 1, "SENADOR" = 2, "PRESIDENTE" = 1 }
ordem_urna = ["DEPUTADO FEDERAL", "SENADOR", "PRESIDENTE"]

[processamento]
ufs = ["RR"]
uf_desenvolvimento = "RR"
"""


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    (tmp_path / "config.toml").write_text(CONFIG_TESTE, encoding="utf-8")
    return tmp_path
