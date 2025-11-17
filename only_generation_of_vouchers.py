# generar_vales_barcode.py
# Genera imágenes con número de vale, código de barras (Code128, 18 dígitos),
# cuadro de condiciones, monto formateado, cuadro "Monto" y cuadro de vencimiento "Vto".

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from textwrap import wrap

# -------- CONFIGURACIÓN GENERAL --------
CSV_PATH = r"C:\Users\caguayo\Desktop\datos\vales.csv"
IMAGE_PATH = r"C:\Users\caguayo\Desktop\datos\base.jpg"
COLUMN_NAME = "CODIGO"
COLUMN_MONTO = "SALDO"
OUTPUT_FOLDER_NAME = "Vales"

# Posiciones editables
TEXT_POSITION = (340, 265)
BARCODE_POSITION = (300, 150)
TEXTBOX_POSITION = (120, 310)
MONTO_POSITION = (780, 538)
MONTO_LABEL_POSITION = (700, 540)

# Cuadro "Monto"
MONTO_LABEL_SIZE = (10, 20)
MONTO_LABEL_FILL = (255, 255, 255)
MONTO_LABEL_TEXT = "Monto"

# Fuente
FONT_PATH = r"C:\Windows\Fonts\Poppins-ExtraLight.ttf"  # Cambiar ruta si es necesario
FONT_SIZE = 30
BOLD_FONT_PATH = r"C:\Windows\Fonts\arialbd.ttf"
TEXT_FILL = (0, 0, 0)

# -------- CUADRO DE TEXTO --------
TEXTBOX_SIZE = (700, 50)
TEXTBOX_FILL = (255, 255, 255)

TEXTBOX_MESSAGE = (
    "Con la sola presentación de esta orden y su documento de identidad se le "
    "expedirá mercaderías por el valor de Gs. {monto} "
    "({monto_letras})\n"
    "Orden de Compra válida en cualquiera de las sucursales de CADENA REAL S.A"
)

# -------- CONFIGURACIÓN NUEVA: VENCIMIENTO -------
VTO_LABEL_TEXT = "Vto"
VTO_LABEL_POSITION = (600, 570)
VTO_LABEL_SIZE = (180, 40)
VTO_DATE_POSITION = (740, 580)
VTO_DATE_VALUE = "30/11/2025"
# -----------------------------------------------

def get_desktop_vales_folder():
    desktop = Path.home() / "Desktop"
    out = desktop / OUTPUT_FOLDER_NAME
    out.mkdir(parents=True, exist_ok=True)
    return out

