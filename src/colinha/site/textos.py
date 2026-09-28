"""Textos da interface: flexão de gênero, cargos, resultados e formatação.

Regras de linguagem no design da change 02 (D5): frases curtas, sem sigla solta, sem
adjetivo avaliativo, flexão pelo gênero declarado. Valor desconhecido interrompe a
geração do site em vez de cair num texto padrão.
"""

from __future__ import annotations

import re
from datetime import date, datetime

NAO_INFORMADO = "Não informado"

NOMES_UF = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima",
    "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins", "BR": "Brasil",
}  # fmt: skip

# Cargo do TSE -> (masculino, feminino, sem gênero declarado).
CARGOS = {
    "PRESIDENTE": ("Presidente", "Presidente", "Presidente"),
    "VICE-PRESIDENTE": ("Vice-presidente", "Vice-presidente", "Vice-presidente"),
    "GOVERNADOR": ("Governador", "Governadora", "Governador(a)"),
    "VICE-GOVERNADOR": ("Vice-governador", "Vice-governadora", "Vice-governador(a)"),
    "SENADOR": ("Senador", "Senadora", "Senador(a)"),
    "1º SUPLENTE": (
        "1º suplente de senador", "1ª suplente de senador", "1º(ª) suplente de senador"
    ),
    "2º SUPLENTE": (
        "2º suplente de senador", "2ª suplente de senador", "2º(ª) suplente de senador"
    ),
    "DEPUTADO FEDERAL": ("Deputado federal", "Deputada federal", "Deputado(a) federal"),
    "DEPUTADO ESTADUAL": ("Deputado estadual", "Deputada estadual", "Deputado(a) estadual"),
    "DEPUTADO DISTRITAL": ("Deputado distrital", "Deputada distrital", "Deputado(a) distrital"),
    "PREFEITO": ("Prefeito", "Prefeita", "Prefeito(a)"),
    "VICE-PREFEITO": ("Vice-prefeito", "Vice-prefeita", "Vice-prefeito(a)"),
    "VEREADOR": ("Vereador", "Vereadora", "Vereador(a)"),
}  # fmt: skip

# Nome do cargo em títulos e listas ("Candidaturas a deputado federal").
CARGO_GENERICO = {cargo: formas[0].lower() for cargo, formas in CARGOS.items()}

# Resultado (saída da change 01) -> (masculino, feminino, sem gênero).
RESULTADOS = {
    "eleito": ("Eleito", "Eleita", "Eleito(a)"),
    "suplente": ("Ficou como suplente", "Ficou como suplente", "Ficou como suplente"),
    "nao_eleito": ("Não eleito", "Não eleita", "Não eleito(a)"),
    "segundo_turno_sem_resultado": (
        "Foi ao 2º turno, sem resultado registrado",
        "Foi ao 2º turno, sem resultado registrado",
        "Foi ao 2º turno, sem resultado registrado",
    ),
    "sem_resultado": (
        "Sem resultado registrado",
        "Sem resultado registrado",
        "Sem resultado registrado",
    ),
}

# Situação de julgamento (TSE) -> texto por extenso.
SITUACOES = {
    "DEFERIDO": "Candidatura deferida pela Justiça Eleitoral.",
    "DEFERIDO COM RECURSO": "Candidatura deferida, com recurso ainda não julgado.",
    "DEFERIDO EM PRAZO RECURSAL OU COM RECURSO": (
        "Candidatura deferida, com recurso ainda não julgado."
    ),
    "INDEFERIDO EM PRAZO RECURSAL OU COM RECURSO": (
        "Candidatura indeferida, com recurso ainda não julgado. O nome está na urna, e a "
        "validade dos votos depende da decisão final da Justiça Eleitoral."
    ),
    "PEDIDO NÃO CONHECIDO EM PRAZO RECURSAL OU COM RECURSO": (
        "Pedido de registro não conhecido, com recurso ainda não julgado. A validade dos "
        "votos depende da decisão final da Justiça Eleitoral."
    ),
    "PENDENTE DE JULGAMENTO": (
        "Candidatura aguardando julgamento. A validade dos votos depende da decisão da "
        "Justiça Eleitoral."
    ),
    "INDEFERIDO": "Candidatura indeferida pela Justiça Eleitoral.",
    "PEDIDO NÃO CONHECIDO": "Pedido de registro não conhecido pela Justiça Eleitoral.",
    "RENÚNCIA": "Houve renúncia à candidatura.",
    "CANCELADO": "Candidatura cancelada.",
    "FALECIMENTO": "Candidatura encerrada por falecimento.",
}

