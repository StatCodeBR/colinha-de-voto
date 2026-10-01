from pathlib import Path

import pandas as pd
import pytest

from colinha import config, tse
from tests.conftest import (
    CABECALHO_CAND,
    CABECALHO_COMPL,
    escrever_csv,
    escrever_zip,
    gerar_cpf,
    linha_cand,
    linha_compl,
)


def carregar(tmp_path: Path, linhas, ano=2026, eleicao=True, cabecalho=CABECALHO_CAND):
    csv = escrever_csv(tmp_path / f"consulta_cand_{ano}_RR.csv", cabecalho, linhas)
    return tse.carregar_candidaturas([csv], ano, eleicao=eleicao, log=lambda m: None)


# --- Leitura ------------------------------------------------------------------------------


@pytest.mark.parametrize("marcador", ["#NULO#", "#NE#", "#NE", "-1", "-3", "-4", ""])
def test_marcador_de_nulo_vira_nulo(tmp_path: Path, marcador: str):
    df = carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA", NR_CPF_CANDIDATO=marcador)])
    assert pd.isna(df.loc[0, "cpf"])


def test_zeros_a_esquerda_preservados(tmp_path: Path):
    df = carregar(tmp_path, [linha_cand(2026, "0100", "0123", "ANA")])
    assert df.loc[0, "sq_candidato"] == "0100"
    assert df.loc[0, "numero"] == "0123"
    assert df.loc[0, "cpf"] == "00000000191"


def test_acentos_latin1(tmp_path: Path):
    df = carregar(tmp_path, [linha_cand(2026, "1", "1111", "JOÃO DA CONCEIÇÃO")])
    assert df.loc[0, "nome_civil"] == "JOÃO DA CONCEIÇÃO"


def test_coluna_obrigatoria_ausente_nomeia_ano_arquivo_e_coluna(tmp_path: Path):
    cabecalho = [c for c in CABECALHO_CAND if c != "DS_CARGO"]
    with pytest.raises(tse.ErroDados, match=r"2026.*consulta_cand_2026_RR\.csv.*DS_CARGO"):
        carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA")], cabecalho=cabecalho)


def test_coluna_do_ano_da_eleicao_opcional_no_historico(tmp_path: Path):
    cabecalho = [c for c in CABECALHO_CAND if c not in {"NM_SOCIAL_CANDIDATO", "DT_NASCIMENTO"}]
    df = carregar(
        tmp_path, [linha_cand(2014, "1", "11", "ANA")], ano=2014, eleicao=False, cabecalho=cabecalho
    )
    assert pd.isna(df.loc[0, "nome_social"])
    assert pd.isna(df.loc[0, "data_nascimento"])
    assert df.loc[0, "nome_exibido"] == "ANA"


def test_nome_social_obrigatorio_no_ano_da_eleicao(tmp_path: Path):
    cabecalho = [c for c in CABECALHO_CAND if c != "NM_SOCIAL_CANDIDATO"]
    with pytest.raises(tse.ErroDados, match="NM_SOCIAL_CANDIDATO"):
        carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA")], cabecalho=cabecalho)


def test_email_e_titulo_nunca_sao_lidos(tmp_path: Path):
    df = carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA")])
    valores = df.astype(str).to_numpy().ravel().tolist()
    assert "fulano@example.com" not in valores
    assert "000000000191" not in valores
    assert not {"NM_EMAIL", "NR_TITULO_ELEITORAL_CANDIDATO"} & set(df.columns)


def test_data_de_nascimento_em_iso(tmp_path: Path):
    df = carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA", DT_NASCIMENTO="09/03/1975")])
    assert df.loc[0, "data_nascimento"] == "1975-03-09"


def test_turno_ilegivel_falha(tmp_path: Path):
    with pytest.raises(tse.ErroDados, match="NR_TURNO"):
        carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA", NR_TURNO="X")])


def test_linhas_de_outro_ano_falham(tmp_path: Path):
    with pytest.raises(tse.ErroDados, match="outros anos"):
        carregar(tmp_path, [linha_cand(2022, "1", "1111", "ANA")], ano=2026)


# --- Normalização -------------------------------------------------------------------------


