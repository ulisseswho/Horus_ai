import re


# ===============================================
# FUNÇÕES AUXILIARES
# ===============================================

def limpar_linha(linha):
    linha = linha.strip()

    if not linha:
        return ""

    linha = linha.replace("—", "-")
    linha = linha.replace("–", "-")
    linha = re.sub(r"^\-\s*", "", linha)
    linha = re.sub(r"\s+", " ", linha)

    return linha.strip()


def extrair_data(linha):
    if not linha:
        return None

    padroes = [
        r"\((\d{2}/\d{2}/\d{4})\)",
        r"\((\d{2}/\d{2})\)",
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}/\d{2})",
    ]

    for padrao in padroes:
        match = re.search(padrao, linha)
        if match:
            return match.group(1)

    return None


def remover_data_da_linha(linha):
    if not linha:
        return ""

    linha = re.sub(r"\(\d{2}/\d{2}/\d{4}\)", "", linha)
    linha = re.sub(r"\(\d{2}/\d{2}\)", "", linha)
    linha = re.sub(r"^\d{2}/\d{2}/\d{4}\s*[:\-]?\s*", "", linha)
    linha = re.sub(r"^\d{2}/\d{2}\s*[:\-]?\s*", "", linha)

    return linha.strip(" :-")


def normalizar_separadores(linha):
    if not linha:
        return ""

    linha = linha.replace(" | ", " || ")
    linha = linha.replace("|", " || ")
    linha = re.sub(r"\s*/\s*", " || ", linha)

    linha = re.sub(r"\s*\|\|\s*", " || ", linha)
    linha = re.sub(r"\s+", " ", linha)

    return linha.strip()


def classificar_categoria_laboratorial(linha_lower):
    if any(x in linha_lower for x in [
        "hb", "hemoglobina", "ht", "hematócrito", "hematocrito", "vcm", "hcm",
        "chcm", "rdw", "leuco", "leucó", "plaq", "plaqueta", "neut", "linf",
        "eos", "baso", "mono"
    ]):
        return "Hemograma"

    if any(x in linha_lower for x in [
        "creatinina", "crea", "ureia", "ur ", "tgo", "tgp", "ldh", "ferro",
        "ferritina", "bilit", "bilirrub", "bt ", "bd ", "bi ", "albumina",
        "proteína", "proteina", "glicose", "glicemia", "ciclosp"
    ]):
        return "Bioquímica"

    if any(x in linha_lower for x in [
        "na ", "sódio", "sodio", "k ", "potássio", "potassio", "mg ", "magnésio",
        "magnesio", "cl ", "cloro", "cálcio", "calcio"
    ]):
        return "Eletrólitos"

    if any(x in linha_lower for x in [
        "pcr", "vhs", "procalcitonina"
    ]):
        return "Marcadores inflamatórios"

    if any(x in linha_lower for x in [
        "inr", "ttpa", "tap", "coag"
    ]):
        return "Coagulação"

    if any(x in linha_lower for x in [
        "tsh", "t4", "cortisol", "aldolase", "cpk", "anti-jo1"
    ]):
        return "Endocrinometabólico"

    if any(x in linha_lower for x in [
        "fan", "anti-", "c3", "c4", "ch50", "fr ", "anticardiolipina",
        "anticoagulante lúpico", "anticoagulante lupico", "coombs"
    ]):
        return "Imunologia"

    if any(x in linha_lower for x in [
        "hiv", "hbsag", "anti-hbs", "anti-hbc", "anti-hcv", "vdrl", "cmv",
        "ebv", "parvovírus", "parvovirus", "igra"
    ]):
        return "Sorologias"

    if any(x in linha_lower for x in [
        "mielograma", "biópsia de medula", "biopsia de medula", "cariótipo",
        "cariotipo", "imunofenotipagem", "medula óssea", "medula ossea"
    ]):
        return "Exames medulares"

    if any(x in linha_lower for x in [
        "reticuló", "reticulo"
    ]):
        return "Reticulócitos"

    if any(x in linha_lower for x in [
        "eletroforese", "imunofixação", "imunofixacao", "proteínas séricas",
        "proteinas sericas", "hemoglobina a1", "hb fetal"
    ]):
        return "Proteinograma"

    return "Outros"


# ===============================================
# DETECTAR E ORGANIZAR EXAMES LABORATORIAIS
# ===============================================

