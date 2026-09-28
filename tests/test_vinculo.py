from pathlib import Path

import pandas as pd
import pytest

from colinha import config, tse, vinculo
from tests.conftest import gerar_cpf
from tests.test_tse import montar_raw


def cand(
    ano: int,
    sq: str,
    nome: str,
    nascimento: str | None = "1980-02-01",
    cpf: str | None = None,
    uf: str = "RR",
    cargo: str = "DEPUTADO ESTADUAL",
    resultado: str | None = None,
) -> dict:
    return {
        "ano": ano,
        "sq_candidato": sq,
        "uf": uf,
        "nm_ue": "BOA VISTA" if ano % 4 == 0 else "RORAIMA",
        "cargo": cargo,
        "numero": "12345",
        "partido": "PXX",
        "nome_civil": nome,
        "data_nascimento": nascimento,
        "cpf": cpf,
        "situacao_totalizacao": resultado,
    }


def tabela(*linhas: dict) -> pd.DataFrame:
    return pd.DataFrame(list(linhas)).astype(
        {c: "str" for c in ["sq_candidato", "nome_civil", "data_nascimento", "cpf"]}
    )


def vinculos(atual, passado) -> dict[tuple[str, int, str], tuple[str, str]]:
    v = vinculo.vincular(tabela(*atual), tabela(*passado))
    return {(r.sq_atual, r.ano_passado, r.sq_passado): (r.nivel, r.regra) for r in v.itertuples()}


# --- Normalização -------------------------------------------------------------------------


def test_nome_com_acentos_e_apostrofo():
    assert vinculo.normalizar_nome("Maria D'Ávila  Souza") == vinculo.normalizar_nome(
        "MARIA D AVILA SOUZA"
    )


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("  josé   da silva ", "JOSE DA SILVA"),
        ("Ana-Clara Conceição", "ANA CLARA CONCEICAO"),
        ("JOÃO D`ÁVILA", "JOAO D AVILA"),
        ("Zé 2º", "ZE O"),
    ],
)
def test_normalizar_nome(nome: str, esperado: str):
    assert vinculo.normalizar_nome(nome) == esperado


def test_versao_vetorizada_igual_a_escalar():
    nomes = ["Maria D'Ávila  Souza", "Ana-Clara", "ÇÃO Ñandu", "Zé 2º"]
    assert vinculo.normalizar_nomes(pd.Series(nomes)).tolist() == [
        vinculo.normalizar_nome(n) for n in nomes
    ]


def test_cpf_valido():
    cpfs = pd.Series([gerar_cpf(123), "00000000191", "00000000192", "11111111111", "123", None])
    assert vinculo.cpf_valido(cpfs).tolist() == [True, True, False, False, False, False]


# --- Regras de vínculo --------------------------------------------------------------------

CPF_A, CPF_B = gerar_cpf(1001), gerar_cpf(2002)


def test_mesmo_cpf_confirma():
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA", cpf=CPF_A)],
        [cand(2022, "7", "ANA DE SOUZA", nascimento="1980-01-01", cpf=CPF_A)],
    )
    assert v == {("1", 2022, "7"): ("confirmado", "cpf")}


def test_mesmo_cpf_com_nome_e_nascimento_divergentes_vai_para_revisao():
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA", cpf=CPF_A)],
        [cand(2016, "7", "JOSE DA SILVA", nascimento="1974-01-01", cpf=CPF_A)],
    )
    assert v == {("1", 2016, "7"): ("ambiguo", "cpf_divergente")}


def test_mesmo_cpf_e_nascimento_com_nome_trocado_confirma():
    # mudança de nome civil: nenhuma palavra em comum, mas CPF e nascimento iguais
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA", cpf=CPF_A)],
        [cand(2018, "7", "BRUNO LIMA COSTA", cpf=CPF_A)],
    )
    assert v == {("1", 2018, "7"): ("confirmado", "cpf")}


def test_particulas_nao_contam_como_palavra_em_comum():
    assert not vinculo.nomes_compativeis("ANA DA SILVA", "JOSE DA COSTA")
    assert vinculo.nomes_compativeis("ANA DA SILVA", "ANA MARIA SOUZA")


def test_cpfs_diferentes_nao_vinculam_mesmo_com_nome_e_nascimento():
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA", cpf=CPF_A)],
        [cand(2022, "7", "ANA SOUZA", cpf=CPF_B)],
    )
    assert v == {}


