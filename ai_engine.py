# ===============================================
# IMPORTS
# ===============================================

import os
from openai import OpenAI


# ===============================================
# CONFIGURAÇÃO DO MODELO
# ===============================================

MODELO_IA = "gpt-4.1-mini"


# ===============================================
# CLIENTE OPENAI
# ===============================================

def cliente_openai():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada")

    return OpenAI(api_key=api_key)


# ===============================================
# PROMPT — ATENDIMENTO CLÍNICO
# ===============================================

def prompt_atendimento_clinico(texto_base):
    return f"""
Você é um assistente de organização clínica para médico emergencista.

Sua tarefa é organizar o conteúdo recebido no modelo abaixo, com linguagem médica clara, elegante e objetiva, sem perder precisão clínica.

INSTRUÇÕES DE ORGANIZAÇÃO

1. Impressão diagnóstica
- manter em lista numerada
- preservar os diagnósticos informados
- ajustar apenas pontuação e capitalização quando necessário

2. Queixa principal
- usar frase curta, objetiva e clinicamente útil
- se a queixa principal estiver vazia, extrair da história da doença atual
- quando houver duração clara na história da doença atual, incluir a duração na queixa principal
- exemplo:
se a HDA disser "febre há 3 dias e dispneia progressiva", a queixa principal deve sair como:
"Dispneia e febre há 3 dias."

3. História da doença atual
- manter em texto corrido, claro e objetivo
- melhorar a redação sem alterar o significado clínico

4. Histórico médico pregresso
- organizar sempre exatamente em:
Comorbidades:
Alergias:
Uso de medicamentos contínuos:
Cirurgias prévias:

- se essas informações estiverem descritas em qualquer parte do texto base, da história da doença atual, do histórico ou dos documentos de origem, resgatar e realocar para este campo
- se uma informação estiver ausente, preencher com "-"
- se houver menção explícita de negativa, como "nega alergias" ou "nega cirurgias prévias", registrar a negativa no subtópico correspondente
- não inventar dados

5. Exame físico
- sempre organizar em:
Ectoscopia:
Neurológico:
Cardiovascular:
Respiratório:
Abdome:
Extremidades:

- classificar cada achado no sistema correto, mesmo se vier sem rótulo explícito
- não repetir o mesmo achado em dois sistemas diferentes
- os sistemas não mencionados devem ser preenchidos com descrição normal

Classificação semântica dos achados:
- RASS, Glasgow, pupilas, nível de consciência, sedação, déficit focal, resposta motora, orientação, confusão, rebaixamento → Neurológico
- bulhas, sopros, pulsos, perfusão, enchimento capilar, edema → Cardiovascular
- murmúrio vesicular, estertores, sibilos, roncos, esforço respiratório → Respiratório
- dor abdominal, distensão, defesa, descompressão brusca, ruídos hidroaéreos → Abdome
- aspecto geral, hidratação, cor, febre, estado geral → Ectoscopia
- edema periférico, perfusão periférica, extremidades frias/quentes → Extremidades

Coerência clínica obrigatória:
- a descrição dos sistemas deve ser clinicamente coerente entre si
- se houver rebaixamento importante do nível de consciência, não usar "consciente e orientado"
- se houver RASS -5, Glasgow muito reduzido, coma, sedação profunda ou descrição equivalente, a ectoscopia deve refletir rebaixamento importante do nível de consciência

Padrões de normalidade para sistemas não mencionados:
- Ectoscopia: estado geral regular, afebril, acianótico, anictérico, normocorado, hidratado, eupneico.
- Neurológico: sem déficits neurológicos focais aparentes.
- Cardiovascular: bulhas rítmicas normofonéticas em 2 tempos, sem sopros, pulsos periféricos palpáveis e perfusão periférica preservada.
- Respiratório: murmúrio vesicular presente bilateralmente, sem ruídos adventícios.
- Abdome: plano, flácido, indolor à palpação, sem sinais de irritação peritoneal.
- Extremidades: sem edema, sem cianose, perfusão periférica preservada.

Exemplo obrigatório de coerência:
Se a entrada do exame físico for:
"RASS -5, pupilas isocóricas e fotorreativas, sem déficits neurológicos focais aparentes."

A saída correta deve seguir esta lógica:
Ectoscopia: paciente em estado geral regular, em rebaixamento importante do nível de consciência, afebril, acianótico, anictérico, normocorado, hidratado.
Neurológico: RASS -5, pupilas isocóricas e fotorreativas, sem déficits neurológicos focais aparentes.
Cardiovascular: bulhas rítmicas normofonéticas em 2 tempos, sem sopros, pulsos periféricos palpáveis e perfusão periférica preservada.
Respiratório: murmúrio vesicular presente bilateralmente, sem ruídos adventícios.
Abdome: plano, flácido, indolor à palpação, sem sinais de irritação peritoneal.
Extremidades: sem edema, sem cianose, perfusão periférica preservada.

6. Parâmetros na admissão
- usar exatamente este formato:
PA X/X mmHg || FC X bpm || FR X irpm || Temp X °C || SatO2 X % || Glicemia X mg/dL
- manter as siglas exatamente assim: PA, FC, FR, Temp, SatO2, Glicemia

7. Exames laboratoriais e exames de imagem
- se já vierem estruturados, preservar conteúdo, datas, horários, colchetes, unidades, siglas e qualificadores
- não transformar em narrativa clínica
- não remover data e hora
- não alterar resultados
- pode apenas melhorar discretamente a capitalização do nome do exame, mantendo o restante intacto

8. Pareceres
- manter o conteúdo informado
- melhorar discretamente a redação, se necessário

9. Condutas
- manter em lista numerada
- melhorar a redação para linguagem médica adequada e elegante
- transformar palavras soltas em frases clínicas completas

Exemplos de condutas:
- "antibióticos" → "Iniciado antibiótico de amplo espectro."
- "oxigenoterapia" → "Iniciada oxigenoterapia suplementar."
- "coletar hemoculturas" → "Solicitada coleta de hemoculturas."

ESTILO DA SAÍDA
- capitalização normal de frase
- sem Markdown
- sem asteriscos
- sem caixa alta desnecessária
- texto limpo e elegante

MODELO EXATO

»» Atendimento Clínico

»» Impressão Diagnóstica:
1. -

»» Queixa Principal:
-

»» História da Doença Atual:
-

»» Histórico Médico Pregresso:
Comorbidades: -
Alergias: -
Uso de medicamentos contínuos: -
Cirurgias prévias: -

»» Exame Físico:
Ectoscopia: estado geral regular, afebril, acianótico, anictérico, normocorado, hidratado, eupneico.
Neurológico: sem déficits neurológicos focais aparentes.
Cardiovascular: bulhas rítmicas normofonéticas em 2 tempos, sem sopros, pulsos periféricos palpáveis e perfusão periférica preservada.
Respiratório: murmúrio vesicular presente bilateralmente, sem ruídos adventícios.
Abdome: plano, flácido, indolor à palpação, sem sinais de irritação peritoneal.
Extremidades: sem edema, sem cianose, perfusão periférica preservada.

»» Parâmetros na admissão:
PA - mmHg || FC - bpm || FR - irpm || Temp - °C || SatO2 - % || Glicemia - mg/dL

»» Exames laboratoriais:
-

»» Exames de imagem:
-

»» Pareceres:
-

»» Condutas:
1. -

TEXTO BASE:
{texto_base}
"""


