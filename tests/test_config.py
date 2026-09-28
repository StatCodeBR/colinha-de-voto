from pathlib import Path

import pytest

from colinha import config


def test_config_do_projeto_carrega():
    cfg = config.carregar()
    assert cfg.eleicao.ano in cfg.eleicao.anos
    assert cfg.processamento.uf_desenvolvimento in config.UFS
    assert cfg.dir_raw == cfg.raiz / "data" / "raw"


def test_ufs_todas_viram_27(raiz: Path):
    texto = (raiz / "config.toml").read_text().replace('ufs = ["RR"]', 'ufs = "todas"')
    (raiz / "config.toml").write_text(texto)
    assert len(config.carregar(raiz / "config.toml").processamento.ufs) == 27


def test_chave_ausente_da_erro_claro(raiz: Path):
    texto = (raiz / "config.toml").read_text().replace("ano = 2026\n", "")
    (raiz / "config.toml").write_text(texto)
    with pytest.raises(config.ErroConfig, match=r"eleicao\.ano"):
        config.carregar(raiz / "config.toml")


def test_uf_desconhecida(raiz: Path):
    texto = (raiz / "config.toml").read_text().replace('ufs = ["RR"]', 'ufs = ["XX"]')
    (raiz / "config.toml").write_text(texto)
    with pytest.raises(config.ErroConfig, match="XX"):
        config.carregar(raiz / "config.toml")


def test_arquivo_ausente(tmp_path: Path):
    with pytest.raises(config.ErroConfig, match="não encontrado"):
        config.carregar(tmp_path / "config.toml")