def test_nome_e_nascimento_unicos_confirmam_quando_falta_cpf():
    v = vinculos(
        [cand(2026, "1", "Ana Souza", cpf=CPF_A)],
        [cand(2024, "7", "ANA SOUZA", cpf=None)],
    )
    assert v == {("1", 2024, "7"): ("confirmado", "nome_nascimento")}


def test_homonimos_com_nascimentos_diferentes_nao_vinculam():
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA", nascimento="1980-02-01")],
        [cand(2024, "7", "ANA SOUZA", nascimento="1975-06-30")],
    )
    assert v == {}


def test_chave_repetida_no_ano_anterior_vira_ambiguo():
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA")],
        [cand(2024, "7", "ANA SOUZA", uf="SP"), cand(2024, "8", "ANA SOUZA", uf="MG")],
    )
    assert v == {
        ("1", 2024, "7"): ("ambiguo", "nome_nascimento"),
        ("1", 2024, "8"): ("ambiguo", "nome_nascimento"),
    }


def test_chave_repetida_no_ano_da_eleicao_vira_ambiguo():
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA"), cand(2026, "2", "ANA SOUZA", uf="SP")],
        [cand(2024, "7", "ANA SOUZA")],
    )
    assert {nivel for nivel, _ in v.values()} == {"ambiguo"}


def test_mesma_chave_em_anos_diferentes_nao_e_ambigua():
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA")],
        [cand(2024, "7", "ANA SOUZA"), cand(2020, "8", "ANA SOUZA")],
    )
    assert {nivel for nivel, _ in v.values()} == {"confirmado"}


def test_sem_nascimento_mesmo_nome_e_uf_vira_provavel():
    v = vinculos(
        [cand(2026, "1", "ANA SOUZA", cpf=CPF_A)],
        [
            cand(2018, "7", "ANA SOUZA", nascimento=None),
            cand(2018, "8", "ANA SOUZA", nascimento=None, uf="SP"),
        ],
    )
    assert v == {("1", 2018, "7"): ("provavel", "nome_uf")}


# --- Correções manuais --------------------------------------------------------------------


def manual(*linhas: tuple[str, str, str, str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sq_candidato_atual": a,
                "ano_passado": ano,
                "sq_candidato_passado": p,
                "decisao": d,
                "revisado_por": "Equipe",
                "revisado_em": "2026-09-28",
                "nota": "",
            }
            for a, ano, p, d in linhas
        ]
    )


ATUAL = tabela(cand(2026, "1", "ANA SOUZA", cpf=CPF_A))
PASSADO = tabela(
    cand(2022, "7", "ANA SOUZA", cpf=CPF_A),
    cand(2018, "8", "ANA SOUZA", nascimento=None),
)


def aplicar(*linhas) -> set[tuple[str, int, str, str]]:
    v = vinculo.vincular(ATUAL, PASSADO)
    v = vinculo.aplicar_manual(v, manual(*linhas), ATUAL, PASSADO)
    return {(r.sq_atual, r.ano_passado, r.sq_passado, r.nivel) for r in v.itertuples()}


def test_sem_correcoes_nada_muda():
    assert aplicar() == {("1", 2022, "7", "confirmado"), ("1", 2018, "8", "provavel")}


def test_rejeicao_manual_remove_vinculo_automatico():
    assert aplicar(("1", "2022", "7", "rejeitar")) == {("1", 2018, "8", "provavel")}


def test_confirmacao_manual_publica_provavel():
    assert aplicar(("1", "2018", "8", " Confirmar ")) == {
        ("1", 2022, "7", "confirmado"),
        ("1", 2018, "8", "confirmado"),
    }


def test_confirmacao_de_candidatura_inexistente_falha():
    with pytest.raises(tse.ErroDados, match="não existem"):
        aplicar(("1", "2014", "99", "confirmar"))


def test_decisao_desconhecida_falha():
    with pytest.raises(tse.ErroDados, match="talvez"):
        aplicar(("1", "2018", "8", "talvez"))


def test_decisoes_conflitantes_falham():
    with pytest.raises(tse.ErroDados, match="ao mesmo tempo"):
        aplicar(("1", "2018", "8", "confirmar"), ("1", "2018", "8", "rejeitar"))