# ===============================================
# PROMPT — EVOLUÇÃO MÉDICA
# ===============================================

def prompt_evolucao_medica(texto_bruto):

    return f"""
Você é um assistente de organização clínica para médico emergencista.

Sua tarefa é reorganizar o texto abaixo no modelo exato de Evolução Médica.

Regras obrigatórias gerais:
- Não invente dados ausentes.
- Se algo não estiver descrito, preencher com "-".
- Manter linguagem médica formal, clara e organizada.
- Não usar Markdown.
- Não usar asteriscos.
- Não usar lista com hífen nos campos finais.
- Não escrever explicações fora do modelo.
- Preservar datas exatamente como aparecem no texto.
- Não inventar ano.
- Não inventar horário.

Impressão diagnóstica:
- Organizar em lista numerada.
- Manter diagnósticos relevantes do texto.
- Pode consolidar termos equivalentes sem perder informação.

Queixa principal:
- Extrair do texto de forma curta e objetiva.
- Se houver duração clara, incluir.

História da doença atual:
- Organizar em texto corrido, claro e cronológico.

Histórico médico pregresso:
- Organizar exatamente em:
Comorbidades:
Cirurgias prévias:
Alergias:
Uso de medicamentos contínuos:
História familiar relevante:
- Resgatar essas informações de qualquer parte do texto, se estiverem disponíveis.
- Se houver negativa explícita, registrar a negativa.
- Se não houver dado, preencher com "-".

Exame físico:
- Organizar exatamente em:
Ectoscopia:
Neurológico:
Cardiovascular:
Respiratório:
Abdome:
Extremidades:

- Se algum sistema não estiver descrito no texto original, preencher com padrão normal completo.
- Não deixar sistema com "-".
- Não usar siglas no exame físico.
- Expandir siglas médicas do exame físico para forma escrita.
- Classificar corretamente cada achado no sistema correspondente.

Conversão obrigatória de siglas no exame físico:
- BEG → bom estado geral
- REG → estado geral regular
- MEG → mau estado geral
- AAA → afebril, acianótica, anictérica
- RCR → ritmo cardíaco regular
- 2T → em dois tempos
- s/ sopros → sem sopros
- MV+ → murmúrio vesicular presente
- s/ RA → sem ruídos adventícios
- RHA+ → ruídos hidroaéreos presentes
- VCM → visceromegalias
- PPP → pulsos periféricos palpáveis
- TEC<3s → tempo de enchimento capilar menor que 3 segundos

Classificação dos sistemas:
- Estado geral, coloração, hidratação, febre, orientação, nível de consciência → Ectoscopia
- Pupilas, déficits focais, Glasgow, RASS, força, sensibilidade → Neurológico
- Ritmo cardíaco, bulhas, sopros, frequência cardíaca, pulsos, perfusão → Cardiovascular
- Murmúrio vesicular, crepitações, sibilos, roncos, saturação, esforço respiratório → Respiratório
- Abdome, dor, ruídos hidroaéreos, massas, visceromegalias → Abdome
- Edema, perfusão periférica, panturrilhas, extremidades → Extremidades

Padrão normal obrigatório para sistemas não descritos:
- Ectoscopia: bom estado geral, afebril, acianótica, anictérica, hidratada, consciente e orientada.
- Neurológico: sem déficits neurológicos focais aparentes.
- Cardiovascular: ritmo cardíaco regular, bulhas normofonéticas em dois tempos, sem sopros.
- Respiratório: murmúrio vesicular presente bilateralmente, sem ruídos adventícios.
- Abdome: plano, flácido, indolor à palpação, ruídos hidroaéreos presentes, sem massas ou visceromegalias.
- Extremidades: sem edema, pulsos periféricos palpáveis, tempo de enchimento capilar menor que 3 segundos.

Parâmetros:
- Usar exatamente este formato:
PA - mmHg || FC - bpm || FR - irpm || Temp - °C || SatO2 - % || Glicemia - mg/dL || Hora -
- Se houver valores claros no texto, preencher.
- Se não houver, manter "-".

Evolução:
- Organizar em texto corrido e objetivo, resumindo o estado atual do paciente.

Exames laboratoriais:
- Não usar lista com hífen.
- Não usar ponto e vírgula como estrutura final.
- Sempre organizar em linhas independentes no seguinte padrão:
[DATA] – CATEGORIA: parâmetro || parâmetro || parâmetro
- Se houver hora disponível:
[DATA – HORA] – CATEGORIA: parâmetro || parâmetro || parâmetro
- Separar por categorias quando possível, como:
Hemograma
Bioquímica
Eletrólitos
Marcadores inflamatórios
Imunologia
Sorologias
Exames medulares
Endocrinometabólico
- Manter os resultados em linha única, separados por "||".
- Nunca iniciar linha de exame com hífen.
- Não transformar exames em narrativa.
- Não alterar valores.
- Não alterar unidades.
- Não interpretar resultados.

Exames de imagem:
- Não usar lista com hífen.
- Sempre organizar em linhas independentes no seguinte padrão:
[DATA] – Exame de imagem: descrição
ou
[DATA – HORA] – Exame de imagem: descrição
- Não resumir demais os achados.
- Não interpretar.

Consulta com especialidades:
- Nunca apresentar em lista com hífen.
- Escrever em texto corrido.
- Pode sugerir interconsultas pertinentes com base no caso, se estiverem claramente indicadas no texto.

Condutas:
- Organizar em lista numerada.
- Redigir em linguagem médica objetiva e elegante.
- Pode melhorar a redação sem alterar a conduta.

Modelo exato:

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
Ectoscopia: bom estado geral, afebril, acianótica, anictérica, hidratada, consciente e orientada.
Neurológico: sem déficits neurológicos focais aparentes.
Cardiovascular: ritmo cardíaco regular, bulhas normofonéticas em dois tempos, sem sopros.
Respiratório: murmúrio vesicular presente bilateralmente, sem ruídos adventícios.
Abdome: plano, flácido, indolor à palpação, ruídos hidroaéreos presentes, sem massas ou visceromegalias.
Extremidades: sem edema, pulsos periféricos palpáveis, tempo de enchimento capilar menor que 3 segundos.

»» Parâmetros:
PA - mmHg || FC - bpm || FR - irpm || Temp - °C || SatO2 - % || Glicemia - mg/dL || Hora -

»» Evolução:
-

»» Exames laboratoriais:
-

»» Exames de imagem:
-

»» Consulta com especialidades:
-

»» Condutas:
1. -

TEXTO BRUTO:
{texto_bruto}
"""

