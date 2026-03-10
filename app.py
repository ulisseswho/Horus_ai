# -*- coding: utf-8 -*-

import os
import streamlit as st
from dotenv import load_dotenv

from ocr_engine import extrair_texto_pdf, extrair_texto_imagem
from ai_engine import organizar_com_ia, gerar_sugestoes_evidencia, MODELO_IA
from exam_engine import organizar_exames_laboratoriais, montar_exames_imagem

load_dotenv()

st.set_page_config(page_title="Hórus Clinical Assistant", layout="wide")

st.title("Hórus Clinical Assistant")
st.caption("Assistente de IA para organização de prontuários clínicos")
st.caption(f"Modelo de IA: {MODELO_IA}")

# ===============================
# CONTROLE DE PACIENTES
# ===============================

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
        "resultado": ""
    }

    st.session_state.pacientes.append(novo)
    st.session_state.paciente_atual = len(st.session_state.pacientes) - 1


if len(st.session_state.pacientes) == 0:
    criar_novo_paciente()


# ===============================
# SIDEBAR
# ===============================

with st.sidebar:

    st.subheader("Pacientes")

    if st.button("Novo Paciente"):
        criar_novo_paciente()
        st.rerun()

    nomes = [p["id"] for p in st.session_state.pacientes]

    selecionado = st.selectbox(
        "Paciente atual",
        range(len(nomes)),
        index=st.session_state.paciente_atual,
        format_func=lambda i: nomes[i]
    )

    if selecionado != st.session_state.paciente_atual:
        st.session_state.paciente_atual = selecionado
        st.rerun()

paciente = st.session_state.pacientes[st.session_state.paciente_atual]
paciente_id = paciente["id"]

st.caption(f"Paciente em edição: {paciente_id}")

resultado_salvo = paciente.get("resultado", "")

if resultado_salvo:

    st.subheader("Documento gerado")

    st.text_area(
        "Texto final para copiar",
        value=resultado_salvo,
        height=500
    )


# ===============================
# TIPO DE DOCUMENTO
# ===============================

tipo_documento = st.selectbox(
    "Tipo de documento",
    ["Atendimento Clínico", "Evolução Médica", "Exames Complementares"]
)

# ===============================================
# ATENDIMENTO CLÍNICO
# ===============================================

if tipo_documento == "Atendimento Clínico":

    st.subheader("Estrutura do Atendimento")

    impressao_diag = st.text_area("Impressões Diagnósticas", height=120)
    qp = st.text_area("Queixa Principal", height=80)
    hda = st.text_area("História da Doença Atual (HDA)", height=160)
    hpp = st.text_area("Histórico Médico Pregresso (HPP)", height=120)
    exame_fisico = st.text_area("Exame Físico", height=180)
    parametros = st.text_area("Parâmetros na admissão", height=80)
    exames_lab = st.text_area("Exames laboratoriais", height=120)
    exames_img = st.text_area("Exames de imagem", height=120)
    pareceres = st.text_area("Pareceres / Interconsultas", height=100)
    condutas = st.text_area("Condutas", height=120)

    if st.button("Gerar Atendimento Clínico"):

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
{parametros}

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

        paciente["resultado"] = resultado

        st.rerun()

# ===============================
# EVOLUÇÃO MÉDICA
# ===============================

if tipo_documento == "Evolução Médica":

    fonte = st.radio(
        "Fonte",
        ["Texto", "Arquivo"],
        horizontal=True
    )

    texto = ""

    if fonte == "Texto":

        texto = st.text_area(
            "Cole o texto da evolução",
            height=350
        )

    else:

        arquivos = st.file_uploader(
            "Envie PDF ou imagem",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True
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
                height=300
            )

            texto = texto_total

    if st.button("Gerar Evolução"):

        resultado = organizar_com_ia(texto, "Evolução Médica")

        sugestoes = gerar_sugestoes_evidencia(texto)

        if sugestoes:
            resultado += "\n\n>>> Sugestões adicionais baseadas em evidência (IA):\n"
            resultado += sugestoes

        paciente["resultado"] = resultado

        st.rerun()


# ===============================
# EXAMES COMPLEMENTARES
# ===============================

if tipo_documento == "Exames Complementares":

    fonte = st.radio(
        "Fonte dos exames",
        ["Texto", "Arquivo"],
        horizontal=True
    )

    texto_exames = ""

    if fonte == "Texto":

        texto_exames = st.text_area(
            "Cole exames aqui",
            height=350
        )

    else:

        arquivos = st.file_uploader(
            "Envie exames",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True
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
                height=300
            )

            texto_exames = texto_total

    if st.button("Organizar Exames"):

        exames_lab = organizar_exames_laboratoriais(texto_exames)
        exames_img = montar_exames_imagem(texto_exames)

        resultado = f"""»» Exames Complementares

»» Exames Laboratoriais:
{exames_lab}

»» Exames de Imagem:
{exames_img}
"""

        paciente["resultado"] = resultado

        st.rerun()