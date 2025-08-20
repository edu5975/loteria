#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Lotería a PDF con IMÁGENES (cover + divisiones limpias).

Salida por defecto:
  - cartas.pdf   -> cartas 16 por hoja (4x4), vertical, con líneas de corte y marco.
  - tableros.pdf -> un tablero 4x4 por hoja, vertical, con marco y fondo pergamino.

Cambios:
  - Imagen con "cover real": recorte automático centrado para llenar todo el área de imagen.
  - Texto negro, DEBAJO de la imagen.
  - Ajustes de layout para evitar solapes (padding y top/bottom bien calculados).

Requisitos:
  pip install reportlab Pillow pandas

Correr:
  python make_loteria_pdf.py --csv cards_template.csv --images images --seed 42 --verbose  
  

"""

import os
import sys
import random
import argparse
import pandas as pd
from PIL import Image

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# --- Página (vertical carta) ---
PAGE_W, PAGE_H = letter
MARGIN = 0.5 * inch

# --- Cartas (16 por hoja, 4x4) ---
CARDS_GRID_R = 4
CARDS_GRID_C = 4
GRID_GAP = 0.22 * inch  # un poco más de respiro para que no se sienta apretado
CARD_CELL_W = (PAGE_W - 2*MARGIN - (CARDS_GRID_C-1)*GRID_GAP) / CARDS_GRID_C
CARD_CELL_H = (PAGE_H - 2*MARGIN - (CARDS_GRID_R-1)*GRID_GAP) / CARDS_GRID_R

CARD_CAPTION_H   = 0.34 * inch  # altura reservada para el nombre (debajo)
CARD_FRAME_INSET = 2            # marco interno de la carta
CARD_IMG_PAD     = 0.06 * inch  # padding interno del área de imagen

# --- Tablero (uno por hoja, 4x4) ---
BOARD_ROWS, BOARD_COLS = 4, 4
BOARD_TITLE_H   = 0.6 * inch
BOARD_TITLE_SZ  = 22
BOARD_CELL_GAP  = 0.18 * inch
BOARD_CAPTION_H = 0.30 * inch
BOARD_IMG_PAD   = 0.06 * inch

def die(msg, code=1):
    sys.stderr.write(str(msg) + "\n")
    sys.exit(code)

def assert_exists(path, what="archivo"):
    if not os.path.exists(path):
        die(f"[ERROR] No se encontró {what}: {path}")

def try_read_csv(csv_file, encoding=None, verbose=False):
    tried = []
    encodings_to_try = []
    if encoding:
        encodings_to_try.append(encoding)
    encodings_to_try += ["utf-8", "utf-8-sig", "cp1252", "latin1"]

    last_err = None
    df = None
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(csv_file, encoding=enc)
            if verbose:
                print(f"[INFO] CSV leído con encoding: {enc}")
            break
        except Exception as e:
            tried.append(enc)
            last_err = e
    if df is None:
        die(f"[ERROR] No pude leer el CSV con {tried}. Último error: {last_err}")
    return df

def read_cards(csv_file, images_dir, verbose=False, encoding=None):
    if verbose: print(f"[INFO] Leyendo CSV: {csv_file}")
    df = try_read_csv(csv_file, encoding=encoding, verbose=verbose)

    missing = set(["id","name","filename"]) - set(df.columns)
    if missing:
        die(f"[ERROR] Faltan columnas en el CSV: {missing}. Debe tener: id,name,filename")

    if len(df) != 54:
        print(f"[WARN] Se esperaban 54 filas, encontradas: {len(df)}")

    # Validar imágenes
    for _, row in df.iterrows():
        fn = str(row["filename"]).strip()
        img_path = os.path.join(images_dir, fn)
        if not os.path.isfile(img_path):
            die(f"[ERROR] No se encontró la imagen: {img_path}\n       Revisa 'filename' en el CSV o la carpeta --images.")

    if verbose: print(f"[INFO] CSV e imágenes OK ({len(df)} filas).")
    return df

def draw_centered_string(c, x, y, w, text, font_name="Helvetica-Bold", font_size=24, color=colors.black):
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    text_w = c.stringWidth(text, font_name, font_size)
    c.drawString(x + (w - text_w) / 2.0, y, text)

def draw_parchment_background(c):
    """Fondo con borde ."""
    c.setFillColorRGB(0.98, 0.95, 0.88)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setStrokeColorRGB(0.5, 0.35, 0.15)
    c.setLineWidth(3)
    inset = 0.25 * inch
    c.roundRect(inset, inset, PAGE_W-2*inset, PAGE_H-2*inset, 12, stroke=1, fill=0)
    c.setStrokeColorRGB(0.35, 0.2, 0.05)
    c.setLineWidth(2)

def draw_cut_lines_for_grid(c, origin_x, origin_y, cell_w, cell_h, rows, cols, gap):
    """Líneas de corte internas + marcas perimetrales (no tocan las imágenes)."""
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    total_w = cols*cell_w + (cols-1)*gap
    total_h = rows*cell_h + (rows-1)*gap
    # verticales internas
    for i in range(1, cols):
        x = origin_x + i*cell_w + (i-1)*gap + gap/2.0
        c.line(x, origin_y - total_h, x, origin_y)
    # horizontales internas
    for j in range(1, rows):
        y = origin_y - j*cell_h - (j-1)*gap - gap/2.0
        c.line(origin_x, y, origin_x + total_w, y)
    # crop marks exteriores
    mark = 0.15 * inch
    c.line(origin_x, origin_y+mark/2, origin_x, origin_y-mark/2)
    c.line(origin_x+total_w, origin_y+mark/2, origin_x+total_w, origin_y-mark/2)
    c.line(origin_x, origin_y - total_h + mark/2, origin_x, origin_y - total_h - mark/2)
    c.line(origin_x+total_w, origin_y - total_h + mark/2, origin_x+total_w, origin_y - total_h - mark/2)
    c.line(origin_x - mark/2, origin_y, origin_x + mark/2, origin_y)
    c.line(origin_x - mark/2, origin_y - total_h, origin_x + mark/2, origin_y - total_h)
    c.line(origin_x + total_w - mark/2, origin_y, origin_x + total_w + mark/2, origin_y)
    c.line(origin_x + total_w - mark/2, origin_y - total_h, origin_x + total_w + mark/2, origin_y - total_h)

# -------- COVER: recorte centrado para llenar el box completo --------
def draw_image_cover(c, img_path, x, y, w, h):
    """
    Dibuja la imagen llenando EXACTAMENTE el rectángulo (x,y,w,h) con recorte centrado (cover).
    x,y en ReportLab son esquina inferior izquierda del cuadro destino.
    """
    with Image.open(img_path) as im:
        iw, ih = im.size
        box_aspect = w / h
        img_aspect = iw / ih

        # Si la imagen es "más ancha" que el box, recortamos ancho; si es más alta, recortamos alto.
        if img_aspect > box_aspect:
            # recortar izquierda/derecha
            new_w = int(ih * box_aspect)
            offset_x = (iw - new_w) // 2
            crop_box = (offset_x, 0, offset_x + new_w, ih)
        else:
            # recortar arriba/abajo
            new_h = int(iw / box_aspect)
            offset_y = (ih - new_h) // 2
            crop_box = (0, offset_y, iw, offset_y + new_h)

        im_cropped = im.crop(crop_box)
        # Ahora im_cropped tiene el aspect ratio del box. Escalamos al tamaño exacto.
        c.drawImage(ImageReader(im_cropped), x, y, width=w, height=h, preserveAspectRatio=False, mask='auto')

# ------------------- CARTAS -------------------
# ------------------- CARTAS -------------------
def add_cards_page_grid16(c, items):
    """
    Dibuja una hoja con hasta 16 cartas (4x4).
    TEXTO ARRIBA (negro) y la imagen debajo ocupando TODO su área (cover).
    """
    draw_parchment_background(c)
    origin_x = MARGIN
    origin_y = PAGE_H - MARGIN

    # Líneas de corte del grid
    draw_cut_lines_for_grid(c, origin_x, origin_y, CARD_CELL_W, CARD_CELL_H, CARDS_GRID_R, CARDS_GRID_C, GRID_GAP)

    idx = 0
    cur_y_top = origin_y
    for r in range(CARDS_GRID_R):
        cur_x_left = origin_x
        for col in range(CARDS_GRID_C):
            if idx < len(items):
                it = items[idx]
                cell_x = cur_x_left
                cell_y = cur_y_top - CARD_CELL_H

                # Marco de carta (decorativo)
                c.setLineWidth(1.4)
                c.setStrokeColor(colors.darkgoldenrod)
                c.rect(cell_x + CARD_FRAME_INSET, cell_y + CARD_FRAME_INSET,
                       CARD_CELL_W - 2*CARD_FRAME_INSET, CARD_CELL_H - 2*CARD_FRAME_INSET, stroke=1, fill=0)

                # --- TEXTO ARRIBA ---
                font_caption = "Helvetica"
                c.setFont(font_caption, 10.5)
                c.setFillColor(colors.black)
                txt = it["name"]
                # recorte si sobrepasa
                while c.stringWidth(txt, font_caption, 10.5) > (CARD_CELL_W - 10):
                    txt = txt[:-1]
                    if len(txt) <= 3:
                        break
                caption_y = cell_y + CARD_CELL_H - CARD_CAPTION_H + 0.06 * inch
                draw_centered_string(c, cell_x, caption_y, CARD_CELL_W, txt,
                                     font_name=font_caption, font_size=10.5, color=colors.black)

                # --- IMAGEN DEBAJO (cover) ---
                img_x = cell_x + CARD_IMG_PAD
                img_y = cell_y + CARD_IMG_PAD
                img_w = CARD_CELL_W - 2*CARD_IMG_PAD
                img_h = CARD_CELL_H - CARD_CAPTION_H - 2*CARD_IMG_PAD
                draw_image_cover(c, it["img_path"], img_x, img_y, img_w, img_h)

            cur_x_left += CARD_CELL_W + GRID_GAP
            idx += 1
        cur_y_top -= CARD_CELL_H + GRID_GAP
    c.showPage()
# ------------------- TABLERO (UNO POR HOJA) -------------------
def add_board_fullpage(c, board_index, items):
    """Un tablero por página. TEXTO ARRIBA y la imagen debajo (cover) en cada casilla."""
    draw_parchment_background(c)

    # Título del tablero
    draw_centered_string(c, MARGIN, PAGE_H - MARGIN - BOARD_TITLE_H + 0.10*inch,
                         PAGE_W - 2*MARGIN, f"Tablero {board_index+1}",
                         font_name="Helvetica-Bold", font_size=BOARD_TITLE_SZ, color=colors.black)

    # Área del tablero
    top_y = PAGE_H - MARGIN - BOARD_TITLE_H - 0.10*inch
    avail_h = top_y - MARGIN
    avail_w = PAGE_W - 2*MARGIN
    inner_margin = 0.10 * inch
    grid_x_left = MARGIN + inner_margin
    grid_y_top  = top_y - inner_margin
    grid_w      = avail_w - 2*inner_margin
    grid_h      = avail_h - 2*inner_margin

    # Marco exterior del tablero
    c.setStrokeColor(colors.darkgoldenrod)
    c.setLineWidth(2)
    c.roundRect(MARGIN, MARGIN, avail_w, avail_h, 12, stroke=1, fill=0)

    # Celdas
    cell_w = (grid_w - (BOARD_COLS-1)*BOARD_CELL_GAP) / BOARD_COLS
    cell_h = (grid_h - (BOARD_ROWS-1)*BOARD_CELL_GAP) / BOARD_ROWS

    cur_y_top = grid_y_top
    idx = 0
    for r in range(BOARD_ROWS):
        cur_x_left = grid_x_left
        for col in range(BOARD_COLS):
            it = items[idx]
            cell_x = cur_x_left
            cell_y = cur_y_top - cell_h

            # Marco de celda
            c.setLineWidth(1)
            c.setStrokeColor(colors.black)
            c.rect(cell_x, cell_y, cell_w, cell_h, stroke=1, fill=0)

            # --- TEXTO ARRIBA ---
            font_caption = "Helvetica"
            c.setFont(font_caption, 10.5)
            c.setFillColor(colors.black)
            txt = it["name"]
            while c.stringWidth(txt, font_caption, 10.5) > (cell_w - 10):
                txt = txt[:-1]
                if len(txt) <= 3:
                    break
            caption_y = cell_y + cell_h - BOARD_CAPTION_H + 0.06 * inch
            draw_centered_string(c, cell_x, caption_y, cell_w, txt,
                                 font_name=font_caption, font_size=10.5, color=colors.black)

            # --- IMAGEN DEBAJO (cover) ---
            img_x = cell_x + BOARD_IMG_PAD
            img_y = cell_y + BOARD_IMG_PAD
            img_w = cell_w - 2*BOARD_IMG_PAD
            img_h = cell_h - BOARD_CAPTION_H - 2*BOARD_IMG_PAD
            draw_image_cover(c, it["img_path"], img_x, img_y, img_w, img_h)

            cur_x_left += cell_w + BOARD_CELL_GAP
            idx += 1
        cur_y_top -= cell_h + BOARD_CELL_GAP
    c.showPage()

# ------------------- ORQUESTA -------------------
def generate_cards_pdf(items, out_cards="cartas.pdf", verbose=False):
    if verbose: print(f"[INFO] Generando cartas -> {out_cards}")
    c = canvas.Canvas(out_cards, pagesize=letter)
    for i in range(0, len(items), 16):
        chunk = items[i:i+16]
        add_cards_page_grid16(c, chunk)
    c.save()
    if verbose: print(f"[OK] Cartas PDF generado: {out_cards}")

def generate_boards_pdf(items, seed=42, out_boards="tableros.pdf", verbose=False):
    if verbose: print(f"[INFO] Generando tableros -> {out_boards}")
    random.seed(seed)
    c = canvas.Canvas(out_boards, pagesize=letter)
    for b in range(20):
        selection = random.sample(items, 16)
        add_board_fullpage(c, b, selection)
    c.save()
    if verbose: print(f"[OK] Tableros PDF generado: {out_boards}")

def main():
    ap = argparse.ArgumentParser(description="Genera Lotería PDF (cartas en 'cartas.pdf' y tableros en 'tableros.pdf').")
    ap.add_argument("--csv", required=True, help="CSV con columnas id,name,filename")
    ap.add_argument("--images", required=True, help="Carpeta de imágenes")
    ap.add_argument("--seed", type=int, default=42, help="Semilla para tableros reproducibles")
    ap.add_argument("--verbose", action="store_true", help="Mensajes detallados")
    ap.add_argument("--encoding", default=None, help="Codificación del CSV (opcional): utf-8, cp1252, latin1")
    # Permitir sobrescribir nombres de salida
    ap.add_argument("--out-cards", default="cartas.pdf", help="Nombre del PDF de cartas (opcional)")
    ap.add_argument("--out-boards", default="tableros.pdf", help="Nombre del PDF de tableros (opcional)")
    args = ap.parse_args()

    assert_exists(args.csv, "el CSV")
    assert_exists(args.images, "la carpeta de imágenes")
    df = read_cards(args.csv, args.images, verbose=args.verbose, encoding=args.encoding)

    # Construir lista ordenada por id
    items = []
    for _, row in df.iterrows():
        items.append({
            "id": int(row["id"]),
            "name": str(row["name"]).strip(),
            "img_path": os.path.join(args.images, str(row["filename"]).strip())
        })
    items.sort(key=lambda x: x["id"])

    # Generar PDFs
    generate_cards_pdf(items, out_cards=args.out_cards, verbose=args.verbose)
    generate_boards_pdf(items, seed=args.seed, out_boards=args.out_boards, verbose=args.verbose)

if __name__ == "__main__":
    main()
