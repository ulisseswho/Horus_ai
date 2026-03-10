import os
from openai import OpenAI

MODELO_IA = "gpt-4.1-mini"


def cliente_openai():

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada")

    return OpenAI(api_key=api_key)


def organizar_com_ia(texto, tipo):

    client = cliente_openai()

    prompt = f"""
Organize o seguinte texto clínico no formato de {tipo}.
Não invente dados.
Se algo não existir usar "-".

TEXTO:
{texto}
"""

    response = client.responses.create(
        model=MODELO_IA,
        input=prompt
    )

    return response.output_text


def gerar_sugestoes_evidencia(texto):

    client = cliente_openai()

    prompt = f"""
Forneça sugestões clínicas baseadas em evidência.

1.
2.
3.

Caso:
{texto}
"""

    response = client.responses.create(
        model=MODELO_IA,
        input=prompt
    )

    return response.output_text
