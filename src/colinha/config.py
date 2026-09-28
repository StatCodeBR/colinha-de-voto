"""Leitura do config.toml para dataclasses tipadas."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

UFS = (
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
)  # fmt: skip

RAIZ_PADRAO = Path(__file__).resolve().parents[2]


class ErroConfig(Exception):
    """Erro de configuração, com mensagem pronta para o usuário."""


@dataclass(frozen=True)
class Projeto:
    nome: str
    subtitulo: str
    url_base: str
    email_contato: str
    url_statcode: str
    repositorio: str


@dataclass(frozen=True)
class Eleicao:
    ano: int
    data_primeiro_turno: date
    anos_historico: tuple[int, ...]
    cargos: tuple[str, ...]
    vagas_colinha: dict[str, int]
    ordem_urna: tuple[str, ...]

    @property
    def anos(self) -> tuple[int, ...]:
        """Ano da eleição seguido dos anos de histórico."""
        return (self.ano, *self.anos_historico)


@dataclass(frozen=True)
class Processamento:
    ufs: tuple[str, ...]
    uf_desenvolvimento: str


@dataclass(frozen=True)
class Config:
    projeto: Projeto
    eleicao: Eleicao
    processamento: Processamento
    raiz: Path

    @property
    def dir_raw(self) -> Path:
        return self.raiz / "data" / "raw"

    @property
    def dir_interim(self) -> Path:
        return self.raiz / "data" / "interim"

    @property
    def dir_processed(self) -> Path:
        return self.raiz / "data" / "processed"

    @property
    def dir_manual(self) -> Path:
        return self.raiz / "data" / "manual"


def _secao(dados: dict[str, Any], nome: str) -> dict[str, Any]:
    valor = dados.get(nome)
    if not isinstance(valor, dict):
        raise ErroConfig(f"config.toml: falta a seção [{nome}]")
    return valor


def _chave(secao: dict[str, Any], nome_secao: str, chave: str, tipo: type) -> Any:
    if chave not in secao:
        raise ErroConfig(f"config.toml: falta a chave '{nome_secao}.{chave}'")
    valor = secao[chave]
    if not isinstance(valor, tipo):
        raise ErroConfig(
            f"config.toml: '{nome_secao}.{chave}' deveria ser {tipo.__name__}, "
            f"mas é {type(valor).__name__}"
        )
    return valor


def _ufs(valor: str | list[str]) -> tuple[str, ...]:
    if valor == "todas":
        return UFS
    if isinstance(valor, list):
        desconhecidas = [uf for uf in valor if uf not in UFS]
        if desconhecidas:
            raise ErroConfig(
                f"config.toml: UFs desconhecidas em 'processamento.ufs': {desconhecidas}"
            )
        return tuple(valor)
    raise ErroConfig("config.toml: 'processamento.ufs' deve ser \"todas\" ou uma lista de UFs")


def carregar(caminho: Path | None = None) -> Config:
    """Lê o config.toml. Por padrão, o da raiz do projeto."""
    caminho = caminho or RAIZ_PADRAO / "config.toml"
    try:
        with caminho.open("rb") as f:
            dados = tomllib.load(f)
    except FileNotFoundError as e:
        raise ErroConfig(f"config.toml não encontrado em {caminho}") from e
    except tomllib.TOMLDecodeError as e:
        raise ErroConfig(f"config.toml inválido: {e}") from e

    p = _secao(dados, "projeto")
    projeto = Projeto(
        nome=_chave(p, "projeto", "nome", str),
        subtitulo=_chave(p, "projeto", "subtitulo", str),
        url_base=_chave(p, "projeto", "url_base", str),
        email_contato=_chave(p, "projeto", "email_contato", str),
        url_statcode=_chave(p, "projeto", "url_statcode", str),
        repositorio=_chave(p, "projeto", "repositorio", str),
    )

    e = _secao(dados, "eleicao")
    data_turno = _chave(e, "eleicao", "data_primeiro_turno", str)
    try:
        data_primeiro_turno = date.fromisoformat(data_turno)
    except ValueError as erro:
        raise ErroConfig(
            f"config.toml: 'eleicao.data_primeiro_turno' não é uma data AAAA-MM-DD: {data_turno}"
        ) from erro
    eleicao = Eleicao(
        ano=_chave(e, "eleicao", "ano", int),
        data_primeiro_turno=data_primeiro_turno,
        anos_historico=tuple(_chave(e, "eleicao", "anos_historico", list)),
        cargos=tuple(_chave(e, "eleicao", "cargos", list)),
        vagas_colinha=dict(_chave(e, "eleicao", "vagas_colinha", dict)),
        ordem_urna=tuple(_chave(e, "eleicao", "ordem_urna", list)),
    )
    if set(eleicao.ordem_urna) != set(eleicao.cargos) or set(eleicao.vagas_colinha) != set(
        eleicao.cargos
    ):
        raise ErroConfig(
            "config.toml: 'eleicao.ordem_urna' e 'eleicao.vagas_colinha' precisam ter os "
            "mesmos cargos de 'eleicao.cargos'"
        )

    pr = _secao(dados, "processamento")
    uf_dev = _chave(pr, "processamento", "uf_desenvolvimento", str)
    if uf_dev not in UFS:
        raise ErroConfig(f"config.toml: 'processamento.uf_desenvolvimento' desconhecida: {uf_dev}")
    if "ufs" not in pr:
        raise ErroConfig("config.toml: falta a chave 'processamento.ufs'")
    processamento = Processamento(ufs=_ufs(pr["ufs"]), uf_desenvolvimento=uf_dev)

    return Config(
        projeto=projeto,
        eleicao=eleicao,
        processamento=processamento,
        raiz=caminho.resolve().parent,
    )