def test_segundo_turno_mantem_resultado_do_segundo(tmp_path: Path):
    linhas = [
        linha_cand(2022, "9", "15", "BIA", NR_TURNO="2", DS_SIT_TOT_TURNO="ELEITO"),
        linha_cand(2022, "9", "15", "BIA", NR_TURNO="1", DS_SIT_TOT_TURNO="2º TURNO"),
        linha_cand(2022, "8", "16", "CAIO", NR_TURNO="1", DS_SIT_TOT_TURNO="NÃO ELEITO"),
    ]
    df = carregar(tmp_path, linhas, ano=2022, eleicao=False)
    assert len(df) == 2
    bia = df[df["sq_candidato"] == "9"].iloc[0]
    assert bia["turno"] == 2
    assert bia["situacao_totalizacao"] == "ELEITO"


def test_nome_social_e_o_nome_exibido(tmp_path: Path):
    df = carregar(
        tmp_path,
        [
            linha_cand(2026, "1", "1111", "NOME CIVIL", NM_SOCIAL_CANDIDATO="NOME SOCIAL"),
            linha_cand(2026, "2", "2222", "OUTRA PESSOA"),
        ],
    )
    assert df.set_index("sq_candidato").loc["1", "nome_exibido"] == "NOME SOCIAL"
    assert df.set_index("sq_candidato").loc["2", "nome_exibido"] == "OUTRA PESSOA"


# --- Arquivo complementar -----------------------------------------------------------------


def ler_compl(tmp_path: Path, linhas) -> pd.DataFrame:
    csv = escrever_csv(tmp_path / "compl.csv", CABECALHO_COMPL, linhas)
    return tse.ler_csv_tse(
        csv,
        2026,
        tse.OBRIGATORIAS_COMPLEMENTAR,
        frozenset(tse.COLUNAS_COMPLEMENTAR) - tse.OBRIGATORIAS_COMPLEMENTAR,
    )


def test_complementar_traz_bens_reeleicao_e_situacao(tmp_path: Path):
    cand = carregar(
        tmp_path,
        [linha_cand(2026, "1", "1111", "ANA"), linha_cand(2026, "2", "2222", "BIA")],
    )
    compl = ler_compl(
        tmp_path,
        [
            linha_compl("1", ST_DECLARAR_BENS="N", ST_REELEICAO="S"),
            linha_compl("2", ST_DECLARAR_BENS="Não divulgável"),
        ],
    )
    df = tse.juntar_complementar(cand, compl).set_index("sq_candidato")
    assert bool(df.loc["1", "declarou_bens"]) is False
    assert bool(df.loc["1", "busca_reeleicao"]) is True
    assert pd.isna(df.loc["2", "declarou_bens"])
    assert pd.isna(df.loc["2", "busca_reeleicao"])  # "#NE": o TSE não informou
    assert "NM_MUNICIPIO_NASCIMENTO" not in df.columns


def test_situacao_no_pleito_prevalece_sobre_julgamento(tmp_path: Path):
    cand = carregar(
        tmp_path,
        [linha_cand(2026, "1", "1111", "ANA"), linha_cand(2026, "2", "2222", "BIA")],
    )
    compl = ler_compl(
        tmp_path,
        [
            linha_compl(
                "1",
                DS_SITUACAO_JULGAMENTO="DEFERIDO",
                DS_SITUACAO_JULGAMENTO_PLEITO="INDEFERIDO EM PRAZO RECURSAL OU COM RECURSO",
            ),
            linha_compl(
                "2", DS_SITUACAO_JULGAMENTO="RENÚNCIA", DS_SITUACAO_JULGAMENTO_PLEITO="#NULO"
            ),
        ],
    )
    df = tse.juntar_complementar(cand, compl).set_index("sq_candidato")
    assert df.loc["1", "situacao_julgamento"] == "INDEFERIDO EM PRAZO RECURSAL OU COM RECURSO"
    assert df.loc["2", "situacao_julgamento"] == "RENÚNCIA"


def test_candidatura_sem_complementar_falha(tmp_path: Path):
    cand = carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA")])
    with pytest.raises(tse.ErroDados, match="sem linha no arquivo complementar"):
        tse.juntar_complementar(cand, ler_compl(tmp_path, [linha_compl("9")]))


def test_complementar_repetido_falha(tmp_path: Path):
    cand = carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA")])
    with pytest.raises(tse.ErroDados, match="repetido"):
        tse.juntar_complementar(cand, ler_compl(tmp_path, [linha_compl("1"), linha_compl("1")]))


# --- Candidaturas exibíveis ---------------------------------------------------------------


