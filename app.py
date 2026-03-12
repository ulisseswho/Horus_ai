# -*- coding: utf-8 -*-

# ===============================================
# IMPORTS
# ===============================================

import streamlit as st
from dotenv import load_dotenv

from docx import Document
from io import BytesIO

from ocr_engine import extrair_texto_pdf, extrair_texto_imagem
from ai_engine import organizar_com_ia, gerar_sugestoes_evidencia, MODELO_IA
from exam_engine import organizar_exames_laboratoriais, montar_exames_imagem
from clinical_parser import extrair_campos_evolucao

load_dotenv()

# ===============================================
# FUNÇÃO WORD
# ===============================================

def gerar_word(texto):
    doc = Document()

    for linha in texto.split("\n"):
        doc.add_paragraph(linha)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer

# ===============================================
# CONFIGURAÇÃO DA PÁGINA
# ===============================================

st.set_page_config(page_title="Hórus Clinical Assistant", layout="wide")

st.title("Hórus Clinical Assistant")
st.caption("Assistente de IA para organização de prontuários clínicos")
st.caption(f"Modelo de IA: {MODELO_IA}")

# ===============================================
# CONTROLE DE PACIENTES
# ===============================================

if "pacientes" not in st.session_state:
    st.session_state.pacientes = []

if "paciente_atual" not in st.session_state:
    st.session_state.paciente_atual = 0

if "contador_paciente" not in st.session_state:
    st.session_state.contador_paciente = 0

def criar_novo_paciente():
    st.session_state.contador_paciente += 1
    paciente_id = f"Paciente {st.session_state.contador_paciente:03d}"

    novo = {
        "id": paciente_id,
        "resultado_atendimento": "",
        "resultado_evolucao": "",
        "resultado_exames": ""
    }

    st.session_state.pacientes.append(novo)
    st.session_state.paciente_atual = len(st.session_state.pacientes) - 1

if len(st.session_state.pacientes) == 0:
    criar_novo_paciente()

# ===============================================
# SIDEBAR
# ===============================================

with st.sidebar:
    st.subheader("Pacientes")

    if "select_paciente_atual" not in st.session_state:
        st.session_state["select_paciente_atual"] = st.session_state.paciente_atual

    if st.button("Novo Paciente", key="btn_novo_paciente_sidebar"):
        criar_novo_paciente()
        st.session_state["select_paciente_atual"] = st.session_state.paciente_atual
        st.rerun()

    nomes = [p["id"] for p in st.session_state.pacientes]

    selecionado = st.selectbox(
        "Paciente atual",
        range(len(nomes)),
        format_func=lambda i: nomes[i],
        key="select_paciente_atual"
    )

    if selecionado != st.session_state.paciente_atual:
        st.session_state.paciente_atual = selecionado
        st.rerun()

# ===============================================
# PACIENTE ATUAL
# ===============================================

paciente = st.session_state.pacientes[st.session_state.paciente_atual]
paciente_id = paciente["id"]

st.caption(f"Paciente em edição: {paciente_id}")

# ===============================================
# TIPO DE DOCUMENTO
# ===============================================

tipo_documento = st.selectbox(
    "Tipo de documento",
    ["Atendimento Clínico", "Evolução Médica", "Exames Complementares"],
    key=f"tipo_documento_{paciente_id}"
)

# ===============================================
# RESULTADOS
# ===============================================

resultado_atendimento = paciente.get("resultado_atendimento", "")
resultado_evolucao = paciente.get("resultado_evolucao", "")
resultado_exames = paciente.get("resultado_exames", "")

documento_atual = ""

if tipo_documento == "Atendimento Clínico":
    documento_atual = resultado_atendimento
elif tipo_documento == "Evolução Médica":
    documento_atual = resultado_evolucao
elif tipo_documento == "Exames Complementares":
    documento_atual = resultado_exames

