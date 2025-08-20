# 🎲 Lotería de Harry Potter

Generador de **lotería personalizada** con temática de _Harry Potter_ en formato **PDF**.  
Crea automáticamente:

- **Cartas** → 54 imágenes, 16 por hoja (4x4), con recorte tipo _cover_, marco y líneas de corte.
- **Tableros** → 20 tablas (una por hoja, 4x4), generadas de forma aleatoria pero reproducible con semilla.

---

## 📂 Estructura del proyecto

loteria/
├── make_loteria_pdf.py # Script principal
├── cards_template.csv # Plantilla de cartas (id, name, filename)
├── images/ # Carpeta con las imágenes de las cartas
├── cartas.pdf # (Salida) Todas las cartas, 16 por hoja
├── tableros.pdf # (Salida) Tableros de juego, 1 por hoja
├── README.md # Este archivo
└── .gitignore

---

## ⚡ Requisitos

- Python **3.8+**
- Librerías:
  ```bash
  pip install reportlab pillow pandas
  ```

📋 Uso

Prepara tu CSV (cards_template.csv) con las columnas:

id → número de la carta (1 a 54).

name → nombre de la carta.

filename → nombre del archivo de la imagen (ubicada en images/).

Ejemplo:

id,name,filename
1,Harry Potter,harry.jpg
2,Hermione Granger,hermione.png
3,Ron Weasley,ron.jpg
...

Coloca las imágenes en la carpeta images/.

Genera los PDFs ejecutando:

python make_loteria_pdf.py --csv cards_template.csv --images images --seed 42 --verbose

👉 El script produce:

cartas.pdf
tableros.pdf

🎨 Personalización

El script dibuja fondo tipo pergamino y marcos dorados.
El texto está en negro y usa la fuente Helvetica.
El layout asegura que no haya solapamientos entre imágenes y texto.

🧙 Objetivo

Proyecto creado para que puedas hacer tus propias loterias tematicas.