# ===============================================
# PROMPT — SUGESTÕES BASEADAS EM EVIDÊNCIA
# ===============================================

def prompt_sugestoes_evidencia(texto_bruto):
    return f"""
Você é um assistente clínico para médico emergencista.

Sua tarefa é fornecer apenas sugestões baseadas em evidência.

Regras:
- Não reescrever o prontuário.
- Não inventar exames.
- Não usar asteriscos.
- Resposta apenas em lista numerada.
- Ser objetivo e clinicamente útil.

Formato obrigatório:

1. ...
2. ...
3. ...

Caso clínico:
{texto_bruto}
"""


# ===============================================
# PROMPT — ORGANIZAÇÃO DE EXAMES LABORATORIAIS
# ===============================================

def prompt_organizar_exames_laboratoriais(texto):
    return f"""
Você é um assistente de organização de exames laboratoriais.

Regras obrigatórias:
- Não interpretar resultados.
- Não alterar valores.
- Não alterar unidades.
- Não reescrever em narrativa clínica.
- Não inventar ano.
- Não inventar horário.
- Não alterar qualificadores como (Elevado) ou (Reduzido).
- Manter capitalização normal de frase.

Formato obrigatório:

[DD/MM/AAAA HH:MM] Nome do exame: resultado || resultado || resultado

Regras adicionais:
- Data e hora sempre entre colchetes.
- Não usar hífen após a hora.
- Não quebrar linha após os dois pontos.
- Tudo deve permanecer na mesma linha.
- Se não houver ano, não inventar.
- Se não houver hora, manter apenas a data.
- Se o texto já vier estruturado, preservar o conteúdo e apenas reorganizar no formato acima.

Exemplo:
[10/03/2026 20:19] Gasometria arterial: pH 7,25 || pCO2 55 mmHg || HCO3 18 mmol/L

Texto bruto:
{texto}
"""