if documento_atual:

    st.subheader("Documento gerado")

    st.text_area(
        "Texto final para copiar",
        value=documento_atual,
        height=500,
        key=f"resultado_{paciente_id}_{tipo_documento}"
    )

    arquivo_word = gerar_word(documento_atual)

    st.download_button(
        label="Criar Word",
        data=arquivo_word,
        file_name=f"{paciente_id}_{tipo_documento}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ===============================================
# ATENDIMENTO CLÍNICO
# ===============================================

if tipo_documento == "Atendimento Clínico":

    st.subheader("Estrutura do Atendimento")

    # ===========================================
    # BLOCO — PREENCHIMENTO AUTOMÁTICO PARA TESTES
    # ===========================================

    if st.button("Preencher dados de teste", key=f"teste_{paciente_id}"):

        st.session_state[f"imp_{paciente_id}"] = "1. sepse\n2. insuficiência respiratória aguda"
        st.session_state[f"qp_{paciente_id}"] = "dispneia e febre"
        st.session_state[f"hda_{paciente_id}"] = (
            "Paciente com febre há 3 dias associada a dispneia progressiva "
            "e piora do estado geral."
        )
        st.session_state[f"hpp_{paciente_id}"] = "HAS e DM2."
        st.session_state[f"ef_{paciente_id}"] = (
            "RASS -5, pupilas isocóricas e fotorreativas, sem déficits neurológicos focais aparentes."
        )

        st.session_state[f"pa_{paciente_id}"] = "90/60"
        st.session_state[f"fc_{paciente_id}"] = "122"
        st.session_state[f"fr_{paciente_id}"] = "28"
        st.session_state[f"temp_{paciente_id}"] = "38.4"
        st.session_state[f"sato2_{paciente_id}"] = "88"
        st.session_state[f"glicemia_{paciente_id}"] = "210"

        st.session_state[f"lab_{paciente_id}"] = (
            "[10/03/2026 20:19] Gasometria arterial:\n"
            "pH 7,25 || pCO2 55 mmHg || HCO3 18 mmol/L"
        )
        st.session_state[f"img_{paciente_id}"] = (
            "[10/03/2026 21:10] Tomografia de tórax:\n"
            "infiltrado pulmonar bilateral."
        )
        st.session_state[f"parec_{paciente_id}"] = "avaliado pela UTI."
        st.session_state[f"cond_{paciente_id}"] = (
            "1. iniciar antibiótico\n"
            "2. oxigenoterapia\n"
            "3. coletar hemoculturas"
        )

        st.rerun()

    # ===========================================
    # BLOCO — FORMULÁRIO DO ATENDIMENTO
    # ===========================================

    with st.form(key=f"form_atendimento_{paciente_id}"):

        # ---------------------------------------
        # CAMPOS PRINCIPAIS
        # ---------------------------------------

        impressao_diag = st.text_area(
            "Impressões Diagnósticas",
            height=120,
            key=f"imp_{paciente_id}"
        )

        qp = st.text_area(
            "Queixa Principal",
            height=80,
            key=f"qp_{paciente_id}"
        )

        hda = st.text_area(
            "História da Doença Atual (HDA)",
            height=160,
            key=f"hda_{paciente_id}"
        )

        hpp = st.text_area(
            "Histórico Médico Pregresso (HPP)",
            height=120,
            key=f"hpp_{paciente_id}"
        )

        exame_fisico = st.text_area(
            "Exame Físico",
            height=180,
            key=f"ef_{paciente_id}"
        )

        # ---------------------------------------
        # PARÂMETROS
        # ---------------------------------------

        st.caption("Parâmetros na admissão")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            pa = st.text_input("PA", key=f"pa_{paciente_id}")

        with col2:
            fc = st.text_input("FC", key=f"fc_{paciente_id}")

        with col3:
            fr = st.text_input("FR", key=f"fr_{paciente_id}")

        with col4:
            temp = st.text_input("Temp", key=f"temp_{paciente_id}")

        with col5:
            sato2 = st.text_input("SatO2", key=f"sato2_{paciente_id}")

        with col6:
            glicemia = st.text_input("Glicemia", key=f"glicemia_{paciente_id}")

        # ---------------------------------------
        # EXAMES E CONDUTAS
        # ---------------------------------------

        exames_lab = st.text_area(
            "Exames laboratoriais",
            height=120,
            key=f"lab_{paciente_id}"
        )

        exames_img = st.text_area(
            "Exames de imagem",
            height=120,
            key=f"img_{paciente_id}"
        )

        pareceres = st.text_area(
            "Pareceres / Interconsultas",
            height=100,
            key=f"parec_{paciente_id}"
        )

        condutas = st.text_area(
            "Condutas",
            height=120,
            key=f"cond_{paciente_id}"
        )

        gerar_atendimento = st.form_submit_button("Gerar Atendimento Clínico")

    # ===========================================
    # BLOCO — GERAÇÃO DO ATENDIMENTO
    # ===========================================

    if gerar_atendimento:

        parametros_formatados = (
            f"PA {pa if pa else '-'} mmHg || "
            f"FC {fc if fc else '-'} bpm || "
            f"FR {fr if fr else '-'} irpm || "
            f"Temp {temp if temp else '-'} °C || "
            f"SatO2 {sato2 if sato2 else '-'} % || "
            f"Glicemia {glicemia if glicemia else '-'} mg/dL"
        )

        texto_base = f"""
IMPRESSÕES DIAGNÓSTICAS:
{impressao_diag}

QUEIXA PRINCIPAL:
{qp}

HDA:
{hda}

HPP:
{hpp}

EXAME FÍSICO:
{exame_fisico}

PARÂMETROS NA ADMISSÃO:
{parametros_formatados}

EXAMES LABORATORIAIS:
{exames_lab}

EXAMES DE IMAGEM:
{exames_img}

PARECERES:
{pareceres}

CONDUTAS:
{condutas}
"""

        with st.spinner("Organizando atendimento..."):
            resultado = organizar_com_ia(texto_base, "Atendimento Clínico")

        sugestoes = gerar_sugestoes_evidencia(texto_base)

        if sugestoes:
            resultado += "\n\n>>> Sugestões adicionais baseadas em evidência (IA):\n"
            resultado += sugestoes

        paciente["resultado_atendimento"] = resultado
        st.rerun()

# ===============================================
# EVOLUÇÃO MÉDICA
# ===============================================

if tipo_documento == "Evolução Médica":

    # ===========================================
    # BLOCO — ENTRADA DA EVOLUÇÃO
    # ===========================================

    fonte = st.radio(
        "Fonte",
        ["Texto", "Arquivo"],
        horizontal=True,
        key=f"fonte_evolucao_{paciente_id}"
    )

    texto = ""

    if fonte == "Texto":

        texto = st.text_area(
            "Cole o texto da evolução",
            height=300,
            key=f"texto_evolucao_{paciente_id}"
        )

    else:

        arquivos = st.file_uploader(
            "Envie PDF ou imagem",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"upload_evolucao_{paciente_id}"
        )

        if arquivos:

            texto_total = ""

            for arquivo in arquivos:
                if arquivo.type == "application/pdf":
                    texto_extraido = extrair_texto_pdf(arquivo)
                else:
                    texto_extraido = extrair_texto_imagem(arquivo)

                texto_total += texto_extraido

            st.text_area(
                "Texto OCR",
                value=texto_total,
                height=250,
                key=f"ocr_evolucao_{paciente_id}"
            )

            texto = texto_total

    # ===========================================
    # BLOCO — ORGANIZAR EVOLUÇÃO
    # ===========================================

    if st.button("Organizar Evolução", key=f"organizar_evolucao_{paciente_id}"):
        resultado = organizar_com_ia(texto, "Evolução Médica")

        campos = extrair_campos_evolucao(resultado)

        st.session_state[f"ev_campos_{paciente_id}"] = campos
        st.session_state[f"ev_base_{paciente_id}"] = resultado

        # pré-preenchimento dos parâmetros
        st.session_state[f"ev_pa_{paciente_id}"] = ""
        st.session_state[f"ev_fc_{paciente_id}"] = ""
        st.session_state[f"ev_fr_{paciente_id}"] = ""
        st.session_state[f"ev_temp_{paciente_id}"] = ""
        st.session_state[f"ev_sato2_{paciente_id}"] = ""
        st.session_state[f"ev_glicemia_{paciente_id}"] = ""
        st.session_state[f"ev_hora_{paciente_id}"] = ""

        st.rerun()

    # ===========================================
    # BLOCO — REVISÃO DA EVOLUÇÃO
    # ===========================================

    if f"ev_campos_{paciente_id}" in st.session_state:

        campos = st.session_state[f"ev_campos_{paciente_id}"]
        base = st.session_state[f"ev_base_{paciente_id}"]

        st.subheader("Revisão da Evolução")

        st.text_area(
            "Texto organizado",
            value=base,
            height=300,
            key=f"texto_base_evolucao_{paciente_id}"
        )

        with st.form(key=f"form_evolucao_{paciente_id}"):

            # ---------------------------------------
            # CAMPOS TRAVADOS
            # ---------------------------------------

            st.caption("Dados extraídos do prontuário")

            st.caption("Atualizações da evolução")

            impressao = st.text_area(
                "Impressões",
                height=120,
                value=campos.get("impressao", ""),
                key=f"ev_imp_{paciente_id}"
            )

            qp = st.text_area(
                "Queixa Principal",
                value=campos.get("qp", ""),
                disabled=True,
                key=f"ev_qp_{paciente_id}"
            )

            hda = st.text_area(
                "HDA",
                value=campos.get("hda", ""),
                disabled=True,
                key=f"ev_hda_{paciente_id}"
            )

            hpp = st.text_area(
                "HPP",
                value=campos.get("hpp", ""),
                disabled=True,
                key=f"ev_hpp_{paciente_id}"
            )

            # ---------------------------------------
            # CAMPOS EDITÁVEIS
            # ---------------------------------------

            exame = st.text_area(
                "Exame físico",
                height=180,
                value=campos.get("exame_fisico", ""),
                key=f"ev_ef_{paciente_id}"
            )

            evolucao = st.text_area(
                "Evolução",
                height=140,
                value=campos.get("evolucao", ""),
                key=f"ev_evol_{paciente_id}"
            )

            # ---------------------------------------
            # PARÂMETROS
            # ---------------------------------------

            st.caption("Parâmetros")

            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

            with col1:
                pa = st.text_input("PA", key=f"ev_pa_{paciente_id}")

            with col2:
                fc = st.text_input("FC", key=f"ev_fc_{paciente_id}")

            with col3:
                fr = st.text_input("FR", key=f"ev_fr_{paciente_id}")

            with col4:
                temp = st.text_input("Temp", key=f"ev_temp_{paciente_id}")

            with col5:
                sato2 = st.text_input("SatO2", key=f"ev_sato2_{paciente_id}")

            with col6:
                glicemia = st.text_input("Glicemia", key=f"ev_glicemia_{paciente_id}")

            with col7:
                hora = st.text_input("Hora", key=f"ev_hora_{paciente_id}")

            # ---------------------------------------
            # EXAMES / PARECERES / CONDUTAS
            # ---------------------------------------

            exames = st.text_area(
                "Exames",
                height=140,
                value=campos.get("exames_lab", ""),
                key=f"ev_exames_{paciente_id}"
            )

            img = st.text_area(
                "Imagem",
                height=120,
                value=campos.get("exames_img", ""),
                key=f"ev_img_{paciente_id}"
            )

            pareceres = st.text_area(
                "Pareceres / interconsultas",
                height=100,
                value=campos.get("especialidades", ""),
                key=f"ev_pareceres_{paciente_id}"
            )

            condutas = st.text_area(
                "Condutas",
                height=120,
                value=campos.get("condutas", ""),
                key=f"ev_cond_{paciente_id}"
            )

            gerar_evolucao = st.form_submit_button("Gerar Evolução")

        # =======================================
        # BLOCO — GERAÇÃO DA EVOLUÇÃO FINAL
        # =======================================

        if gerar_evolucao:

            parametros_formatados = (
                f"PA {pa if pa else '-'} mmHg || "
                f"FC {fc if fc else '-'} bpm || "
                f"FR {fr if fr else '-'} irpm || "
                f"Temp {temp if temp else '-'} °C || "
                f"SatO2 {sato2 if sato2 else '-'} % || "
                f"Glicemia {glicemia if glicemia else '-'} mg/dL || "
                f"Hora {hora if hora else '-'}"
            )

            texto_final = f"""»» Evolução Médica

»» Impressão Diagnóstica:
{impressao}

»» Queixa Principal:
{qp}

»» História da Doença Atual:
{hda}

»» Histórico Médico Pregresso:
{hpp}

»» Exame Físico:
{exame}

»» Parâmetros:
{parametros_formatados}

»» Evolução:
{evolucao}

»» Exames laboratoriais:
{exames}

»» Exames de imagem:
{img}

»» Consulta com especialidades:
{pareceres}

»» Condutas:
{condutas}
"""

            sugestoes = gerar_sugestoes_evidencia(texto_final)

            if sugestoes:
                texto_final += "\n\n>>> Sugestões adicionais baseadas em evidência (IA):\n"
                texto_final += sugestoes

            paciente["resultado_evolucao"] = texto_final
            st.rerun()

# ===============================================
# EXAMES COMPLEMENTARES
# ===============================================

if tipo_documento == "Exames Complementares":

    fonte = st.radio(
        "Fonte dos exames",
        ["Texto", "Arquivo"],
        horizontal=True,
        key=f"fonte_exames_{paciente_id}"
    )

    texto_exames = ""

    if fonte == "Texto":

        texto_exames = st.text_area(
            "Cole exames aqui",
            height=350,
            key=f"texto_exames_{paciente_id}"
        )

    else:

        arquivos = st.file_uploader(
            "Envie exames",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"upload_exames_{paciente_id}"
        )

        if arquivos:
            texto_total = ""

            for arquivo in arquivos:
                if arquivo.type == "application/pdf":
                    texto_extraido = extrair_texto_pdf(arquivo)
                else:
                    texto_extraido = extrair_texto_imagem(arquivo)

                texto_total += texto_extraido

            st.text_area(
                "Texto OCR",
                value=texto_total,
                height=300,
                key=f"ocr_exames_{paciente_id}"
            )

            texto_exames = texto_total

    if st.button("Organizar Exames", key=f"organizar_exames_{paciente_id}"):

        exames_lab = organizar_exames_laboratoriais(texto_exames)
        exames_img = montar_exames_imagem(texto_exames)

        resultado = f"""»» Exames Complementares

»» Exames Laboratoriais:
{exames_lab}

»» Exames de Imagem:
{exames_img}
"""

        paciente["resultado_exames"] = resultado
        st.rerun()