_PARTICULAS = {"da", "das", "de", "do", "dos", "e"}


class ErroTexto(Exception):
    """Valor sem texto definido. Acrescente-o aqui em vez de cair num padrão."""


def _forma(genero: str | None) -> int:
    return {"MASCULINO": 0, "FEMININO": 1}.get(genero or "", 2)


def flexao(genero: str | None, masculino: str, feminino: str, neutro: str) -> str:
    return (masculino, feminino, neutro)[_forma(genero)]


def cargo(nome: str, genero: str | None) -> str:
    try:
        return CARGOS[nome][_forma(genero)]
    except KeyError as e:
        raise ErroTexto(f"cargo sem texto: {nome!r}") from e


def slug_cargo(nome: str) -> str:
    return CARGO_GENERICO[nome].replace(" ", "-")


def resultado(valor: str, genero: str | None) -> str:
    try:
        return RESULTADOS[valor][_forma(genero)]
    except KeyError as e:
        raise ErroTexto(f"resultado sem texto: {valor!r}") from e


def situacao(descricao: str) -> str:
    try:
        return SITUACOES[descricao]
    except KeyError as e:
        raise ErroTexto(f"situação sem texto: {descricao!r}") from e


def etiqueta_historico(classe: str, genero: str | None, janela: str) -> str:
    """`janela`: "de 2014 a 2024". Ausência de registro sempre com a janela."""
    textos = {
        "eleito": flexao(genero, "Já foi eleito", "Já foi eleita", "Já foi eleito(a)"),
        "concorreu": "Já concorreu",
        "sem_registro": f"Nenhuma candidatura encontrada {janela}",
        "em_verificacao": "Histórico em verificação",
    }
    try:
        return textos[classe]
    except KeyError as e:
        raise ErroTexto(f"classe de histórico sem texto: {classe!r}") from e


def titulo(texto: str | None) -> str:
    """"SÃO JOÃO DA BARRA" -> "São João da Barra"."""
    if not texto:
        return NAO_INFORMADO
    palavras = texto.lower().split()
    return " ".join(
        p if (i > 0 and p in _PARTICULAS) else "-".join(s[:1].upper() + s[1:] for s in p.split("-"))
        for i, p in enumerate(palavras)
    )


def frase(texto: str | None) -> str:
    """"SUPERIOR COMPLETO" -> "Superior completo"."""
    if not texto:
        return NAO_INFORMADO
    t = texto.strip().lower()
    return t[:1].upper() + t[1:]


def federacao(composicao: str | None) -> str | None:
    """"44-UNIÃO/11-PP" -> "UNIÃO/PP"."""
    if not composicao:
        return None
    return "/".join(re.sub(r"^\d+-", "", p.strip()) for p in composicao.split("/"))


def data_br(iso: str) -> str:
    """Data ou data e hora ISO -> "27/09/2026"."""
    d = datetime.fromisoformat(iso).date() if "T" in iso else date.fromisoformat(iso)
    return d.strftime("%d/%m/%Y")


def reais(valor: float) -> str:
    """5119829.39 -> "R$ 5.119.829,39"."""
    inteiro, centavos = f"{valor:,.2f}".split(".")
    return f"R$ {inteiro.replace(',', '.')},{centavos}"


def bens(declarou: bool | None, total: float | None, quantidade: int | None) -> str:
    if declarou is None:
        return NAO_INFORMADO
    if not declarou or total is None:
        return "Não declarou bens ao TSE"
    itens = "1 bem" if quantidade == 1 else f"{quantidade} bens"
    return f"{reais(total)}, soma de {itens} declarados"


def idade(anos: int | None) -> str:
    return NAO_INFORMADO if anos is None else f"{anos} anos no dia do 1º turno"


def link_rede(url: str) -> dict[str, str] | None:
    """Link clicável só para http(s) ou domínio; o resto não vira link.

    O TSE publica as URLs em maiúsculas: o domínio vai para minúsculas (não diferencia),
    o caminho fica como veio.
    """
    u = url.strip()
    m = re.match(r"^(?:(https?)://)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})(/\S*)?$", u, re.IGNORECASE)
    if not m:
        return None
    esquema = (m.group(1) or "https").lower()
    host = m.group(2).lower()
    caminho = m.group(3) or ""
    return {"href": f"{esquema}://{host}{caminho}", "texto": f"{host}{caminho}"}
