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


# ======================================
# PARSER DE PARÂMETROS VITAIS
# ======================================

def normalizar_parametros(texto):

    if not texto or not texto.strip():
        return "PA - mmHg || FC - bpm || FR - irpm || Temp - °C || SatO2 - % || Glicemia - mg/dL"

    texto = texto.replace(",", ".")
    tokens = texto.split()

    pa = None
    fc = None
    fr = None
    temp = None
    sat = None
    glicemia = None

    for token in tokens:

        t = token.lower()

        # pressão arterial
        if re.fullmatch(r"\d{2,3}/\d{2,3}", token):
            if pa is None:
                pa = token

        # frequência cardíaca
        elif t.endswith("bpm"):
            valor = t.replace("bpm", "")
            if valor.isdigit():
                fc = valor

        # frequência respiratória
        elif t.endswith("irpm"):
            valor = t.replace("irpm", "")
            if valor.isdigit():
                fr = valor

        # saturação
        elif token.endswith("%"):
            valor = token.replace("%", "")
            if valor.isdigit():
                sat = valor

        # temperatura (30–43 °C)
        elif re.fullmatch(r"\d{2}(\.\d+)?", token):
            valor = float(token)
            if 30 <= valor <= 43 and temp is None:
                temp = token

        # glicemia (heurística)
        elif token.isdigit():
            valor = int(token)
            if 20 <= valor <= 600:
                glicemia = token

    return (
        f"PA {pa if pa else '-'} mmHg || "
        f"FC {fc if fc else '-'} bpm || "
        f"FR {fr if fr else '-'} irpm || "
        f"Temp {temp if temp else '-'} °C || "
        f"SatO2 {sat if sat else '-'} % || "
        f"Glicemia {glicemia if glicemia else '-'} mg/dL"
    )

# ===============================================
# PARSER — EXTRAIR CAMPOS DA EVOLUÇÃO ORGANIZADA
# ===============================================

def extrair_bloco(texto, titulo, proximos_titulos):

    inicio = texto.find(titulo)

    if inicio == -1:
        return ""

    inicio += len(titulo)

    fim = len(texto)

    for prox in proximos_titulos:

        pos = texto.find(prox, inicio)

        if pos != -1 and pos < fim:
            fim = pos

    return texto[inicio:fim].strip()


def extrair_campos_evolucao(texto):

    if not texto:
        return {}

    titulos = [
        "»» Impressão Diagnóstica:",
        "»» Queixa Principal:",
        "»» História da Doença Atual:",
        "»» Histórico Médico Pregresso:",
        "»» Exame Físico:",
        "»» Parâmetros:",
        "»» Evolução:",
        "»» Exames laboratoriais:",
        "»» Exames de imagem:",
        "»» Consulta com especialidades:",
        "»» Condutas:",
    ]

    return {

        "impressao": extrair_bloco(
            texto,
            "»» Impressão Diagnóstica:",
            titulos[1:]
        ),

        "qp": extrair_bloco(
            texto,
            "»» Queixa Principal:",
            titulos[2:]
        ),

        "hda": extrair_bloco(
            texto,
            "»» História da Doença Atual:",
            titulos[3:]
        ),

        "hpp": extrair_bloco(
            texto,
            "»» Histórico Médico Pregresso:",
            titulos[4:]
        ),

        "exame_fisico": extrair_bloco(
            texto,
            "»» Exame Físico:",
            titulos[5:]
        ),

        "parametros": extrair_bloco(
            texto,
            "»» Parâmetros:",
            titulos[6:]
        ),

        "evolucao": extrair_bloco(
            texto,
            "»» Evolução:",
            titulos[7:]
        ),

        "exames_lab": extrair_bloco(
            texto,
            "»» Exames laboratoriais:",
            titulos[8:]
        ),

        "exames_img": extrair_bloco(
            texto,
            "»» Exames de imagem:",
            titulos[9:]
        ),

        "especialidades": extrair_bloco(
            texto,
            "»» Consulta com especialidades:",
            titulos[10:]
        ),

        "condutas": extrair_bloco(
            texto,
            "»» Condutas:",
            []
        ),
    }