# ===============================================
# PROMPT — ORGANIZAÇÃO DE EXAMES DE IMAGEM
# ===============================================

def prompt_organizar_exames_imagem(texto):
    return f"""
Você é um assistente de organização de exames de imagem.

Regras obrigatórias:
- Não interpretar achados.
- Não resumir o exame.
- Não inventar ano.
- Não inventar horário.
- Manter capitalização normal de frase.

Formato obrigatório:

[DD/MM/AAAA HH:MM] Nome do exame: descrição

Regras adicionais:
- Data e hora sempre entre colchetes.
- Não usar hífen após a hora.
- Não quebrar linha após os dois pontos.
- Tudo deve permanecer na mesma linha.
- Se o texto já vier estruturado, preservar o conteúdo e apenas reorganizar no formato acima.

Exemplo:
[10/03/2026 21:10] Tomografia de tórax: infiltrado pulmonar bilateral.

Texto bruto:
{texto}
"""

# ===============================================
# FUNÇÃO — ORGANIZAR DOCUMENTO
# ===============================================

def organizar_com_ia(texto, tipo):
    client = cliente_openai()

    if tipo == "Atendimento Clínico":
        prompt = prompt_atendimento_clinico(texto)
    else:
        prompt = prompt_evolucao_medica(texto)

    response = client.responses.create(
        model=MODELO_IA,
        input=prompt
    )

    return response.output_text if response.output_text else ""


# ===============================================
# FUNÇÃO — GERAR SUGESTÕES
# ===============================================

def gerar_sugestoes_evidencia(texto):
    client = cliente_openai()

    response = client.responses.create(
        model=MODELO_IA,
        input=prompt_sugestoes_evidencia(texto)
    )

    return response.output_text if response.output_text else ""


# ===============================================
# FUNÇÃO — ORGANIZAR EXAMES LABORATORIAIS
# ===============================================

def organizar_exames_laboratoriais(texto):
    client = cliente_openai()

    if not texto or texto.strip() == "":
        return "-"

    response = client.responses.create(
        model=MODELO_IA,
        input=prompt_organizar_exames_laboratoriais(texto)
    )

    return response.output_text if response.output_text else "-"


# ===============================================
# FUNÇÃO — ORGANIZAR EXAMES DE IMAGEM
# ===============================================

def montar_exames_imagem(texto):
    client = cliente_openai()

    if not texto or texto.strip() == "":
        return "-"

    response = client.responses.create(
        model=MODELO_IA,
        input=prompt_organizar_exames_imagem(texto)
    )

    return response.output_text if response.output_text else "-"