def cfg_teste(raiz: Path) -> config.Config:
    return config.carregar(raiz / "config.toml")


def base_exibiveis(tmp_path: Path, extra, situacoes: dict[str, str] | None = None):
    linhas = [
        linha_cand(2026, "1", "1111", "ANA"),
        linha_cand(2026, "2", "22", "BIA", DS_CARGO="SENADOR"),
        linha_cand(2026, "3", "10", "CIDA", DS_CARGO="PRESIDENTE", SG_UF="BR", SG_UE="BR"),
        *extra,
    ]
    situacoes = situacoes or {}
    compl = [
        linha_compl(
            ln["SQ_CANDIDATO"],
            DS_SITUACAO_JULGAMENTO_PLEITO=situacoes.get(ln["SQ_CANDIDATO"], "DEFERIDO"),
        )
        for ln in linhas
    ]
    return tse.juntar_complementar(carregar(tmp_path, linhas), ler_compl(tmp_path, compl))


def test_vice_e_suplente_ficam_de_fora(tmp_path: Path, raiz: Path):
    df = base_exibiveis(
        tmp_path,
        [
            linha_cand(2026, "4", "10", "DITO", DS_CARGO="VICE-PRESIDENTE", SG_UF="BR"),
            linha_cand(2026, "5", "221", "EVA", DS_CARGO="1º SUPLENTE"),
        ],
    )
    exib = tse.candidaturas_exibiveis(df, cfg_teste(raiz))
    assert sorted(exib["sq_candidato"]) == ["1", "2", "3"]


def test_inapta_aparece_com_apto_false(tmp_path: Path, raiz: Path):
    df = base_exibiveis(
        tmp_path,
        [linha_cand(2026, "6", "3333", "FABI"), linha_cand(2026, "7", "4444", "GIL")],
        {"6": "INDEFERIDO", "7": "INDEFERIDO EM PRAZO RECURSAL OU COM RECURSO"},
    )
    exib = tse.candidaturas_exibiveis(df, cfg_teste(raiz)).set_index("sq_candidato")
    assert bool(exib.loc["6", "apto"]) is False
    assert bool(exib.loc["7", "apto"]) is True  # sub judice: está na urna
    assert bool(exib.loc["1", "apto"]) is True


def test_situacao_desconhecida_falha(tmp_path: Path, raiz: Path):
    df = base_exibiveis(tmp_path, [linha_cand(2026, "6", "3333", "FABI")], {"6": "SITUAÇÃO NOVA"})
    with pytest.raises(tse.ErroDados, match="SITUAÇÃO NOVA"):
        tse.candidaturas_exibiveis(df, cfg_teste(raiz))


def test_cargo_configurado_sem_candidatura_falha(tmp_path: Path, raiz: Path):
    df = tse.juntar_complementar(
        carregar(tmp_path, [linha_cand(2026, "1", "1111", "ANA")]),
        ler_compl(tmp_path, [linha_compl("1")]),
    )
    with pytest.raises(tse.ErroDados, match="PRESIDENTE"):
        tse.candidaturas_exibiveis(df, cfg_teste(raiz))


# --- Bens e redes -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "centavos"),
    [("1234,56", 123456), ("1.234,56", 123456), ("1234.56", 123456), ("0,00", 0), ("10", 1000)],
)
def test_valor_em_centavos(texto: str, centavos: int):
    assert tse.valor_em_centavos(texto) == centavos


def test_valor_ilegivel_falha():
    with pytest.raises(tse.ErroDados, match="ilegível"):
        tse.valor_em_centavos("abc")


def test_total_bens_soma_e_distingue_zero_de_nao_declarado():
    bens = pd.DataFrame(
        {
            "SQ_CANDIDATO": ["1", "1", "1", "2"],
            "VR_BEM_CANDIDATO": ["100,00", "50,50", "0,01", "0,00"],
        }
    )
    total = tse.total_bens(bens).set_index("sq_candidato")
    assert total.loc["1", "bens_total_centavos"] == 15051
    assert total.loc["1", "bens_quantidade"] == 3
    assert total.loc["2", "bens_total_centavos"] == 0  # declarou, com valor zero
    assert "3" not in total.index  # não declarou: sem linha, o detalhe mostra nulo


def test_redes_sociais_sem_duplicatas():
    redes = pd.DataFrame(
        {
            "SQ_CANDIDATO": ["1", "1", "2"],
            "DS_URL": ["https://a.invalid/x", "https://a.invalid/x", None],
        }
    )
    assert tse.redes_sociais(redes).to_dict("records") == [
        {"sq_candidato": "1", "url": "https://a.invalid/x"}
    ]


