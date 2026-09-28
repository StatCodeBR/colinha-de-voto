import json
import re
from pathlib import Path

import httpx
import pytest

from colinha import coleta
from tests.conftest import escrever_zip

FONTE = coleta.Fonte("arquivo.zip", "https://exemplo.invalid/arquivo.zip")


def cliente(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def baixar(dir_raw: Path, handler, **kw):
    return coleta.baixar(
        [FONTE], dir_raw, cliente=cliente(handler), dormir=lambda s: None, log=lambda m: None, **kw
    )


def test_primeiro_download_registra_manifesto(tmp_path: Path):
    baixar(tmp_path, lambda r: httpx.Response(200, content=b"conteudo"))
    assert (tmp_path / "arquivo.zip").read_bytes() == b"conteudo"
    entrada = json.loads((tmp_path / "manifest.json").read_text())["arquivo.zip"]
    assert entrada["url"] == FONTE.url
    assert entrada["tamanho"] == 8
    assert len(entrada["sha256"]) == 64
    assert entrada["baixado_em"]


def test_cache_evita_novo_download(tmp_path: Path):
    chamadas = []

    def handler(r):
        chamadas.append(r)
        return httpx.Response(200, content=b"x")

    baixar(tmp_path, handler)
    baixar(tmp_path, handler)
    assert len(chamadas) == 1


def test_forcar_baixa_de_novo(tmp_path: Path):
    chamadas = []

    def handler(r):
        chamadas.append(r)
        return httpx.Response(200, content=b"x")

    baixar(tmp_path, handler)
    baixar(tmp_path, handler, forcar=True)
    assert len(chamadas) == 2


def test_arquivo_sem_manifesto_e_baixado(tmp_path: Path):
    (tmp_path / "arquivo.zip").write_bytes(b"velho")
    baixar(tmp_path, lambda r: httpx.Response(200, content=b"novo"))
    assert (tmp_path / "arquivo.zip").read_bytes() == b"novo"


def test_falha_nao_deixa_arquivo_com_nome_final(tmp_path: Path):
    tentativas = []

    def handler(r):
        tentativas.append(r)
        raise httpx.ReadError("conexão caiu", request=r)

    with pytest.raises(coleta.ErroDownload, match=re.escape(FONTE.url)):
        baixar(tmp_path, handler)
    assert len(tentativas) == coleta.TENTATIVAS
    assert not (tmp_path / "arquivo.zip").exists()
    assert not (tmp_path / "arquivo.zip.part").exists()
    assert coleta.Manifesto(tmp_path / "manifest.json").get("arquivo.zip") is None


def test_falha_no_meio_do_stream_nao_deixa_arquivo(tmp_path: Path):
    class StreamQuebrado(httpx.SyncByteStream):
        def __iter__(self):
            yield b"parte"
            raise httpx.ReadError("conexão caiu")

    with pytest.raises(coleta.ErroDownload):
        baixar(tmp_path, lambda r: httpx.Response(200, stream=StreamQuebrado()))
    assert list(tmp_path.glob("arquivo.zip*")) == []


def test_http_403_vira_erro_com_url(tmp_path: Path):
    with pytest.raises(coleta.ErroDownload, match="403"):
        baixar(tmp_path, lambda r: httpx.Response(403))


def test_recupera_na_segunda_tentativa(tmp_path: Path):
    respostas = iter([httpx.Response(503), httpx.Response(200, content=b"ok")])
    baixar(tmp_path, lambda r: next(respostas))
    assert (tmp_path / "arquivo.zip").read_bytes() == b"ok"


def test_extrair_mantem_so_os_csvs_pedidos(tmp_path: Path):
    a = tmp_path / "a.csv"
    a.write_text("x")
    z = escrever_zip(
        tmp_path / "c.zip", {"c_2026_RR.csv": a, "c_2026_BRASIL.csv": a, "leiame.pdf": a}
    )
    extraidos = coleta.extrair(z, tmp_path / "out", re.compile(r"c_2026_(?:RR|BR)\.csv"))
    assert [p.name for p in extraidos] == ["c_2026_RR.csv"]
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["c_2026_RR.csv"]


def test_extrair_sem_arquivo_esperado_lista_conteudo(tmp_path: Path):
    a = tmp_path / "a.csv"
    a.write_text("x")
    z = escrever_zip(tmp_path / "c.zip", {"outro_nome.csv": a})
    with pytest.raises(coleta.ErroDownload, match=r"outro_nome\.csv"):
        coleta.extrair(z, tmp_path / "out", re.compile(r"c_2026_RR\.csv"))
