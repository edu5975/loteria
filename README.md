
GUÍA RÁPIDA — Lotería con imágenes (PDF automático)

1) Requisitos en tu computadora
   - Python 3.9+
   - pip install reporta Pillow pandas

2) Prepara tus imágenes
   - Crea una carpeta, por ejemplo: images/
   - Coloca dentro las 54 imágenes (una por carta).
   - Renómbralas y actualiza el archivo cards_template.csv en la columna 'filename'.
     *Ejemplo: 01_Harry_Potter.jpg, 02_Hermione_Granger.jpg, etc.*

3) Edita el CSV
   - Abre cards_template.csv y verifica:
     id (1..54), name (no cambiar si no quieres), filename (coincide con tu archivo en images/).

4) Ejecuta el generador
   - python make_loteria_pdf.py --csv cards_template.csv --images images --out Loteria.pdf


5) ¿Qué genera?
   - 54 páginas de cartas: imagen grande + nombre.
   - 20 páginas de tableros 4x4: con imágenes + pie de imagen.
   - El tamaño y proporción de imagen se ajusta automáticamente para encajar sin deformarse.

6) Consejos
   - Cambia --seed para generar combinaciones distintas de los tableros.
   - Si alguna imagen se ve rara, revisa la resolución original (ideal ≥ 800px por lado).
   - Puedes abrir el PDF final y, si quieres, imprimir por rangos (solo cartas o solo tableros).

¡Listo! PDF listo para imprimir y jugar.