def test_ler_manual(tmp_path: Path):
    assert vinculo.ler_manual(tmp_path / "nao_existe.csv").empty
    ruim = tmp_path / "ruim.csv"
    ruim.write_text("a,b\n1,2\n")
    with pytest.raises(tse.ErroDados, match="cabeçalho"):
        vinculo.ler_manual(ruim)
    real = vinculo.ler_manual(Path(__file__).parents[1] / "data" / "manual" / "vinculos.csv")
    assert list(real.columns) == vinculo.COLUNAS_MANUAL


# --- Resultado ----------------------------------------------------------------------------


def test_mapear_resultado():
    df = tabela(
        *(
            cand(2022, str(i), "X", resultado=r)
            for i, r in enumerate(
                ["ELEITO POR QP", "ELEITO POR MÉDIA", "NÃO ELEITO", "SUPLENTE", "2º TURNO", None]
            )
        )
    )
    assert vinculo.mapear_resultado(df).tolist() == [
        "eleito",
        "eleito",
        "nao_eleito",
        "suplente",
        "segundo_turno_sem_resultado",
        "sem_resultado",
    ]


def test_resultado_desconhecido_falha_com_ano_e_valor():
    df = tabela(cand(2020, "1", "X", resultado="ELEITO"), cand(2020, "2", "X", resultado="CASSADO"))
    with pytest.raises(tse.ErroDados, match="2020: 'CASSADO'"):
        vinculo.mapear_resultado(df)


# --- Classificação ------------------------------------------------------------------------


def test_classificacao_do_historico():
    v = pd.DataFrame(
        [
            ("eleita", 2020, "a", "confirmado"),
            ("concorreu", 2022, "b", "confirmado"),
            ("concorreu", 2018, "c", "ambiguo"),
            ("pendente", 2024, "d", "provavel"),
            ("fora_da_janela", 2010, "e", "confirmado"),
        ],
        columns=["sq_atual", "ano_passado", "sq_passado", "nivel"],
    )
    resultados = pd.DataFrame(
        [(2020, "a", "eleito"), (2022, "b", "suplente"), (2010, "e", "eleito")],
        columns=["ano", "sq_candidato", "resultado"],
    )
    atuais = pd.Series(["eleita", "concorreu", "pendente", "fora_da_janela", "nada"])
    h = vinculo.classificar(atuais, v, resultados, (2024, 2022, 2020, 2018)).set_index(
        "sq_candidato"
    )
    assert h["historico"].to_dict() == {
        "eleita": "eleito",
        "concorreu": "concorreu",
        "pendente": "em_verificacao",
        "fora_da_janela": "sem_registro",
        "nada": "sem_registro",
    }
    assert h["ha_registros_em_verificacao"].to_dict() == {
        "eleita": False,
        "concorreu": True,
        "pendente": False,
        "fora_da_janela": False,
        "nada": False,
    }


# --- Revisão e execução -------------------------------------------------------------------


def test_revisao_traz_evidencias_sem_cpf():
    v = vinculo.vincular(ATUAL, PASSADO)
    rev = vinculo.revisao(v, ATUAL, PASSADO)
    assert len(rev) == 1  # só o provável
    linha = rev.iloc[0]
    assert (linha["sq_candidato_atual"], linha["ano_passado"]) == ("1", 2018)
    assert linha["cpf_informado_atual"] == "sim"
    assert linha["cpf_informado_passado"] == "não"
    assert linha["nome_normalizado_passado"] == "ANA SOUZA"
    assert CPF_A not in rev.astype(str).to_numpy().ravel()


def test_executar_de_ponta_a_ponta(raiz: Path):
    montar_raw(raiz)
    cfg = config.carregar(raiz / "config.toml")
    tse.processar(cfg, log=lambda m: None)
    vinculo.executar(cfg, log=lambda m: None)

    v = pd.read_parquet(cfg.dir_interim / "vinculos.parquet")
    assert v[["sq_atual", "ano_passado", "sq_passado", "nivel", "regra"]].values.tolist() == [
        ["1", 2022, "7", "confirmado", "cpf"]
    ]
    h = pd.read_parquet(cfg.dir_interim / "historico.parquet").set_index("sq_candidato")
    assert h.loc["1", "historico"] == "concorreu"
    assert h.loc["2", "historico"] == "sem_registro"
    assert h.loc["3", "historico"] == "sem_registro"
    revisao = (cfg.dir_processed / "revisao_vinculos.csv").read_text(encoding="utf-8")
    assert "00000000191" not in revisao