def organizar_exames_laboratoriais(texto):

    if not texto or texto.strip() == "":
        return "-"

    linhas = texto.split("\n")

    padroes_lab = [
        "hb", "hemoglobina", "ht", "hematócrito", "hematocrito", "vcm", "hcm",
        "chcm", "rdw", "leuco", "leucó", "plaq", "plaqueta", "neut", "linf",
        "eos", "baso", "mono", "inr", "ttpa", "tap", "pcr", "ldh", "creatinina",
        "crea", "ureia", "ur ", "na ", "sódio", "sodio", "k ", "potássio",
        "potassio", "mg ", "magnésio", "magnesio", "tgo", "tgp", "ferro",
        "ferritina", "reticuló", "reticulo", "tsh", "t4", "fan", "coombs",
        "anticardiolipina", "anti-", "c3", "c4", "ch50", "vdrl", "cmv", "ebv",
        "hiv", "hbsag", "anti-hbs", "anti-hbc", "anti-hcv", "igra",
        "mielograma", "biópsia de medula", "biopsia de medula", "cariótipo",
        "cariotipo", "imunofenotipagem", "eletroforese", "imunofixação",
        "imunofixacao", "cortisol", "aldolase", "cpk", "anti-jo1"
    ]

    exames_formatados = []
    data_atual = None

    for linha in linhas:
        linha_limpa = limpar_linha(linha)

        if not linha_limpa:
            continue

        data_encontrada = extrair_data(linha_limpa)
        if data_encontrada:
            data_atual = data_encontrada

        linha_lower = linha_limpa.lower()

        if any(p in linha_lower for p in padroes_lab):
            categoria = classificar_categoria_laboratorial(linha_lower)
            conteudo = remover_data_da_linha(linha_limpa)
            conteudo = normalizar_separadores(conteudo)

            if data_atual:
                exames_formatados.append(f"[{data_atual}] – {categoria}: {conteudo}")
            else:
                exames_formatados.append(f"{categoria}: {conteudo}")

    if not exames_formatados:
        return "-"

    return "\n".join(exames_formatados)


# ===============================================
# DETECTAR E ORGANIZAR EXAMES DE IMAGEM
# ===============================================

def organizar_exames_laboratoriais(texto):

    if not texto or texto.strip() == "":
        return "-"

    linhas = texto.split("\n")

    padroes_lab = [
        "hb", "hemoglobina", "ht", "hematócrito", "hematocrito", "vcm", "hcm",
        "chcm", "rdw", "leuco", "leucó", "plaq", "plaqueta", "neut", "linf",
        "eos", "baso", "mono", "inr", "ttpa", "tap", "pcr", "ldh", "creatinina",
        "crea", "ureia", "ur ", "na ", "sódio", "sodio", "k ", "potássio",
        "potassio", "mg ", "magnésio", "magnesio", "tgo", "tgp", "ferro",
        "ferritina", "reticuló", "reticulo", "tsh", "t4", "fan", "coombs",
        "anticardiolipina", "anti-", "c3", "c4", "ch50", "vdrl", "cmv", "ebv",
        "hiv", "hbsag", "anti-hbs", "anti-hbc", "anti-hcv", "igra",
        "mielograma", "biópsia de medula", "biopsia de medula", "cariótipo",
        "cariotipo", "imunofenotipagem", "eletroforese", "imunofixação",
        "imunofixacao", "cortisol", "aldolase", "cpk", "anti-jo1",
        "ph", "pco2", "po2", "hco3", "lactato"
    ]

    bloqueios = [
        "eletrocardiograma",
        "ecg",
        "telemedicina",
        "prevent",
        "senior",
        "data de nasc",
        "data de nascimento",
        "matricula",
        "crm:",
        "emitido em",
        "laudado por",
        "filtros:",
        "velocidade:",
        "ritmo:",
        "conclus",
        "observa",
        "dados do paciente",
        "dados da solicit",
        "ecgnow"
    ]

    exames_formatados = []
    data_atual = None

    for linha in linhas:
        linha_limpa = limpar_linha(linha)

        if not linha_limpa:
            continue

        linha_lower = linha_limpa.lower()

        if any(b in linha_lower for b in bloqueios):
            continue

        data_encontrada = extrair_data(linha_limpa)
        if data_encontrada:
            data_atual = data_encontrada

        if not any(p in linha_lower for p in padroes_lab):
            continue

        if not re.search(r"\d", linha_limpa):
            continue

        conteudo = remover_data_da_linha(linha_limpa)
        conteudo = normalizar_separadores(conteudo)

        if len(conteudo) < 8:
            continue

        categoria = classificar_categoria_laboratorial(linha_lower)

        if any(x in linha_lower for x in ["ph", "pco2", "po2", "hco3", "lactato", "gasometr"]):
            categoria = "Gasometria"

        if data_atual:
            exames_formatados.append(f"[{data_atual}] – {categoria}: {conteudo}")
        else:
            exames_formatados.append(f"{categoria}: {conteudo}")

    if not exames_formatados:
        return "-"

    exames_unicos = []
    vistos = set()

    for exame in exames_formatados:
        if exame not in vistos:
            exames_unicos.append(exame)
            vistos.add(exame)

    return "\n".join(exames_unicos)


