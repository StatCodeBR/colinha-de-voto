import json
import re
from pathlib import Path

import pandas as pd
import pytest

from colinha import config, saida, tse, vinculo
from tests.conftest import gerar_cpf
from tests.test_tse import montar_raw
from tests.test_vinculo import cand, tabela

# --- Identificadores ----------------------------------------------------------------------


def exib(*linhas: tuple[str, str, str, bool]) -> pd.DataFrame:
    return pd.DataFrame(linhas, columns=["sq_candidato", "uf", "numero", "apto"])


def test_id_simples_em_minusculas():
    ids = saida.atribuir_ids(exib(("1", "RR", "1234", True), ("2", "BR", "10", True)))
    assert ids.to_dict() == {"1": "rr/1234", "2": "br/10"}


def test_numero_herdado_fica_com_a_candidatura_apta():
    ids = saida.atribuir_ids(
        exib(("1", "RR", "1234", False), ("2", "RR", "1234", True), ("3", "SP", "1234", False))
    )
    assert ids.to_dict() == {"1": "rr/1234-1", "2": "rr/1234", "3": "sp/1234"}


def test_numero_repetido_so_entre_inaptas_leva_sufixo_nas_duas():
    ids = saida.atribuir_ids(exib(("1", "RR", "55", False), ("2", "RR", "55", False)))
    assert ids.to_dict() == {"1": "rr/55-1", "2": "rr/55-2"}


def test_duas_aptas_com_o_mesmo_numero_falham():
    with pytest.raises(tse.ErroDados, match="aptas"):
        saida.atribuir_ids(exib(("1", "RR", "55", True), ("2", "RR", "55", True)))


# --- Reeleição ----------------------------------------------------------------------------

CPF = gerar_cpf(4242)


def reel(atual_cargo: str, passado: dict, nivel: str = "confirmado") -> bool | None:
    atual = tabela(cand(2026, "1", "ANA SOUZA", cpf=CPF, cargo=atual_cargo))
    p = tabela(passado)
    v = pd.DataFrame(
        [("1", passado["ano"], passado["sq_candidato"], nivel, "cpf")],
        columns=["sq_atual", "ano_passado", "sq_passado", "nivel", "regra"],
    )
    resultados = p[["ano", "sq_candidato"]].assign(resultado=vinculo.mapear_resultado(p))
    valor = vinculo.reeleicao(atual, p, v, resultados)["1"]
    return None if pd.isna(valor) else bool(valor)


def test_eleita_para_o_mesmo_cargo_na_eleicao_anterior_busca_reeleicao():
    assert reel(
        "DEPUTADO FEDERAL",
        cand(2022, "7", "X", cargo="DEPUTADO FEDERAL", resultado="ELEITO POR QP"),
    )


def test_senador_olha_oito_anos_antes():
    assert reel("SENADOR", cand(2018, "7", "X", cargo="SENADOR", resultado="ELEITO"))
    assert not reel("SENADOR", cand(2022, "7", "X", cargo="SENADOR", resultado="ELEITO"))


def test_outro_cargo_outra_uf_ou_suplente_nao_e_reeleicao():
    assert not reel(
        "DEPUTADO FEDERAL", cand(2022, "7", "X", cargo="DEPUTADO ESTADUAL", resultado="ELEITO")
    )
    assert not reel(
        "DEPUTADO FEDERAL",
        cand(2022, "7", "X", cargo="DEPUTADO FEDERAL", uf="SP", resultado="ELEITO"),
    )
    assert not reel(
        "DEPUTADO FEDERAL", cand(2022, "7", "X", cargo="DEPUTADO FEDERAL", resultado="SUPLENTE")
    )


def test_vinculo_pendente_na_eleicao_anterior_deixa_nulo():
    passado = cand(2022, "7", "X", cargo="DEPUTADO FEDERAL", resultado="ELEITO")
    assert reel("DEPUTADO FEDERAL", passado, nivel="ambiguo") is None


# --- Registros ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nascimento", "anos"), [("1980-10-04", 46), ("1980-10-05", 45), (None, None)]
)
def test_idade_no_primeiro_turno(nascimento, anos):
    assert saida.idade(nascimento, pd.Timestamp("2026-10-04").date()) == anos


def linha_publica(**extra) -> dict:
    return {
        "sq_candidato": "1",
        "uf": "RR",
        "numero": "1234",
        "cargo": "DEPUTADO FEDERAL",
        "nome_urna": "ANINHA",
        "nome_exibido": "NOME SOCIAL",
        "nome_civil": "NOME CIVIL SECRETO",
        "cpf": "00000000191",
        "data_nascimento": "1980-02-01",
        "partido": "PXX",
        "federacao": None,
        "genero": "FEMININO",
        "cor_raca": "PARDA",
        "grau_instrucao": None,
        "ocupacao": "PROFESSORA",
        "apto": True,
        "situacao_julgamento": "DEFERIDO",
        "declarou_bens": False,
        "bens_total_centavos": float("nan"),
        "bens_quantidade": float("nan"),
        "historico": "sem_registro",
        "ha_registros_em_verificacao": False,
        "busca_reeleicao": pd.NA,
        "coluna_nova_do_tse": "vazou",
        **extra,
    }


