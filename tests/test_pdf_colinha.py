"""Colinha de bolso em PDF: o gerador em JavaScript roda no Node e o PDF é lido com pypdf."""

import io
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader

GERADOR = Path(__file__).parent / "js" / "gerar_pdf.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node vem do nix develop")

CARTAO = {
    "titulo": "Colinha de São Paulo",
    "vagas": [
        {
            "cargo": "Deputado federal",
            "digitos": 4,
            "numero": "1234",
            "nome": "JOÃO",
            "partido": "AAA",
        },
        {
            "cargo": "Deputado estadual",
            "digitos": 5,
            "numero": "54321",
            "nome": "BIA",
            "partido": "BBB",
        },
        {
            "cargo": "Senador, 1º voto",
            "digitos": 3,
            "numero": "123",
            "nome": "CÉU",
            "partido": "CCC",
        },
        {"cargo": "Senador, 2º voto", "digitos": 3, "numero": None},
        {
            "cargo": "Governador",
            "digitos": 2,
            "numero": "45",
            "nome": "DANI",
            "partido": "DDD",
            "aviso": "Confira no site: a situação mudou",
        },
        {"cargo": "Presidente", "digitos": 2, "numero": "10", "nome": "ŁUKA", "partido": "EEE"},
    ],
    "rodape": ["exemplo.invalid · gerado em 01/10/2026", "Confira os números antes de votar."],
}


def gerar(cartao: dict) -> bytes:
    saida = subprocess.run(
        ["node", str(GERADOR)], input=json.dumps(cartao).encode(), capture_output=True, check=True
    )
    return saida.stdout


@pytest.fixture(scope="module")
def pdf() -> bytes:
    return gerar(CARTAO)


@pytest.fixture(scope="module")
def texto(pdf: bytes) -> str:
    return PdfReader(io.BytesIO(pdf)).pages[0].extract_text()


def test_uma_pagina_a4(pdf: bytes):
    leitor = PdfReader(io.BytesIO(pdf), strict=True)
    assert len(leitor.pages) == 1
    caixa = leitor.pages[0].mediabox
    assert (round(float(caixa.width)), round(float(caixa.height))) == (595, 842)
    assert pdf.isascii()


def test_vagas_na_ordem_da_urna_com_acentos(texto: str):
    posicoes = [texto.index(v["cargo"]) for v in CARTAO["vagas"]]
    assert posicoes == sorted(posicoes)
    assert "Colinha de São Paulo" in texto
    assert "JOÃO · AAA" in texto and "CÉU · CCC" in texto


def test_cada_numero_sai_completo(texto: str):
    sem_espaco = re.sub(r"\s", "", texto)
    for v in CARTAO["vagas"]:
        if v["numero"]:
            assert v["numero"] in sem_espaco, v["numero"]


def test_vaga_vazia_sem_numero_inventado(texto: str):
    trecho = texto.split("Senador, 2º voto")[1].split("Governador")[0]
    assert not re.search(r"\d", trecho)


def test_aviso_no_lugar_do_partido(texto: str):
    assert "DANI · Confira no site: a situação mudou" in texto
    assert "DDD" not in texto


def test_caractere_fora_da_tabela_vira_interrogacao(texto: str):
    assert "?UKA · EEE" in texto


def test_nome_longo_e_cortado_sem_cortar_o_partido():
    cartao = {
        **CARTAO,
        "vagas": [{**CARTAO["vagas"][0], "nome": "NOME MUITO COMPRIDO " * 6, "partido": "PARTIDO"}],
    }
    texto = PdfReader(io.BytesIO(gerar(cartao))).pages[0].extract_text()
    assert "… · PARTIDO" in texto


def test_parenteses_e_barra_escapados():
    cartao = {**CARTAO, "titulo": "Colinha (teste) \\ barra"}
    leitor = PdfReader(io.BytesIO(gerar(cartao)), strict=True)
    assert "Colinha (teste) \\ barra" in leitor.pages[0].extract_text()
    assert leitor.metadata.title == "Colinha (teste) \\ barra"


def test_nada_alem_do_cartao(pdf: bytes):
    leitor = PdfReader(io.BytesIO(pdf))
    assert set(leitor.metadata) == {"/Title", "/Producer"}
    assert b"/URI" not in pdf and b"/JavaScript" not in pdf
