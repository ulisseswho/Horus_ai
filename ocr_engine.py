from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes


def extrair_texto_imagem(arquivo):
    imagem = Image.open(arquivo)
    return pytesseract.image_to_string(imagem)


def extrair_texto_pdf(arquivo):
    paginas = convert_from_bytes(arquivo.read())
    texto_total = ""

    for pagina in paginas:
        texto_total += pytesseract.image_to_string(pagina) + "\n"

    return texto_total