def test_detalhe_so_tem_campos_da_allowlist(raiz: Path):
    cfg = config.carregar(raiz / "config.toml")
    d = saida.detalhe(linha_publica(), "rr/1234", [], [], cfg, {}, "agora")
    texto = json.dumps(d, ensure_ascii=False)
    for proibido in ["NOME CIVIL SECRETO", "00000000191", "1980-02-01", "vazou", "nome_civil"]:
        assert proibido not in texto
    assert d["nome_exibido"] == "NOME SOCIAL"
    assert d["perfil"]["idade"] == 46
    assert d["perfil"]["grau_instrucao"] is None
    assert d["bens"] == {"declarou_bens": False, "total": None, "quantidade": None}
    assert d["historico"]["busca_reeleicao"] is None
    assert d["historico"]["cobertura"] == {"inicio": 2022, "fim": 2022}


def test_item_do_indice_so_tem_campos_da_allowlist():
    item = saida.item_indice(linha_publica(), "rr/1234")
    assert set(item) == {
        "id", "nome_urna", "numero", "cargo", "partido", "genero", "historico",
        "busca_reeleicao", "apto",
    }  # fmt: skip


def test_bens_declarados_somados(raiz: Path):
    cfg = config.carregar(raiz / "config.toml")
    c = linha_publica(declarou_bens=True, bens_total_centavos=15051.0, bens_quantidade=3.0)
    assert saida.detalhe(c, "rr/1234", [], [], cfg, {}, "agora")["bens"] == {
        "declarou_bens": True,
        "total": 150.51,
        "quantidade": 3,
    }


def test_trajetoria_sem_nome_da_eleicao_anterior():
    passado = tabela(
        cand(2022, "7", "NOME ANTIGO", resultado="ELEITO"),
        cand(2018, "8", "NOME ANTIGO", resultado="SUPLENTE"),
        cand(2014, "9", "NOME ANTIGO", resultado="ELEITO"),
    )
    v = pd.DataFrame(
        [
            ("1", 2018, "8", "confirmado"),
            ("1", 2022, "7", "confirmado"),
            ("1", 2014, "9", "ambiguo"),
        ],
        columns=["sq_atual", "ano_passado", "sq_passado", "nivel"],
    )
    resultados = passado[["ano", "sq_candidato"]].assign(
        resultado=vinculo.mapear_resultado(passado)
    )
    t = saida.trajetorias(v, passado, resultados, (2022, 2018, 2014))["1"]
    assert [(x["ano"], x["resultado"]) for x in t] == [(2022, "eleito"), (2018, "suplente")]
    assert "NOME ANTIGO" not in json.dumps(t)
    assert set(t[0]) == {"ano", "cargo", "uf", "local", "partido", "resultado"}


# --- De ponta a ponta e privacidade -------------------------------------------------------


def gerar_tudo(raiz: Path) -> config.Config:
    montar_raw(raiz)
    cfg = config.carregar(raiz / "config.toml")
    raw = cfg.dir_raw
    manifesto = {
        z.name: {
            "url": f"https://exemplo.invalid/{z.name}",
            "baixado_em": "2026-09-28T10:00:00-03:00",
        }
        for z in raw.glob("*.zip")
    }
    (raw / "manifest.json").write_text(json.dumps(manifesto))
    tse.processar(cfg, log=lambda m: None)
    vinculo.executar(cfg, log=lambda m: None)
    saida.gerar(cfg, ("RR",), log=lambda m: None)
    return cfg


def test_saidas_de_ponta_a_ponta(raiz: Path):
    cfg = gerar_tudo(raiz)
    out = cfg.dir_processed
    indice = json.loads((out / "RR" / "indice.json").read_text())
    assert [c["id"] for c in indice["candidatos"]] == ["rr/1111", "rr/22"]  # ordem alfabética
    assert json.loads((out / "BR" / "indice.json").read_text())["candidatos"][0]["id"] == "br/10"
    ana = json.loads((out / "RR" / "candidatos" / "1111.json").read_text())
    assert ana["trajetoria"][0]["resultado"] == "suplente"
    assert ana["fontes"]["candidatura"][0]["extraido_em"] == "2026-09-28T10:00:00-03:00"
    resumo = json.loads((out / "resumo.json").read_text())
    assert resumo["ufs"]["RR"]["candidaturas"] == 2
    assert (out / "manifesto.json").exists()


def test_nenhum_cpf_de_entrada_aparece_nas_saidas(raiz: Path):
    cfg = gerar_tudo(raiz)
    cpfs = set(pd.read_parquet(cfg.dir_interim / "candidaturas.parquet")["cpf"].dropna())
    assert cpfs
    for arquivo in cfg.dir_processed.rglob("*"):
        if arquivo.is_file():
            texto = arquivo.read_text(encoding="utf-8")
            digitos = set(re.findall(r"\d{11}", texto))
            assert not cpfs & digitos, arquivo
            assert not any(cpf in texto for cpf in cpfs), arquivo


def test_checar_privacidade_acha_vazamento(raiz: Path):
    cfg = gerar_tudo(raiz)
    assert saida.checar_privacidade(cfg) == []
    (cfg.dir_processed / "RR" / "vazou.json").write_text('{"x":"00000000191"}')
    assert len(saida.checar_privacidade(cfg)) == 1