def load_font(font_path=None, size=48):
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size=size)
        for candidate in ["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
            try:
                return ImageFont.truetype(candidate, size=size)
            except Exception:
                continue
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()

def generate_barcode_image(number):
    number_digits = "".join(filter(str.isdigit, number))
    code = barcode.get("code128", number_digits, writer=ImageWriter())
    temp_path = Path("temp_barcode")
    saved_path = code.save(
        str(temp_path),
        {"module_height": 90, "quiet_zone": 2, "write_text": False}
    )
    barcode_img = Image.open(saved_path).convert("RGBA")
    os.remove(saved_path)
    CM_TO_PX = 37.8
    target_width = int(10 * CM_TO_PX)
    target_height = int(3 * CM_TO_PX)
    barcode_img = barcode_img.resize((target_width, target_height), Image.LANCZOS)
    return barcode_img

def formatear_monto(valor):
    """Limpia y deja el monto en formato: 75.000 Gs"""
    monto_raw = str(valor).strip()
    monto_limpio = monto_raw.replace(".", "").replace(",", "").replace(" ", "")
    monto_digits = "".join(c for c in monto_limpio if c.isdigit())
    if monto_digits == "":
        monto_digits = "0"
    monto_int = int(monto_digits)
    monto_formateado = f"{monto_int:,}".replace(",", ".")
    return f"{monto_formateado} Gs"

# Función para convertir número a letras (simplificada para Guaraníes)
UNIDADES = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
DECENAS = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
ESPECIALES = {11:"once",12:"doce",13:"trece",14:"catorce",15:"quince",
             16:"dieciseis",17:"diecisiete",18:"dieciocho",19:"diecinueve"}

def numero_a_letras(n):
    n = int(n)
    if n == 0:
        return "cero guaranies"
    miles = n // 1000
    resto = n % 1000
    letras = ""
    if miles > 0:
        letras += f"{numero_a_letras(miles).replace(' guaranies','')} mil "
    centenas = resto // 100
    decenas = (resto % 100) // 10
    unidades = resto % 10
    if resto % 100 in ESPECIALES:
        letras += ESPECIALES[resto % 100] + " "
    else:
        if centenas > 0:
            if centenas == 1 and resto % 100 == 0:
                letras += "cien "
            elif centenas == 1:
                letras += "ciento "
            elif centenas == 5:
                letras += "quinientos "
            elif centenas == 7:
                letras += "setecientos "
            elif centenas == 9:
                letras += "novecientos "
            else:
                letras += UNIDADES[centenas] + "cientos "
        if decenas > 0:
            letras += DECENAS[decenas]
            if unidades > 0:
                letras += " y "
        if unidades > 0 and resto % 100 not in ESPECIALES:
            letras += UNIDADES[unidades]
    letras = letras.strip() + " guaranies"
    return letras.lower()

def main():
    if not os.path.exists(CSV_PATH):
        print(f"❌ ERROR: No se encontró el archivo CSV en: {CSV_PATH}")
        return
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ ERROR: No se encontró la imagen base en: {IMAGE_PATH}")
        return

    df = pd.read_csv(CSV_PATH, sep=';')
    df.columns = [c.strip() for c in df.columns]
    print("Columnas encontradas en CSV:", df.columns.tolist())
    if COLUMN_NAME not in df.columns or COLUMN_MONTO not in df.columns:
        print(f"❌ ERROR: Verifica que '{COLUMN_NAME}' y '{COLUMN_MONTO}' existan en el CSV.")
        return

    out_folder = get_desktop_vales_folder()
    font = load_font(FONT_PATH, FONT_SIZE)
    font_bold = load_font(BOLD_FONT_PATH, FONT_SIZE)
    base_img = Image.open(IMAGE_PATH).convert("RGB")

    print(f"🖼️ Imagen base cargada ({base_img.size[0]}x{base_img.size[1]})")
    print(f"📋 Total de vales: {len(df)}")
    print(f"📁 Guardando en: {out_folder}\n")

    for idx, row in df.iterrows():
        img = base_img.copy()
        draw = ImageDraw.Draw(img)

        # Número de vale
        num = str(int(float(row[COLUMN_NAME])))

        # Código de barras
        barcode_img = generate_barcode_image(num)
        img.paste(barcode_img, BARCODE_POSITION, barcode_img)

        draw.text(TEXT_POSITION, num, font=font, fill=TEXT_FILL)

        # Cuadro de condiciones
        x, y = TEXTBOX_POSITION
        w, h = TEXTBOX_SIZE
        draw.rectangle([(x, y), (x + w, y + h)], fill=TEXTBOX_FILL)

        # Monto formateado
        monto_final = formatear_monto(row[COLUMN_MONTO])
        monto_letras = numero_a_letras(row[COLUMN_MONTO])

        mensaje_personalizado = TEXTBOX_MESSAGE.format(monto=monto_final, monto_letras=monto_letras)
        lines = wrap(mensaje_personalizado, 60)
        current_y = y + 5
        for line in lines:
            draw.text((x + 8, current_y), line, font=font, fill=TEXT_FILL)
            current_y += FONT_SIZE + 5

        # Cuadro "Monto"
        x_label, y_label = MONTO_LABEL_POSITION
        w_label, h_label = MONTO_LABEL_SIZE
        draw.rectangle([(x_label, y_label), (x_label + w_label, y_label + h_label)], fill=MONTO_LABEL_FILL)
        bbox = draw.textbbox((0, 0), MONTO_LABEL_TEXT, font=font_bold)
        text_x = x_label + (w_label - (bbox[2] - bbox[0])) / 2
        text_y = y_label + (h_label - (bbox[3] - bbox[1])) / 2
        draw.text((text_x, text_y), MONTO_LABEL_TEXT, font=font_bold, fill=TEXT_FILL)
        draw.text(MONTO_POSITION, monto_final, font=font, fill=TEXT_FILL)

        # Cuadro Vto + Fecha
        x_vto, y_vto = VTO_LABEL_POSITION
        w_vto, h_vto = VTO_LABEL_SIZE
        draw.rectangle([(x_vto, y_vto), (x_vto + w_vto, y_vto + h_vto)], fill=(255, 255, 255))
        bbox_vto = draw.textbbox((0, 0), VTO_LABEL_TEXT, font=font_bold)
        text_x_vto = x_vto + (w_vto - (bbox_vto[2] - bbox_vto[0])) / 2
        text_y_vto = y_vto + (h_vto - (bbox_vto[3] - bbox_vto[1])) / 2
        draw.text((text_x_vto, text_y_vto), VTO_LABEL_TEXT, font=font_bold, fill=TEXT_FILL)
        draw.text(VTO_DATE_POSITION, VTO_DATE_VALUE, font=font, fill=TEXT_FILL)

        # Guardado
        filename = f"{str(idx+1).zfill(4)}_{num}.jpg"
        img.save(out_folder / filename, quality=95)
        if (idx + 1) % 50 == 0 or idx == len(df) - 1:
            print(f"  ✅ Generado {idx+1}/{len(df)} → {filename}")

    print("\n🎉 ¡Listo! Todas las imágenes se generaron correctamente.")
    print("📂 Carpeta de salida:", out_folder)

if __name__ == "__main__":
    main()
