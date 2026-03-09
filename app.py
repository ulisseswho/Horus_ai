import os
import re
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes

load_dotenv()

# ======================================
# CONTROLE DE PACIENTES
# ======================================

if "pacientes" not in st.session_state:
    st.session_state.pacientes = []

if "paciente_atual" not in st.session_state:
    st.session_state.paciente_atual = None

if "contador_paciente" not in st.session_state:
    st.session_state.contador_paciente = 0

if "editor_texto" not in st.session_state:
    st.session_state.editor_texto = ""


def criar_novo_paciente():
    st.session_state.contador_paciente += 1
    paciente_id = f"Paciente {st.session_state.contador_paciente:03d}"

    novo = {
        "id": paciente_id,
        "texto_bruto": "",
        "resultado": "",
        "sugestoes": ""
    }

    st.session_state.pacientes.append(novo)
    st.session_state.paciente_atual = len(st.session_state.pacientes) - 1
    st.session_state.editor_texto = ""
    st.session_state.texto_exames_novos = ""
    
def carregar_texto_paciente():
    paciente = st.session_state.pacientes[st.session_state.paciente_atual]
    st.session_state.editor_texto = paciente["texto_bruto"]


if len(st.session_state.pacientes) == 0:
    criar_novo_paciente()
    carregar_texto_paciente()

# ==============================
# FUNÇÕES OCR
# ==============================

def extrair_texto_imagem(arquivo):
    imagem = Image.open(arquivo)
    texto = pytesseract.image_to_string(imagem)
    return texto


def extrair_texto_pdf(arquivo):
    paginas = convert_from_bytes(arquivo.read())
    texto_total = ""

    for pagina in paginas:
        texto = pytesseract.image_to_string(pagina)
        texto_total += texto + "\n"

    return texto_total


# ==============================
# INTERFACE STREAMLIT
# ==============================

st.title("Hórus Clinical Assistant")
st.write("Organizador de texto clínico para Atendimento na Emergência e Evolução Médica")

with st.sidebar:
    st.subheader("Pacientes")

    if st.button("Novo Paciente"):
        criar_novo_paciente()

    nomes_pacientes = [p["id"] for p in st.session_state.pacientes]

    selecionado = st.selectbox(
        "Paciente atual",
        range(len(nomes_pacientes)),
        index=st.session_state.paciente_atual,
        format_func=lambda i: nomes_pacientes[i]
    )

    st.session_state.paciente_atual = selecionado

    st.divider()
    st.write("Resumo da sessão")
    st.write(f"Total de pacientes: {len(st.session_state.pacientes)}")

paciente = st.session_state.pacientes[st.session_state.paciente_atual]
st.caption(f"Paciente em edição: {paciente['id']}")

resultado_salvo = paciente.get("resultado", "")

if resultado_salvo:
    st.subheader("Texto organizado")
    st.text(resultado_salvo)

    st.subheader("Texto final para copiar")
    st.text_area(
        "Clique aqui, depois use Command + A e Command + C",
        value=resultado_salvo,
        height=500,
        key=f"resultado_{paciente['id']}"
    )

tipo_documento = st.selectbox(
    "Escolha o tipo de documento",
    ["Atendimento na Emergência", "Evolução Médica"]
)

usar_ia = st.checkbox("Usar IA para organizar o texto", value=True)
modelo_ia = st.text_input("Modelo da IA", value="gpt-4.1-mini")

mostrar_sugestoes_ia = st.checkbox("Mostrar sugestões baseadas em evidência (IA)", value=False)

texto = st.text_area(
    "Cole aqui o texto bruto do atendimento",
    height=350,
    key="editor_texto"
)

st.subheader("Atualização posterior")

texto_exames_novos = st.text_area(
    "Cole aqui apenas exames / parâmetros / imagem para atualizar depois",
    height=180,
    key="texto_exames_novos"
)

st.session_state.pacientes[st.session_state.paciente_atual]["texto_bruto"] = texto

# ==============================
# UPLOAD DE PDF OU IMAGEM
# ==============================

