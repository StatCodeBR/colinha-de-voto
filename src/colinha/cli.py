"""CLI `colinha`: baixar, processar e tudo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from colinha import coleta, config, tse


def _ufs(cfg: config.Config, uf: str | None) -> tuple[str, ...]:
    if uf is None:
        return cfg.processamento.ufs
    uf = uf.upper()
    if uf not in config.UFS:
        raise config.ErroConfig(f"UF desconhecida: {uf}")
    return (uf,)


def _preparar_pastas(cfg: config.Config) -> None:
    for pasta in (cfg.dir_raw, cfg.dir_interim, cfg.dir_processed):
        pasta.mkdir(parents=True, exist_ok=True)


def cmd_baixar(cfg: config.Config, args: argparse.Namespace) -> None:
    # Os arquivos do TSE são nacionais: --uf não reduz o download.
    coleta.baixar(tse.fontes(cfg), cfg.dir_raw, forcar=args.forcar)


def cmd_processar(cfg: config.Config, args: argparse.Namespace) -> None:
    ufs = _ufs(cfg, args.uf)
    tse.processar(cfg)
    print(f"Tabelas normalizadas em {cfg.dir_interim}. UFs pedidas: {', '.join(ufs)}")


def cmd_tudo(cfg: config.Config, args: argparse.Namespace) -> None:
    cmd_baixar(cfg, args)
    cmd_processar(cfg, args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="colinha", description="Colinha do Voto")
    parser.add_argument(
        "--config", type=Path, default=None, help="caminho do config.toml (padrão: raiz)"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    def com_uf(p: argparse.ArgumentParser) -> None:
        p.add_argument("--uf", help="processa só esta UF (ex.: RR)")

    def com_forcar(p: argparse.ArgumentParser) -> None:
        p.add_argument("--forcar", action="store_true", help="ignora o cache e baixa de novo")

    p = sub.add_parser("baixar", help="baixa os dados do TSE para data/raw/")
    com_uf(p)
    com_forcar(p)
    p.set_defaults(func=cmd_baixar)

    p = sub.add_parser("processar", help="normaliza e cruza os dados")
    com_uf(p)
    p.set_defaults(func=cmd_processar)

    p = sub.add_parser("tudo", help="baixar + processar")
    com_uf(p)
    com_forcar(p)
    p.set_defaults(func=cmd_tudo)

    args = parser.parse_args(argv)
    try:
        cfg = config.carregar(args.config)
        _ufs(cfg, args.uf)
        _preparar_pastas(cfg)
        args.func(cfg, args)
    except (config.ErroConfig, coleta.ErroDownload, tse.ErroDados) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
