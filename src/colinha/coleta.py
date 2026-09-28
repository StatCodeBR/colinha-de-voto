"""Download com cache e manifesto, e extração dos zips."""

from __future__ import annotations

import hashlib
import json
import re
import time
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

TENTATIVAS = 3
ESPERA_INICIAL_S = 2.0
USER_AGENT = "ColinhaDoVoto/0.1 (StatCode; dados abertos)"


class ErroDownload(Exception):
    """Falha definitiva ao baixar um arquivo."""


@dataclass(frozen=True)
class Fonte:
    """Um arquivo a baixar. `nome` é o nome do arquivo em data/raw/."""

    nome: str
    url: str


def _agora() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


class Manifesto:
    """`data/raw/manifest.json`: URL, `baixado_em`, sha256 e tamanho de cada arquivo."""

    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho
        self.entradas: dict[str, dict] = {}
        if caminho.exists():
            self.entradas = json.loads(caminho.read_text(encoding="utf-8"))

    def get(self, nome: str) -> dict | None:
        return self.entradas.get(nome)

    def registrar(self, nome: str, url: str, arquivo: Path, baixado_em: str) -> None:
        self.entradas[nome] = {
            "url": url,
            "baixado_em": baixado_em,
            "sha256": sha256_arquivo(arquivo),
            "tamanho": arquivo.stat().st_size,
        }
        self.salvar()

    def salvar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.caminho.with_suffix(".json.part")
        tmp.write_text(
            json.dumps(self.entradas, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.caminho)


def _baixar_para(cliente: httpx.Client, url: str, destino: Path) -> None:
    """Baixa em streaming para `destino.part` e só renomeia no fim."""
    parcial = destino.with_name(destino.name + ".part")
    try:
        with cliente.stream("GET", url) as resposta:
            resposta.raise_for_status()
            with parcial.open("wb") as f:
                for bloco in resposta.iter_bytes(1 << 20):
                    f.write(bloco)
        parcial.replace(destino)
    finally:
        parcial.unlink(missing_ok=True)


def baixar(
    fontes: list[Fonte],
    dir_raw: Path,
    *,
    forcar: bool = False,
    cliente: httpx.Client | None = None,
    dormir: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = print,
) -> list[Path]:
    """Baixa as fontes que ainda não estão em cache. Devolve os caminhos locais."""
    dir_raw.mkdir(parents=True, exist_ok=True)
    manifesto = Manifesto(dir_raw / "manifest.json")
    proprio = cliente is None
    cliente = cliente or httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(60.0), follow_redirects=True
    )
    caminhos = []
    try:
        for fonte in fontes:
            destino = dir_raw / fonte.nome
            caminhos.append(destino)
            if not forcar and destino.exists() and manifesto.get(fonte.nome):
                log(f"em cache: {fonte.nome}")
                continue
            log(f"baixando: {fonte.url}")
            erro: Exception | None = None
            for tentativa in range(1, TENTATIVAS + 1):
                try:
                    _baixar_para(cliente, fonte.url, destino)
                    erro = None
                    break
                except httpx.HTTPError as e:
                    erro = e
                    if tentativa < TENTATIVAS:
                        espera = ESPERA_INICIAL_S * 2 ** (tentativa - 1)
                        log(f"  falhou ({e}); nova tentativa em {espera:.0f}s")
                        dormir(espera)
            if erro is not None:
                raise ErroDownload(
                    f"não foi possível baixar {fonte.url} depois de {TENTATIVAS} tentativas: {erro}"
                ) from erro
            manifesto.registrar(fonte.nome, fonte.url, destino, _agora())
    finally:
        if proprio:
            cliente.close()
    return caminhos


def extrair(zip_path: Path, destino: Path, padrao: re.Pattern[str]) -> list[Path]:
    """Extrai do zip só os arquivos cujo nome casa com `padrao`.

    Falha listando o conteúdo do zip se nenhum arquivo casar, para que uma mudança de
    layout do TSE apareça logo.
    """
    destino.mkdir(parents=True, exist_ok=True)
    extraidos = []
    with zipfile.ZipFile(zip_path) as z:
        nomes = [n for n in z.namelist() if not n.endswith("/")]
        for nome in nomes:
            base = Path(nome).name
            if not padrao.fullmatch(base):
                continue
            alvo = destino / base
            if not alvo.exists() or alvo.stat().st_mtime < zip_path.stat().st_mtime:
                parcial = alvo.with_name(alvo.name + ".part")
                with z.open(nome) as origem, parcial.open("wb") as f:
                    while bloco := origem.read(1 << 20):
                        f.write(bloco)
                parcial.replace(alvo)
            extraidos.append(alvo)
    if not extraidos:
        raise ErroDownload(
            f"{zip_path.name}: nenhum arquivo casa com {padrao.pattern}. Conteúdo: {nomes}"
        )
    return sorted(extraidos)