def montar_exames_imagem(texto):

    if not texto or texto.strip() == "":
        return "-"

    texto_lower = texto.lower()

    if "eletrocardiograma" in texto_lower or "ecg" in texto_lower:

        nome_exame = "Eletrocardiograma de repouso"
        data = None
        hora = None
        conclusao = None

        match_data_hora = re.search(
            r"data\s*:\s*(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2}:\d{2})",
            texto,
            flags=re.IGNORECASE
        )
        if match_data_hora:
            data = match_data_hora.group(1)
            hora = match_data_hora.group(2)

        if not data:
            match_data = re.search(
                r"data(?: exame)?\s*[:]\s*(\d{1,2}/\d{1,2}/\d{4})",
                texto,
                flags=re.IGNORECASE
            )
            if match_data:
                data = match_data.group(1)

        if not hora:
            match_hora = re.search(
                r"hora\s*[:]\s*(\d{2}:\d{2}:\d{2})",
                texto,
                flags=re.IGNORECASE
            )
            if match_hora:
                hora = match_hora.group(1)

        match_conclusao = re.search(
            r"conclus[aã]o(?:\(oes\))?\s*(.*?)(?:notas|observa|$)",
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )
        if match_conclusao:
            conclusao = re.sub(r"\s+", " ", match_conclusao.group(1)).strip(" .:-")

        if not conclusao and "ritmo: sinusal" in texto_lower:
            conclusao = "Eletrocardiograma dentro dos limites da normalidade."

        if conclusao:
            if data and hora:
                return f"[{data} – {hora}] – {nome_exame}: {conclusao}"
            elif data:
                return f"[{data}] – {nome_exame}: {conclusao}"
            else:
                return f"{nome_exame}: {conclusao}"

    linhas = texto.split("\n")

    exames_img = []
    vistos = set()
    data_atual = None
    hora_atual = None
    nome_exame = None

    padroes_titulo = [
        "tomografia",
        "tc ",
        "ressonância",
        "ressonancia",
        "rm ",
        "ultrassom",
        "ultrassonografia",
        "usg",
        "raio x",
        "rx",
        "ecott",
        "ecocardiograma",
        "mamografia",
        "colpocitologia",
        "birads",
        "birads-us",
        "eletrocardiograma",
        "ecg"
    ]

    padroes_conclusao = [
        "conclusão",
        "conclusao",
        "conclusões",
        "conclusoes",
        "impressão",
        "impressao",
        "resultado",
        "parecer"
    ]

    for i, linha in enumerate(linhas):
        linha_limpa = limpar_linha(linha)

        if not linha_limpa:
            continue

        linha_lower = linha_limpa.lower()

        data_encontrada = extrair_data(linha_limpa)
        if data_encontrada:
            data_atual = data_encontrada

        match_hora = re.search(r"\b(\d{2}:\d{2}:\d{2})\b", linha_limpa)
        if match_hora:
            hora_atual = match_hora.group(1)

        if any(p in linha_lower for p in padroes_titulo):
            nome_exame = remover_data_da_linha(linha_limpa)
            nome_exame = normalizar_separadores(nome_exame)

        if any(p in linha_lower for p in padroes_conclusao):

            conclusao_partes = []

            linha_sem_rotulo = re.sub(
                r"(?i)^(conclus[aã]o(?:\(oes\))?|conclus[oõ]es|impress[aã]o|resultado|parecer)\s*[:\-]?\s*",
                "",
                linha_limpa
            ).strip()

            if linha_sem_rotulo and linha_sem_rotulo.lower() not in [p.lower() for p in padroes_conclusao]:
                conclusao_partes.append(linha_sem_rotulo)

            for j in range(i + 1, min(i + 8, len(linhas))):
                prox = limpar_linha(linhas[j])

                if not prox:
                    break

                prox_lower = prox.lower()

                if any(p in prox_lower for p in padroes_titulo):
                    break

                if any(p in prox_lower for p in [
                    "dados do paciente",
                    "dados da solicitação",
                    "dados da solicitagao",
                    "laudo",
                    "notas",
                    "observa",
                    "filtros:",
                    "velocidade:"
                ]):
                    break

                conclusao_partes.append(prox)

            conclusao = " ".join(conclusao_partes).strip()
            conclusao = re.sub(r"\s+", " ", conclusao)

            if conclusao:
                if not nome_exame:
                    nome_exame = "Exame complementar"

                if data_atual and hora_atual:
                    registro = f"[{data_atual} – {hora_atual}] – {nome_exame}: {conclusao}"
                elif data_atual:
                    registro = f"[{data_atual}] – {nome_exame}: {conclusao}"
                else:
                    registro = f"{nome_exame}: {conclusao}"

                if registro not in vistos:
                    exames_img.append(registro)
                    vistos.add(registro)

    if not exames_img:
        return "-"

    return "\n".join(exames_img)
