import re

SIGLAS = {
    r"\bGECA\b": "gastroenterocolite aguda",
    r"\bHAS\b": "hipertensão arterial sistêmica",
    r"\bDM\b": "diabetes mellitus",
    r"\bQP\b": "queixa principal",
    r"\bHDA\b": "história da doença atual",
    r"\bHPP\b": "histórico patológico pregresso",
}


def expandir_siglas(texto):
    if not texto:
        return texto

    resultado = texto
    for padrao, expansao in SIGLAS.items():
        resultado = re.sub(padrao, expansao, resultado, flags=re.IGNORECASE)

    return resultado