arquivos = st.file_uploader(
    "Envie PDF(s) ou imagem(ns) do prontuário",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if arquivos:
    texto_total_ocr = ""

    for arquivo in arquivos:
        if arquivo.type == "application/pdf":
            texto_extraido = extrair_texto_pdf(arquivo)
        else:
            texto_extraido = extrair_texto_imagem(arquivo)

        texto_total_ocr += f"\n\n===== {arquivo.name} =====\n\n"
        texto_total_ocr += texto_extraido

    st.subheader("Texto extraído dos arquivos")
    st.text_area(
        "Texto OCR",
        value=texto_total_ocr,
        height=300
    )

# ======================================
# INCORPORAR EXAMES AUTOMATICAMENTE
# ======================================

paciente = st.session_state.pacientes[st.session_state.paciente_atual]
documento_atual = paciente.get("resultado", "")

if documento_atual and texto_total_ocr.strip() and not st.session_state.get("ocr_processado"):

    blocos_novos = extrair_blocos(texto_total_ocr)

    novos_labs = organizar_exames_laboratoriais(blocos_novos["exames_laboratoriais"])
    novas_imagens = montar_exames_imagem(blocos_novos["exames_imagem"])

    # LABORATÓRIOS
    match_labs = re.search(
        r"(»» Exames Laboratoriais:\n)(.*?)(?=\n»»)",
        documento_atual,
        flags=re.S
    )

    if match_labs:
        labs_antigos = match_labs.group(2).strip()

        if labs_antigos == "-" or labs_antigos == "":
            labs_completo = novos_labs
        else:
            labs_completo = labs_antigos + "\n" + novos_labs

        documento_atual = re.sub(
            r"(»» Exames Laboratoriais:\n).*?(?=\n»»)",
            f"»» Exames Laboratoriais:\n{labs_completo}\n",
            documento_atual,
            flags=re.S
        )

    # IMAGEM
    match_img = re.search(
        r"(»» Exames de Imagem:\n)(.*?)(?=\n»»)",
        documento_atual,
        flags=re.S
    )

    if match_img:
        img_antigos = match_img.group(2).strip()

        if img_antigos == "-" or img_antigos == "":
            img_completo = novas_imagens
        else:
            img_completo = img_antigos + "\n" + novas_imagens

        documento_atual = re.sub(
            r"(»» Exames de Imagem:\n).*?(?=\n»»)",
            f"»» Exames de Imagem:\n{img_completo}\n",
            documento_atual,
            flags=re.S
        )

    st.session_state.pacientes[st.session_state.paciente_atual]["resultado"] = documento_atual

    st.success("Exames incorporados automaticamente ao documento.")
    st.session_state.ocr_processado = True

    texto = texto_total_ocr

    st.session_state.editor_texto = texto_total_ocr
    st.session_state.pacientes[st.session_state.paciente_atual]["texto_bruto"] = texto_total_ocr


# ======================================
# DICIONÁRIO DE SIGLAS
# ======================================

SIGLAS = {
    r"\bREG\b": "estado geral regular",
    r"\bBEG\b": "bom estado geral",
    r"\bMEG\b": "mau estado geral",
    r"\bCOTE\b": "consciente e orientado em tempo e espaço",
    r"\bBRNF\b": "bulhas rítmicas normofonéticas",
    r"MV\+": "murmúrio vesicular presente",
    r"\bAA\b": "ar ambiente",
    r"\bHAS\b": "hipertensão arterial sistêmica",
    r"\bDM\b": "diabetes mellitus",
    r"\bDLP\b": "dislipidemia",
    r"\bDAC\b": "doença arterial coronariana",
    r"\bDRC\b": "doença renal crônica",
    r"\bAVC\b": "acidente vascular cerebral",
    r"\bAVCI\b": "acidente vascular cerebral isquêmico",
    r"\bAVCH\b": "acidente vascular cerebral hemorrágico",
    r"\bIAM\b": "infarto agudo do miocárdio",
    r"\bICC\b": "insuficiência cardíaca congestiva",
    r"\bIC\b": "insuficiência cardíaca",
    r"\bDPOC\b": "doença pulmonar obstrutiva crônica",
    r"\bTVP\b": "trombose venosa profunda",
    r"\bTEP\b": "tromboembolismo pulmonar",
    r"\bPCR\b": "proteína C reativa",
    r"\bHPP\b": "histórico patológico pregresso",
    r"\bHMP\b": "histórico médico pregresso",
    r"\bHDA\b": "história da doença atual",
    r"\bHMA\b": "história da moléstia atual",
    r"\bQP\b": "queixa principal",
    r"\bAAA\b": "afebril, acianótico, anictérico",
    r"\bACIANO\b": "acianótico",
    r"\bANICT\b": "anictérico",
    r"\bHIDR\b": "hidratado",
    r"\bHIPOCOR\b": "hipocorado",
    r"\bNORMOCOR\b": "normocorado",
    r"\bRCR\b": "ritmo cardíaco regular",
    r"\bMUV\b": "murmúrio vesicular universal",
    r"\bDVA\b": "drogas vasoativas",
    r"\bHIPOCORADA\b": "hipocorada",
    r"\bHIPOCORADO\b": "hipocorado",
}


def expandir_siglas(texto):
    if not texto:
        return texto

    resultado = texto

    for padrao, expansao in SIGLAS.items():
        resultado = re.sub(padrao, expansao, resultado, flags=re.IGNORECASE)

    return resultado


def value_replace_case_insensitive(texto, antigo, novo):
    return re.sub(re.escape(antigo), novo, texto, flags=re.IGNORECASE)


# ======================================
# IDENTIFICAÇÃO DE BLOCOS
# ======================================

SINONIMOS = {
    "impressao_diagnostica": [
        "impressão diagnóstica",
        "impressao diagnostica",
        "diagnósticos",
        "diagnosticos",
        "hipóteses diagnósticas",
        "hipoteses diagnosticas",
        "hd"
    ],
    "queixa_principal": [
        "queixa principal",
        "qp",
        "queixa",
        "motivo da consulta"
    ],
    "hda": [
        "história da doença atual",
        "historia da doenca atual",
        "hda",
        "hma",
        "história clínica",
        "historia clinica"
    ],
    "hmp": [
        "histórico médico pregresso",
        "historico medico pregresso",
        "histórico patológico pregresso",
        "historico patologico pregresso",
        "hpp",
        "hmp",
        "antecedentes"
    ],
    "exame_fisico": [
        "exame físico",
        "exame fisico",
        "ef"
    ],
    "parametros": [
        "parâmetros",
        "parametros",
        "sinais vitais",
        "sv"
    ],
    "evolucao": [
        "evolução",
        "evolucao"
    ],
    "exames_laboratoriais": [
        "exames laboratoriais",
        "laboratório",
        "laboratorio",
        "labs",
        "laboratoriais"
    ],
    "exames_imagem": [
        "exames de imagem",
        "imagem",
        "imagens"
    ],
    "especialidades": [
        "consulta com especialidades",
        "parecer",
        "pareceres",
        "interconsulta",
        "especialidades"
    ],
 
    "condutas": [
        "condutas",
        "conduta",
        "plano"
    ]
}


def limpar_titulo_linha(linha):
    return re.sub(r'^[\s»>\-•*]+', '', linha.strip(), flags=re.IGNORECASE)


def identificar_bloco(linha):
    linha_limpa = limpar_titulo_linha(linha)
    linha_lower = linha_limpa.lower()

    for nome_bloco, lista_sinonimos in SINONIMOS.items():
        for sinonimo in lista_sinonimos:
            padrao = rf"^{re.escape(sinonimo)}\s*:"
            if re.search(padrao, linha_lower, re.IGNORECASE):
                resto = re.split(
                    rf"^{re.escape(sinonimo)}\s*:",
                    linha_limpa,
                    maxsplit=1,
                    flags=re.IGNORECASE
                )
                conteudo = resto[1].strip() if len(resto) > 1 else ""
                return nome_bloco, conteudo

    return None, None


def extrair_blocos(texto):
    blocos = {k: "-" for k in SINONIMOS}

    texto = re.sub(r"\s+#", "\n#", texto)
    texto = re.sub(r"(?i)\s+(hda:|hma:|hpp:|hmp:|qp:|queixa principal:|exames laboratoriais:|exames de imagem:|condutas:|conduta:|parâmetros:|parametros:|ao exame:)", r"\n\1", texto)

    linhas = texto.splitlines()
    bloco_atual = None
    buffer = []

    for linha in linhas:
        nome_bloco, conteudo = identificar_bloco(linha)

        if nome_bloco:
            if bloco_atual:
                conteudo_bloco = "\n".join(buffer).strip()
                blocos[bloco_atual] = conteudo_bloco if conteudo_bloco else "-"

            bloco_atual = nome_bloco
            buffer = []

            if conteudo:
                buffer.append(conteudo)
        else:
            if bloco_atual:
                buffer.append(linha.strip())

    if bloco_atual:
        conteudo_bloco = "\n".join(buffer).strip()
        blocos[bloco_atual] = conteudo_bloco if conteudo_bloco else "-"

    if blocos["hda"] == "-" and texto.strip():
        blocos["hda"] = texto.strip()

    return blocos


# ======================================
# FUNÇÕES AUXILIARES
# ======================================

def extrair_item_hmp(bloco_hmp, rotulos):
    if not bloco_hmp or bloco_hmp == "-":
        return "-"

    for linha in bloco_hmp.splitlines():
        linha_limpa = linha.strip()

        for rotulo in rotulos:
            padrao = rf"^{re.escape(rotulo)}\s*:\s*(.+)$"
            achado = re.search(padrao, linha_limpa, re.IGNORECASE)
            if achado:
                return expandir_siglas(achado.group(1).strip())

    return "-"


def enumerar_itens(texto_bloco):
    if not texto_bloco or texto_bloco.strip() in ["", "-"]:
        return "1. -"

    linhas = [expandir_siglas(l.strip(" -•\t")) for l in texto_bloco.splitlines() if l.strip()]

    if not linhas:
        return "1. -"

    if len(linhas) == 1:
        partes = [p.strip() for p in re.split(r"\.\s+|\;\s+", linhas[0]) if p.strip()]
        if len(partes) > 1:
            linhas = partes

    resultado = []
    for i, item in enumerate(linhas, 1):
        resultado.append(f"{i}. {item}")

    return "\n".join(resultado)


def limpar_rotulo_duplicado(linha, rotulo):
    padrao = rf"^\s*{re.escape(rotulo)}\s*:\s*"
    return re.sub(padrao, "", linha.strip(), flags=re.IGNORECASE)


# ======================================
# EXAME FÍSICO
# ======================================

def montar_exame_fisico(bloco_extraido):
    modelo = {
        "Ectoscopia": "estado geral regular, consciente, orientado em tempo e espaço, afebril, acianótico, anictérico, normocorado, hidratado, eupneico.",
        "Neurológico": "Glasgow 15, pupilas isocóricas e fotorreagentes, sem déficits neurológicos focais aparentes.",
        "Cardiovascular": "bulhas rítmicas normofonéticas em 2 tempos, sem sopros, pulsos periféricos palpáveis e simétricos, perfusão periférica preservada.",
        "Respiratório": "murmúrio vesicular presente em ambos os hemitórax, sem ruídos adventícios.",
        "Abdome": "plano, flácido, indolor à palpação, sem sinais de irritação peritoneal.",
        "Extremidades": "sem edema, sem cianose, perfusão periférica preservada."
    }

    if bloco_extraido and bloco_extraido != "-":
        bloco_extraido = expandir_siglas(bloco_extraido)
        linhas = [l.strip() for l in bloco_extraido.splitlines() if l.strip()]

        for linha in linhas:
            linha_lower = linha.lower()

            if "neuro" in linha_lower or "neurol" in linha_lower:
                valor = limpar_rotulo_duplicado(linha, "Neuro")
                valor = limpar_rotulo_duplicado(valor, "Neurológico")
                valor = valor.strip().rstrip(".")
                if valor:
                    modelo["Neurológico"] = f"{valor}, Glasgow 15, pupilas isocóricas e fotorreagentes, sem déficits neurológicos focais aparentes."

            elif "cardio" in linha_lower or "bulha" in linha_lower or "sopro" in linha_lower or "pulso" in linha_lower:
                valor = limpar_rotulo_duplicado(linha, "Cardiovascular")
                valor = valor.strip().rstrip(".")
                if valor:
                    valor = value_replace_case_insensitive(valor, "bulhas rítmicas normofonéticas", "bulhas rítmicas normofonéticas em 2 tempos")
                    modelo["Cardiovascular"] = f"{valor}, sem sopros, pulsos periféricos palpáveis e simétricos, perfusão periférica preservada."

            elif "resp" in linha_lower or "vesicular" in linha_lower or "mv+" in linha_lower or "murmúrio vesicular" in linha_lower or "murmurio vesicular" in linha_lower:
                valor = limpar_rotulo_duplicado(linha, "Respiratório")
                valor = value_replace_case_insensitive(valor, "MV+", "murmúrio vesicular presente")
                valor = value_replace_case_insensitive(valor, "murmúrio vesicular presente bilateralmente", "murmúrio vesicular presente em ambos os hemitórax, sem ruídos adventícios")
                valor = value_replace_case_insensitive(valor, "murmúrio vesicular presente", "murmúrio vesicular presente em ambos os hemitórax, sem ruídos adventícios")
                valor = value_replace_case_insensitive(valor, "murmurio vesicular presente", "murmúrio vesicular presente em ambos os hemitórax, sem ruídos adventícios")
                valor = valor.strip().rstrip(".")
                if valor:
                    modelo["Respiratório"] = f"{valor}."

            elif "abd" in linha_lower:
                valor = limpar_rotulo_duplicado(linha, "Abdome")
                valor = valor.strip().rstrip(".")
                if valor:
                    if "palpação" not in valor.lower():
                        valor = f"{valor}, à palpação"
                    modelo["Abdome"] = f"{valor}."

            elif "extrem" in linha_lower or "mmii" in linha_lower or "mmss" in linha_lower:
                valor = limpar_rotulo_duplicado(linha, "Extremidades")
                valor = valor.strip().rstrip(".")
                if valor:
                    if "perfusão" not in valor.lower() and "perfusao" not in valor.lower():
                        valor = f"{valor}, perfusão periférica preservada"
                    modelo["Extremidades"] = f"{valor}."

            else:
                valor = limpar_rotulo_duplicado(linha, "Ectoscopia")
                valor = valor.strip().rstrip(".")
                if valor:
                    complemento = "acianótico, anictérico, normocorado, hidratado"
                    modelo["Ectoscopia"] = f"{valor} ({complemento})."

    resultado = "\n".join([
        f"Ectoscopia: {modelo['Ectoscopia']}",
        f"Neurológico: {modelo['Neurológico']}",
        f"Cardiovascular: {modelo['Cardiovascular']}",
        f"Respiratório: {modelo['Respiratório']}",
        f"Abdome: {modelo['Abdome']}",
        f"Extremidades: {modelo['Extremidades']}",
    ])
    return resultado


# ======================================
# PARÂMETROS
# ======================================

def extrair_hora_parametros(bloco):
    if not bloco or bloco == "-":
        return "-"

    match = re.search(r"(\d{2}:\d{2})", bloco)
    if match:
        return match.group(1)

    return "-"


def montar_parametros(bloco):
    modelo = "PA - mmHg || FC - bpm || FR - irpm || Temp - °C || SatO2 - % || Glicemia - mg/dL || Hora -"

    if bloco and bloco != "-":
        hora = extrair_hora_parametros(bloco)
        bloco_limpo = expandir_siglas(bloco).strip()

        substituicoes = [
            (r"\bPA\s*(\d+/\d+)", r"PA \1 mmHg"),
            (r"\bFC\s*(\d+)\b(?!\s*bpm)", r"FC \1 bpm"),
            (r"\bFR\s*(\d+)\b(?!\s*irpm)", r"FR \1 irpm"),
            (r"\bTemp\s*([0-9]+[.,]?[0-9]*)\b(?!\s*°C)", r"Temp \1°C"),
            (r"\bSatO2\s*(\d+)\b(?!\s*%)", r"SatO2 \1%"),
            (r"\bglicemia capilar\s*(\d+)\b", r"Glicemia \1 mg/dL"),
            (r"\bGlicemia\s*(\d+)\b(?!\s*mg/dL)", r"Glicemia \1 mg/dL"),
        ]

        for padrao, repl in substituicoes:
            bloco_limpo = re.sub(padrao, repl, bloco_limpo, flags=re.IGNORECASE)

        if "Hora" not in bloco_limpo and "hora" not in bloco_limpo:
            return f"{bloco_limpo} || Hora {hora}"
        return bloco_limpo

    return modelo


# ======================================
# IMAGEM
# ======================================

def extrair_data_hora_imagem(bloco):
    if not bloco or bloco == "-":
        return "-", "-"

    match_data_hora = re.search(r"(\d{2}/\d{2}/\d{4})\s*[–-]?\s*(\d{2}:\d{2})", bloco)
    if match_data_hora:
        return match_data_hora.group(1), match_data_hora.group(2)

    match_data = re.search(r"(\d{2}/\d{2}/\d{4})", bloco)
    if match_data:
        return match_data.group(1), "-"

    return "-", "-"


def normalizar_nome_imagem(bloco):
    bloco = value_replace_case_insensitive(bloco, "Tomografia Computadorizada", "TC")
    bloco = value_replace_case_insensitive(bloco, "Ressonância Magnética", "RM")
    bloco = value_replace_case_insensitive(bloco, "Raio-X", "RX")
    bloco = value_replace_case_insensitive(bloco, "radiografia", "RX")
    return bloco


def montar_exames_imagem(bloco):
    if not bloco or bloco == "-":
        return "[DATA – HORA] – -"

    data, hora = extrair_data_hora_imagem(bloco)
    bloco_limpo = expandir_siglas(bloco).strip()
    bloco_limpo = normalizar_nome_imagem(bloco_limpo)

    bloco_limpo = re.sub(r"^\[\d{2}/\d{2}/\d{4}(?:\s*[–-]\s*\d{2}:\d{2}|\s*[–-]\s*-)?\]\s*[–-]\s*", "", bloco_limpo)
    bloco_limpo = re.sub(r"\(?\d{2}/\d{2}/\d{4}\s*\d{2}:\d{2}\)?", "", bloco_limpo).strip(" :-")

    return f"[{data} – {hora}] – {bloco_limpo}"


# ======================================
# LABORATÓRIOS
# ======================================

REFERENCIAS_LABS = {
    "Hb": (12.0, 16.0),
    "Ht": (36.0, 47.0),
    "Leucócitos": (4000, 11000),
    "Segmentados": (40, 74),
    "Plaquetas": (150000, 400000),
    "Glicose": (70, 99),
    "Ureia": (15, 40),
    "Creatinina": (0.6, 1.3),
    "Sódio": (135, 145),
    "Potássio": (3.5, 5.0),
    "PCR": (0, 5),
    "Lactato": (0.5, 2.0),
}


def classificar_valor(nome, valor):
    if nome not in REFERENCIAS_LABS:
        return None

    ref_min, ref_max = REFERENCIAS_LABS[nome]

    try:
        valor_float = float(str(valor).replace(",", "."))
    except ValueError:
        return None

    if valor_float < ref_min:
        return "Reduzido"
    if valor_float > ref_max:
        return "Elevado"
    return None


def formatar_item_lab(nome, valor, unidade):
    status = classificar_valor(nome, valor)
    valor_txt = str(valor).replace(",", ",")

    if status:
        return f"{nome} ({status}) {valor_txt} {unidade}".strip()
    return f"{nome} {valor_txt} {unidade}".strip()


def procurar_valor(bloco, padroes):
    for padrao in padroes:
        match = re.search(padrao, bloco, re.IGNORECASE)
        if match:
            return match.group(1).replace(",", ".").strip()
    return None


def montar_linha_categoria(nome_categoria, itens):
    itens_validos = [item for item in itens if item]
    if not itens_validos:
        return None
    return f"{nome_categoria}: " + " || ".join(itens_validos)


def extrair_data_hora_laboratorio(bloco_labs):
    if not bloco_labs or bloco_labs == "-":
        return "-", "-"

    padrao_data_hora = r"(\d{2}/\d{2}/\d{4})\s*[–-]?\s*(\d{2}:\d{2})"
    match = re.search(padrao_data_hora, bloco_labs)

    if match:
        return match.group(1), match.group(2)

    padrao_data = r"(\d{2}/\d{2}/\d{4})"
    match_data = re.search(padrao_data, bloco_labs)
    if match_data:
        return match_data.group(1), "-"

    return "-", "-"


def organizar_exames_laboratoriais(bloco_labs):
    if not bloco_labs or bloco_labs == "-":
        return "-"

    data_exame, hora_exame = extrair_data_hora_laboratorio(bloco_labs)

    hemograma = []
    coag = []
    bioq = []
    eletrolitos = []
    inflam = []
    gaso = []
    eas = []

    hb = procurar_valor(bloco_labs, [r"(?:\bhb\b|hemoglobina)[^\d]{0,20}(\d+[.,]?\d*)"])
    if hb:
        hemograma.append(formatar_item_lab("Hemoglobina", hb, "g/dL"))

    ht = procurar_valor(bloco_labs, [r"(?:\bht\b|hemat[oó]crito)[^\d]{0,20}(\d+[.,]?\d*)"])
    if ht:
        hemograma.append(formatar_item_lab("Hematócrito", ht, "%"))

    leuc = procurar_valor(bloco_labs, [r"(?:leuc[oó]citos)[^\d]{0,20}(\d+[.,]?\d*)"])
    if leuc:
        hemograma.append(formatar_item_lab("Leucócitos", leuc, "/mm³"))

    seg = procurar_valor(bloco_labs, [r"(?:segmentados)[^\d]{0,20}(\d+[.,]?\d*)"])
    if seg:
        hemograma.append(formatar_item_lab("Segmentados", seg, "%"))

    plaq = procurar_valor(bloco_labs, [r"(?:plaquetas)[^\d]{0,20}(\d+[.,]?\d*)"])
    if plaq:
        hemograma.append(formatar_item_lab("Plaquetas", plaq, "/mm³"))

    ap = procurar_valor(bloco_labs, [r"(?:\bap\b)[^\d]{0,20}(\d+[.,]?\d*)"])
    if ap:
        coag.append(f"AP {ap}%")

    tp = procurar_valor(bloco_labs, [r"(?:\btp\b)[^\d]{0,20}(\d+[.,]?\d*)"])
    if tp:
        coag.append(f"TP {tp} s")

    inr = procurar_valor(bloco_labs, [r"(?:\binr\b)[^\d]{0,20}(\d+[.,]?\d*)"])
    if inr:
        coag.append(f"INR {inr}")

    glicose = procurar_valor(bloco_labs, [r"(?:glicose|glicemia)[^\d]{0,20}(\d+[.,]?\d*)"])
    if glicose:
        bioq.append(formatar_item_lab("Glicose", glicose, "mg/dL"))

    ureia = procurar_valor(bloco_labs, [r"(?:ur[eé]ia|ureia)[^\d]{0,20}(\d+[.,]?\d*)"])
    if ureia:
        bioq.append(formatar_item_lab("Ureia", ureia, "mg/dL"))

    creat = procurar_valor(bloco_labs, [r"(?:creatinina)[^\d]{0,20}(\d+[.,]?\d*)"])
    if creat:
        bioq.append(formatar_item_lab("Creatinina", creat, "mg/dL"))

    sodio = procurar_valor(bloco_labs, [r"(?:s[oó]dio|\bna\b|\bna\+)[^\d]{0,20}(\d+[.,]?\d*)"])
    if sodio:
        eletrolitos.append(formatar_item_lab("Sódio", sodio, "mEq/L"))

    potassio = procurar_valor(bloco_labs, [r"(?:pot[aá]ssio|\bk\b|\bk\+)[^\d]{0,20}(\d+[.,]?\d*)"])
    if potassio:
        eletrolitos.append(formatar_item_lab("Potássio", potassio, "mEq/L"))

    pcr = procurar_valor(bloco_labs, [r"(?:\bpcr\b|prote[ií]na c reativa)[^\d]{0,20}(\d+[.,]?\d*)"])
    if pcr:
        inflam.append(formatar_item_lab("Proteína C reativa", pcr, "mg/L"))

    ph = procurar_valor(bloco_labs, [r"(?:\bph\b)[^\d]{0,20}(\d+[.,]?\d*)"])
    if ph:
        gaso.append(f"pH {ph}")

    lactato = procurar_valor(bloco_labs, [r"(?:lactato)[^\d]{0,20}(\d+[.,]?\d*)"])
    if lactato:
        gaso.append(formatar_item_lab("Lactato", lactato, "mmol/L"))

    sat = procurar_valor(bloco_labs, [r"(?:satura[cç][aã]o|sat)[^\d]{0,20}(\d+[.,]?\d*)"])
    if sat:
        gaso.append(f"Saturação {sat}")

    leuc_eas = re.search(r"(?:eas.*?leuc[oó]citos\s*(negativo|positivo|\d+[.,]?\d*))", bloco_labs, re.IGNORECASE | re.DOTALL)
    if leuc_eas:
        eas.append(f"Leucócitos {leuc_eas.group(1)}")

    hemacias_eas = re.search(r"(?:eas.*?hem[aá]cias\s*(negativo|positivo|\d+[.,]?\d*))", bloco_labs, re.IGNORECASE | re.DOTALL)
    if hemacias_eas:
        eas.append(f"Hemácias {hemacias_eas.group(1)}")

    linhas = []

    linha_hemograma = montar_linha_categoria("Hemograma", hemograma)
    if linha_hemograma:
        linhas.append(f"[{data_exame} – {hora_exame}] – {linha_hemograma}")

    linha_coag = montar_linha_categoria("Coagulação", coag)
    if linha_coag:
        linhas.append(f"[{data_exame} – {hora_exame}] – {linha_coag}")

    linha_bioq = montar_linha_categoria("Bioquímica", bioq)
    if linha_bioq:
        linhas.append(f"[{data_exame} – {hora_exame}] – {linha_bioq}")

    linha_elet = montar_linha_categoria("Eletrólitos", eletrolitos)
    if linha_elet:
        linhas.append(f"[{data_exame} – {hora_exame}] – {linha_elet}")

    linha_inflam = montar_linha_categoria("Marcadores inflamatórios", inflam)
    if linha_inflam:
        linhas.append(f"[{data_exame} – {hora_exame}] – {linha_inflam}")

    linha_gaso = montar_linha_categoria("Gasometria", gaso)
    if linha_gaso:
        linhas.append(f"[{data_exame} – {hora_exame}] – {linha_gaso}")

    linha_eas = montar_linha_categoria("EAS", eas)
    if linha_eas:
        linhas.append(f"[{data_exame} – {hora_exame}] – {linha_eas}")

    if not linhas:
        return expandir_siglas(bloco_labs)

    return "\n".join(linhas)


# ======================================
# PROMPTS DE IA
# ======================================

def prompt_atendimento_emergencia(texto_bruto):
    return f"""
Você é um assistente de organização clínica para médico emergencista.
Reorganize o texto abaixo no modelo EXATO a seguir.

Regras obrigatórias:
- Não invente dados ausentes.
- Se algo não existir, coloque "-".
- Mantenha linguagem médica formal em português.
- Enumere Impressão Diagnóstica e Condutas.
- Expanda siglas médicas comuns quando apropriado.
- Não escreva explicações fora do modelo.
- Em Exame Físico, complete os campos com padrão normal quando o texto vier incompleto.
- Em Parâmetros, use exatamente este formato:
PA X/X mmHg || FC X bpm || FR X irpm || Temp X°C || SatO2 X% || Glicemia X mg/dL || Hora XX:XX
- Em Exames Laboratoriais, organize do mais recente para o mais antigo, usando exatamente o formato:
[DATA – HORA] – CATEGORIA: item || item || item
- Categorias possíveis: Hemograma, Coagulação, Bioquímica, Eletrólitos, Marcadores inflamatórios, Gasometria, EAS, Função hepática.
- Em Exames de Imagem, use exatamente o formato:
[DATA – HORA] – EXAME: descrição
- Se houver mais de um exame de imagem, manter um por linha.
- Em Condutas, use verbos no infinitivo e linguagem objetiva.
- Evite siglas desnecessárias na saída final.
- Não reinterpretar achados semiológicos. Preserve literalmente termos como “hipocorada (1+/4+)”, “bulhas hipofonéticas”, “MUV”, “AAA”, “TEC ~3seg” quando já estiverem claros no texto.
- Não substituir achados por sinônimos de intensidade diferente. Exemplo: “hipocorada (1+/4+)” não pode virar “palidez leve” nem “palidez acentuada”.
- Em caso de dúvida, prefira manter o texto original organizado em vez de resumir ou parafrasear.
- Não criar condutas, achados ou interpretações que não estejam explicitamente descritos.
- AAA deve ser preservado e expandido como “afebril, acianótica, anictérica”.
- Não deslocar achados entre sistemas. Exemplo: edema de membros inferiores não deve ser inserido em Cardiovascular se não estiver explicitamente descrito.
- POCUS deve ser descrito como “ultrassonografia à beira-leito (POCUS)” e nunca como “pulso-onda contínuo”.
- Em Condutas, incluir apenas medidas explicitamente descritas no texto-fonte; não acrescentar monitorização, suspensão de antibiótico ou outras medidas inferidas.
- Preserve a data completa no formato DD/MM/AAAA sempre que ela estiver disponível no texto-fonte.
- Se a hora não estiver disponível, usar “-” sem inventar horário.
- Em Exame Físico, quando houver siglas claras no texto-fonte, expandi-las sem alterar o significado clínico original.
- Em caso de ambiguidade no exame físico, preferir transcrever o achado original organizado em vez de reinterpretá-lo.
- Não transformar “MUV” em expressão diferente do seu significado clínico sem contexto suficiente; se necessário, manter de forma conservadora.
- Não mover informações de regulação, transferência, vaga zero ou transporte para “Consulta com Especialidades”; essas informações devem ir em Condutas.
- “Consulta com Especialidades” só deve ser preenchido quando houver parecer, interconsulta ou avaliação por especialidade explicitamente descrita.
- Não resumir ou suavizar achados clínicos potencialmente relevantes.
- Preserve a graduação original de sinais clínicos exatamente como no texto-fonte.

MODELO EXATO:

»» Atendimento na Emergência

»» Impressão Diagnóstica:
1. -

»» Queixa Principal:
-

»» História da Doença Atual:
-

»» Histórico Médico Pregresso:
Comorbidades: -
Cirurgias prévias: -
Alergias: -
Uso de medicamentos contínuos: -
História familiar relevante: -

»» Exame Físico:
Ectoscopia: -
Neurológico: -
Cardiovascular: -
Respiratório: -
Abdome: -
Extremidades: -

»» Parâmetros:
PA - mmHg || FC - bpm || FR - irpm || Temp - °C || SatO2 - % || Glicemia - mg/dL || Hora -

»» Exames Laboratoriais:
-

»» Exames de Imagem:
-

»» Consulta com Especialidades:
-

»» Condutas:
1. -

TEXTO BRUTO:
{texto_bruto}
"""


def prompt_evolucao_medica(texto_bruto):
    return f"""
Você é um assistente de organização clínica para médico emergencista.
Reorganize o texto abaixo no modelo EXATO a seguir.

Regras obrigatórias:
- Não invente dados ausentes.
- Se algo não existir, coloque "-".
- Mantenha linguagem médica formal em português.
- Enumere Impressão Diagnóstica e Condutas.
- Expanda siglas médicas comuns quando apropriado.
- Não escreva explicações fora do modelo.
- Em Exame Físico, complete os campos com padrão normal quando o texto vier incompleto.
- Em Parâmetros, use exatamente este formato:
PA X/X mmHg || FC X bpm || FR X irpm || Temp X°C || SatO2 X% || Glicemia X mg/dL || Hora XX:XX
- Em Exames Laboratoriais, organize do mais recente para o mais antigo, usando exatamente o formato:
[DATA – HORA] – CATEGORIA: item || item || item
- Categorias possíveis: Hemograma, Coagulação, Bioquímica, Eletrólitos, Marcadores inflamatórios, Gasometria, EAS, Função hepática.
- Em Exames de Imagem, use exatamente o formato:
[DATA – HORA] – EXAME: descrição
- Se houver mais de um exame de imagem, manter um por linha.
- Em Condutas, use verbos no infinitivo e linguagem objetiva.
- Evite siglas desnecessárias na saída final.
- Não reinterpretar achados semiológicos. Preserve literalmente termos como “hipocorada (1+/4+)”, “bulhas hipofonéticas”, “MUV”, “AAA”, “TEC ~3seg” quando já estiverem claros no texto.
- Não substituir achados por sinônimos de intensidade diferente. Exemplo: “hipocorada (1+/4+)” não pode virar “palidez leve” nem “palidez acentuada”.
- Em caso de dúvida, prefira manter o texto original organizado em vez de resumir ou parafrasear.
- Não criar condutas, achados ou interpretações que não estejam explicitamente descritos.
- AAA deve ser preservado e expandido como “afebril, acianótica, anictérica”.
- Não deslocar achados entre sistemas. Exemplo: edema de membros inferiores não deve ser inserido em Cardiovascular se não estiver explicitamente descrito.
- POCUS deve ser descrito como “ultrassonografia à beira-leito (POCUS)” e nunca como “pulso-onda contínuo”.
- Em Condutas, incluir apenas medidas explicitamente descritas no texto-fonte; não acrescentar monitorização, suspensão de antibiótico ou outras medidas inferidas. 
- Preserve a data completa no formato DD/MM/AAAA sempre que ela estiver disponível no texto-fonte.
- Se a hora não estiver disponível, usar “-” sem inventar horário.
- Em Exame Físico, quando houver siglas claras no texto-fonte, expandi-las sem alterar o significado clínico original.
- Em caso de ambiguidade no exame físico, preferir transcrever o achado original organizado em vez de reinterpretá-lo.
- Não transformar “MUV” em expressão diferente do seu significado clínico sem contexto suficiente; se necessário, manter de forma conservadora.
- Não mover informações de regulação, transferência, vaga zero ou transporte para “Consulta com Especialidades”; essas informações devem ir em Condutas.
- “Consulta com Especialidades” só deve ser preenchido quando houver parecer, interconsulta ou avaliação por especialidade explicitamente descrita.
- Não resumir ou suavizar achados clínicos potencialmente relevantes.
- Preserve a graduação original de sinais clínicos exatamente como no texto-fonte.

MODELO EXATO:

»» Evolução Médica

»» Impressão Diagnóstica:
1. -

»» Queixa Principal:
-

»» História da Doença Atual:
-

»» Histórico Médico Pregresso:
Comorbidades: -
Cirurgias prévias: -
Alergias: -
Uso de medicamentos contínuos: -
História familiar relevante: -

»» Exame Físico:
Ectoscopia: -
Neurológico: -
Cardiovascular: -
Respiratório: -
Abdome: -
Extremidades: -

»» Parâmetros:
PA - mmHg || FC - bpm || FR - irpm || Temp - °C || SatO2 - % || Glicemia - mg/dL || Hora -

»» Evolução:
-

»» Exames Laboratoriais:
-

»» Exames de Imagem:
-

»» Consulta com Especialidades:
-

»» Condutas:
1. -

TEXTO BRUTO:
{texto_bruto}
"""


def organizar_com_ia(texto_bruto, tipo_documento, modelo):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente.")

    client = OpenAI(api_key=api_key)

    if tipo_documento == "Atendimento na Emergência":
        prompt = prompt_atendimento_emergencia(texto_bruto)
    else:
        prompt = prompt_evolucao_medica(texto_bruto)

    response = client.responses.create(
        model=modelo,
        input=prompt
    )

    return response.output_text


def gerar_sugestoes_evidencia(texto_bruto, modelo):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente.")

    client = OpenAI(api_key=api_key)

    prompt = f"""
Você é um assistente clínico para médico emergencista.

Sua tarefa NÃO é reescrever o prontuário.
Sua tarefa é fornecer apenas sugestões baseadas em evidência para apoio à decisão clínica.

Regras obrigatórias:
- Responda em português.
- Baseie-se apenas no caso descrito.
- Não invente exames já realizados se eles não estiverem no texto.
- Não confunda “condutas realizadas” com “sugestões”.
- Não escreva parágrafos longos.
- Gere apenas uma lista numerada.
- Seja objetivo.
- Inclua apenas sugestões plausíveis e clinicamente relevantes para o cenário descrito.
- Se o caso estiver incompleto, inclua apenas sugestões gerais prudentes.
- Não repita literalmente as condutas já realizadas, a menos que sejam criticamente importantes.
- Não inclua avisos legais, explicações metodológicas ou texto fora da lista.

Formato de saída obrigatório:

1. ...
2. ...
3. ...

CASO CLÍNICO:
{texto_bruto}
"""

    response = client.responses.create(
        model=modelo,
        input=prompt
    )

    return response.output_text


# ======================================
# EVOLUÇÃO MÉDICA
# ======================================

def gerar_modelo_evolucao(texto):
    blocos = extrair_blocos(texto)

    bloco_hmp = blocos["hmp"]

    comorbidades = extrair_item_hmp(
        bloco_hmp,
        ["comorbidades", "antecedentes", "patologias prévias", "patologias previas"]
    )
    cirurgias = extrair_item_hmp(
        bloco_hmp,
        ["cirurgias prévias", "cirurgias previas", "cirurgias"]
    )
    alergias = extrair_item_hmp(
        bloco_hmp,
        ["alergias", "alergia"]
    )
    medicacoes = extrair_item_hmp(
        bloco_hmp,
        ["uso de medicamentos contínuos", "uso de medicamentos continuos", "medicações em uso", "medicacoes em uso", "medicações", "medicacoes"]
    )
    historia_familiar = extrair_item_hmp(
        bloco_hmp,
        ["história familiar relevante", "historia familiar relevante", "história familiar", "historia familiar"]
    )

    exame_fisico = montar_exame_fisico(blocos["exame_fisico"])
    parametros = montar_parametros(blocos["parametros"])
    diagnosticos = enumerar_itens(blocos["impressao_diagnostica"])
    exames_laboratoriais = organizar_exames_laboratoriais(blocos["exames_laboratoriais"])
    exames_imagem = montar_exames_imagem(blocos["exames_imagem"])
    especialidades = expandir_siglas(blocos["especialidades"])
    condutas = enumerar_itens(blocos["condutas"])
    qp = expandir_siglas(blocos["queixa_principal"])
    hda = expandir_siglas(blocos["hda"])

    evolucao_texto = blocos["evolucao"]
    if evolucao_texto == "-":
        evolucao_texto = "-"
    else:
        evolucao_texto = expandir_siglas(evolucao_texto)

    resultado = f"""»» Evolução Médica

»» Impressão Diagnóstica:
{diagnosticos}

»» Queixa Principal:
{qp}

»» História da Doença Atual:
{hda}

»» Histórico Médico Pregresso:
Comorbidades: {comorbidades}
Cirurgias prévias: {cirurgias}
Alergias: {alergias}
Uso de medicamentos contínuos: {medicacoes}
História familiar relevante: {historia_familiar}

»» Exame Físico:
{exame_fisico}

»» Parâmetros:
{parametros}

»» Evolução:
{evolucao_texto}

»» Exames Laboratoriais:
{exames_laboratoriais}

»» Exames de Imagem:
{exames_imagem}

»» Consulta com Especialidades:
{especialidades}

»» Condutas:
{condutas}
"""
    return resultado


# ======================================
# ATENDIMENTO NA EMERGÊNCIA
# ======================================

def gerar_modelo_atendimento(texto):
    blocos = extrair_blocos(texto)

    bloco_hmp = blocos["hmp"]

    comorbidades = extrair_item_hmp(
        bloco_hmp,
        ["comorbidades", "antecedentes", "patologias prévias", "patologias previas"]
    )
    cirurgias = extrair_item_hmp(
        bloco_hmp,
        ["cirurgias prévias", "cirurgias previas", "cirurgias"]
    )
    alergias = extrair_item_hmp(
        bloco_hmp,
        ["alergias", "alergia"]
    )
    medicacoes = extrair_item_hmp(
        bloco_hmp,
        ["uso de medicamentos contínuos", "uso de medicamentos continuos", "medicações em uso", "medicacoes em uso", "medicações", "medicacoes"]
    )
    historia_familiar = extrair_item_hmp(
        bloco_hmp,
        ["história familiar relevante", "historia familiar relevante", "história familiar", "historia familiar"]
    )

    exame_fisico = montar_exame_fisico(blocos["exame_fisico"])
    parametros = montar_parametros(blocos["parametros"])
    diagnosticos = enumerar_itens(blocos["impressao_diagnostica"])
    condutas = enumerar_itens(blocos["condutas"])

    exames_laboratoriais = organizar_exames_laboratoriais(blocos["exames_laboratoriais"])
    exames_imagem = montar_exames_imagem(blocos["exames_imagem"])
    especialidades = expandir_siglas(blocos["especialidades"])
    qp = expandir_siglas(blocos["queixa_principal"])
    hda = expandir_siglas(blocos["hda"])

    resultado = f"""»» Atendimento na Emergência

»» Impressão Diagnóstica:
{diagnosticos}

»» Queixa Principal:
{qp}

»» História da Doença Atual:
{hda}

»» Histórico Médico Pregresso:
Comorbidades: {comorbidades}
Cirurgias prévias: {cirurgias}
Alergias: {alergias}
Uso de medicamentos contínuos: {medicacoes}
História familiar relevante: {historia_familiar}

»» Exame Físico:
{exame_fisico}

»» Parâmetros:
{parametros}

»» Exames Laboratoriais:
{exames_laboratoriais}

»» Exames de Imagem:
{exames_imagem}

»» Consulta com Especialidades:
{especialidades}

»» Condutas:
{condutas}
"""
    return resultado


# ======================================
# BOTÃO PRINCIPAL
# ======================================

resultado_final = ""

if st.button("Gerar Documento"):
    try:
        if usar_ia:
            with st.spinner("Organizando com IA..."):
                resultado_final = organizar_com_ia(texto, tipo_documento, modelo_ia)
        else:
            if tipo_documento == "Atendimento na Emergência":
                resultado_final = gerar_modelo_atendimento(texto)
            else:
                resultado_final = gerar_modelo_evolucao(texto)

        st.session_state.pacientes[st.session_state.paciente_atual]["resultado"] = resultado_final

        # st.subheader("Texto organizado")
        # st.text(resultado_final)

        # st.subheader("Texto final para copiar")
        # st.text_area(
        #    "Clique aqui, depois use Command + A e Command + C",
        #   value=resultado_final,
        #   height=500
        # )

        st.info("Dica: clique dentro da caixa acima, pressione Command + A e depois Command + C para copiar tudo.")

        if mostrar_sugestoes_ia:
            with st.spinner("Gerando sugestões baseadas em evidência..."):
                sugestoes = gerar_sugestoes_evidencia(texto, modelo_ia)

            st.session_state.pacientes[st.session_state.paciente_atual]["sugestoes"] = sugestoes

            st.subheader("Sugestões baseadas em evidência (IA)")
            st.text(sugestoes)

            st.text_area(
                "Sugestões para copiar separadamente",
                value=sugestoes,
                height=220
            )

    except Exception as e:
        st.error(f"Erro ao gerar documento: {e}")

if st.button("Atualizar Exames"):
    paciente = st.session_state.pacientes[st.session_state.paciente_atual]

    documento_atual = paciente.get("resultado", "")
    exames_novos = st.session_state.get("texto_exames_novos", "")

    if documento_atual and exames_novos:
        blocos_novos = extrair_blocos(exames_novos)

        novos_labs = organizar_exames_laboratoriais(blocos_novos["exames_laboratoriais"])
        novas_imagens = montar_exames_imagem(blocos_novos["exames_imagem"])

        # =========================
        # LABORATÓRIOS (ACRESCENTAR)
        # =========================
        match_labs = re.search(
            r"(»» Exames Laboratoriais:\n)(.*?)(?=\n»»)",
            documento_atual,
            flags=re.S
        )

        if match_labs:
            labs_antigos = match_labs.group(2).strip()

            if labs_antigos == "-" or labs_antigos == "":
                labs_completo = novos_labs
            else:
                labs_completo = labs_antigos + "\n" + novos_labs

            documento_atual = re.sub(
                r"(»» Exames Laboratoriais:\n).*?(?=\n»»)",
                f"»» Exames Laboratoriais:\n{labs_completo}\n",
                documento_atual,
                flags=re.S
            )

        # ======================
        # IMAGEM (ACRESCENTAR)
        # ======================
        match_img = re.search(
            r"(»» Exames de Imagem:\n)(.*?)(?=\n»»)",
            documento_atual,
            flags=re.S
        )

        if match_img:
            img_antigos = match_img.group(2).strip()

            if img_antigos == "-" or img_antigos == "":
                img_completo = novas_imagens
            else:
                img_completo = img_antigos + "\n" + novas_imagens

            documento_atual = re.sub(
                r"(»» Exames de Imagem:\n).*?(?=\n»»)",
                f"»» Exames de Imagem:\n{img_completo}\n",
                documento_atual,
                flags=re.S
            )

        # salvar documento atualizado
        st.session_state.pacientes[st.session_state.paciente_atual]["resultado"] = documento_atual

        st.success("Exames adicionados ao documento.")

        st.subheader("Documento atualizado")
        st.text(documento_atual)

        st.text_area(
            "Texto final para copiar",
            value=documento_atual,
            height=500,
            key="documento_atualizado"
        )