# --- Processamento de ponta a ponta -------------------------------------------------------


def montar_raw(raiz: Path) -> None:
    raw = raiz / "data" / "raw"
    tmp = raiz / "tmp"
    cand26 = [
        linha_cand(2026, "1", "1111", "ANA"),
        linha_cand(2026, "2", "222", "BIA", DS_CARGO="SENADOR", NR_CPF_CANDIDATO=gerar_cpf(2)),
    ]
    pres = [
        linha_cand(
            2026,
            "3",
            "10",
            "CIDA",
            DS_CARGO="PRESIDENTE",
            SG_UF="BR",
            SG_UE="BR",
            NR_CPF_CANDIDATO=gerar_cpf(3),
        )
    ]
    escrever_zip(
        raw / "consulta_cand_2026.zip",
        {
            "consulta_cand_2026_RR.csv": escrever_csv(tmp / "a.csv", CABECALHO_CAND, cand26),
            "consulta_cand_2026_BR.csv": escrever_csv(tmp / "b.csv", CABECALHO_CAND, pres),
            "consulta_cand_2026_BRASIL.csv": escrever_csv(
                tmp / "c.csv", CABECALHO_CAND, cand26 + pres
            ),
            "leiame.pdf": tmp / "a.csv",
        },
    )
    compl = [linha_compl("1"), linha_compl("2"), linha_compl("3", ST_DECLARAR_BENS="N")]
    escrever_zip(
        raw / "consulta_cand_complementar_2026.zip",
        {
            "consulta_cand_complementar_2026_RR.csv": escrever_csv(
                tmp / "g.csv", CABECALHO_COMPL, compl[:2]
            ),
            "consulta_cand_complementar_2026_BR.csv": escrever_csv(
                tmp / "h.csv", CABECALHO_COMPL, compl[2:]
            ),
        },
    )
    cand22 = [linha_cand(2022, "7", "4444", "ANA", DS_SIT_TOT_TURNO="SUPLENTE")]
    escrever_zip(
        raw / "consulta_cand_2022.zip",
        {"consulta_cand_2022_RR.csv": escrever_csv(tmp / "d.csv", CABECALHO_CAND, cand22)},
    )
    bens = [{"ANO_ELEICAO": "2026", "SQ_CANDIDATO": "1", "VR_BEM_CANDIDATO": "1000,00"}]
    escrever_zip(
        raw / "bem_candidato_2026.zip",
        {
            "bem_candidato_2026_RR.csv": escrever_csv(
                tmp / "e.csv", ["ANO_ELEICAO", "SQ_CANDIDATO", "VR_BEM_CANDIDATO"], bens
            )
        },
    )
    redes = [{"SQ_CANDIDATO": "1", "DS_URL": "https://exemplo.invalid/ana"}]
    escrever_zip(
        raw / "rede_social_candidato_2026.zip",
        {
            "rede_social_candidato_2026_RR.csv": escrever_csv(
                tmp / "f.csv", ["SQ_CANDIDATO", "DS_URL"], redes
            )
        },
    )


def test_processar_grava_tabelas_normalizadas(raiz: Path):
    montar_raw(raiz)
    tse.processar(cfg_teste(raiz), log=lambda m: None)
    interim = raiz / "data" / "interim"
    cand = pd.read_parquet(interim / "candidaturas.parquet")
    # consolidado _BRASIL ignorado: sem duplicatas
    assert sorted(cand["sq_candidato"]) == ["1", "2", "3", "7"]
    assert set(cand["ano"]) == {2022, 2026}
    por_sq = cand.set_index("sq_candidato")
    assert por_sq.loc["1", "situacao_julgamento"] == "DEFERIDO"
    assert bool(por_sq.loc["3", "declarou_bens"]) is False
    assert pd.isna(por_sq.loc["7", "situacao_julgamento"])  # só no ano da eleição
    bens = pd.read_parquet(interim / "bens_2026.parquet")
    assert bens.to_dict("records") == [
        {"sq_candidato": "1", "bens_total_centavos": 100000, "bens_quantidade": 1}
    ]
    redes = pd.read_parquet(interim / "redes_sociais_2026.parquet")
    assert redes["url"].tolist() == ["https://exemplo.invalid/ana"]
