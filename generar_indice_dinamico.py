from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os

# Colores extraídos del INDICE original
COLOR_TEXT_MAIN = colors.HexColor("#081233") # Azul Marino
COLOR_ACCENT = colors.HexColor("#F5AD14")    # Dorado/Naranja
COLOR_BLACK = colors.black

def generar_indice(cat_start_pages, output_path="templates/INDICE.pdf"):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 1. TÍTULO "ÍNDICE"
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(COLOR_TEXT_MAIN)
    c.drawCentredString(width / 2.0, height - 70, "ÍNDICE")
    
    # 2. LISTA DE CATEGORÍAS
    c.setFont("Helvetica-Bold", 18)
    
    # Categorías en el orden correcto
    orden_categorias = [
        ("CALZADO DE SEGURIDAD", 1),
        ("PROTECCIÓN CORPORAL", 2),
        ("PROTECCIÓN DE CABEZA", 3),
        ("PROTECCIÓN MANUAL", 4),
        ("PROTECCIÓN VISUAL", 5),
        ("PROTECCIÓN AUDITIVA", 6),
        ("PROTECCIÓN RESPIRATORIA", 7),
        ("PROTECCIÓN FACIAL", 8),
        ("SEÑALÉTICAS", 9),
        ("ACCESORIOS DE PROTECCIÓN VARIOS", 10),
    ]
    
    start_y = height - 150
    espaciado = 45 # Menor espaciado para que quepan 10 items
    
    for idx, (cat_name, cat_order) in enumerate(orden_categorias):
        y_pos = start_y - (idx * espaciado)
        
        # Obtener número de página del diccionario, si no existe, poner '-'
        page_num = cat_start_pages.get(cat_name, "-")
        
        # Dibujar nombre de la categoría
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(COLOR_TEXT_MAIN)
        texto_cat = f"{cat_order}. {cat_name}"
        c.drawString(50, y_pos, texto_cat)
        
        # Dibujar puntos suspensivos (opcional, para dar estilo de índice)
        # o simplemente poner el número de página alineado a la derecha
        
        # Dibujar número de página (más grande y color dorado)
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(COLOR_ACCENT)
        # Alinear a la derecha (cerca del margen derecho)
        c.drawRightString(width - 50, y_pos - 4, str(page_num))
        
        # Línea divisoria muy sutil (opcional, mejora el diseño)
        c.setStrokeColor(colors.HexColor("#E2E8F0")) # Gris muy claro
        c.setLineWidth(0.5)
        c.line(50, y_pos - 15, width - 50, y_pos - 15)

    # 3. FOOTER (Información de contacto)
    footer_y = 150
    c.setStrokeColor(COLOR_ACCENT)
    c.setLineWidth(2)
    c.line(50, footer_y + 25, width - 50, footer_y + 25) # Línea superior del footer
    
    # Bloque Izquierdo (Correo)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(COLOR_ACCENT)
    c.drawString(50, footer_y, "CORREO ELECTRÓNICO")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(COLOR_BLACK)
    c.drawString(50, footer_y - 20, "VENTAS@PROSEGIN.COM")
    
    # Bloque Medio (Número)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(COLOR_ACCENT)
    c.drawCentredString(width / 2.0, footer_y, "NÚMERO")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(COLOR_BLACK)
    c.drawCentredString(width / 2.0, footer_y - 20, "989 983 227")
    
    # Bloque Inferior (Dirección)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(COLOR_ACCENT)
    c.drawCentredString(width / 2.0, footer_y - 60, "AV. GUILLERMO DANSEY NRO. 354 URB. LIMA")
    c.drawCentredString(width / 2.0, footer_y - 78, "INDUSTRIAL - PISO 2 TIENDA A2")

    c.save()
    print(f"✅ Índice generado en {output_path}")

if __name__ == '__main__':
    # Datos de prueba para previsualizar el diseño
    dummy_pages = {
        "CALZADO DE SEGURIDAD": 1,
        "PROTECCIÓN CORPORAL": 12,
        "PROTECCIÓN DE CABEZA": 36,
        "PROTECCIÓN MANUAL": 40,
        "PROTECCIÓN VISUAL": 57,
        "PROTECCIÓN AUDITIVA": 67,
        "PROTECCIÓN RESPIRATORIA": 70,
        "PROTECCIÓN FACIAL": 75,
        "SEÑALÉTICAS": 80,
        "ACCESORIOS DE PROTECCIÓN VARIOS": 86,
    }
    
    generar_indice(dummy_pages, "templates/INDICE_NUEVO.pdf")
