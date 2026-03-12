import re


def sanitizar_texto(texto):

    if not texto:
        return ""

    texto = re.sub(r"(?i)paciente\s*:\s*.*", "", texto)
    texto = re.sub(r"(?i)nome\s*:\s*.*", "", texto)
    texto = re.sub(r"(?i)cpf\s*:\s*.*", "", texto)
    texto = re.sub(r"(?i)rg\s*:\s*.*", "", texto)
    texto = re.sub(r"(?i)data de nascimento\s*:\s*.*", "", texto)
    texto = re.sub(r"(?i)data de nasc\.*\s*:\s*.*", "", texto)
    texto = re.sub(r"(?i)matr[ií]cula\s*:\s*.*", "", texto)
    texto = re.sub(r"(?i)conv[eê]nio\s*:\s*.*", "", texto)

    texto = re.sub(r"(?i)crm\s*:\s*.*", "", texto)
    texto = re.sub(r"(?i)dr\.*\s*[a-z\s]+", "", texto)

    texto = re.sub(r"(?i)emitido em\s*:.*", "", texto)
    texto = re.sub(r"(?i)laudado por\s*:.*", "", texto)
    texto = re.sub(r"(?i)p[aá]gina\(s\).*", "", texto)

    texto = re.sub(r"(?i)prevent.*", "", texto)
    texto = re.sub(r"(?i)telemedicina.*", "", texto)

    texto = re.sub(r"\n\s*\n", "\n", texto)
    texto = re.sub(r"\s{2,}", " ", texto)

    return texto.strip()