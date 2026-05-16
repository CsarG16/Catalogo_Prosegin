import os
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer, PageBreak, HRFlowable, Flowable
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
import pathlib
import fitz  # Para unir la portada PDF al catálogo final
from reportlab.platypus import Flowable
import procesar_imagenes

# ==========================================
# PALETA DE COLORES PARA PRODUCTOS (Swatches)
# ==========================================
PRODUCT_COLORS = {
    'plomo': '#9CA3AF',
    'azul marino': '#1E3A8A',
    'blanco': '#FFFFFF',
    'negro': '#000000',
    'beige': '#D1BFA7',
    'azul electrico': '#2563EB',
    'amarillo': '#FDE047',
    'rojo': '#EF4444',
    'naranja': '#F97316',
    'verde': '#22C55E'
}

class ColorCircles(Flowable):
    def __init__(self, color_names):
        Flowable.__init__(self)
        self.colors_to_draw = []
        for c in color_names:
            c_clean = c.strip().lower()
            if c_clean in PRODUCT_COLORS:
                self.colors_to_draw.append(PRODUCT_COLORS[c_clean])
        
        self.size = 0.35 * cm
        self.padding = 0.15 * cm
        self.width = len(self.colors_to_draw) * (self.size + self.padding)
        self.height = self.size

    def draw(self):
        for i, color_hex in enumerate(self.colors_to_draw):
            self.canv.saveState()
            self.canv.setFillColor(colors.HexColor(color_hex))
            x = i * (self.size + self.padding)
            # Borde sutil para todos los círculos (da un aspecto más premium)
            self.canv.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.canv.setLineWidth(0.5)
            self.canv.circle(x + self.size/2, self.size/2, self.size/2, fill=1, stroke=1)
            self.canv.restoreState()


# ==========================================
# REGISTRO DE FUENTES PREMIUM
# ==========================================
try:
    pdfmetrics.registerFont(TTFont('Georgia', r'C:\Windows\Fonts\georgia.ttf'))
    pdfmetrics.registerFont(TTFont('Georgia-Bold', r'C:\Windows\Fonts\georgiab.ttf'))
    pdfmetrics.registerFont(TTFont('Georgia-Italic', r'C:\Windows\Fonts\georgiai.ttf'))
    pdfmetrics.registerFont(TTFont('Calibri', r'C:\Windows\Fonts\calibri.ttf'))
    pdfmetrics.registerFont(TTFont('Calibri-Bold', r'C:\Windows\Fonts\calibrib.ttf'))
    pdfmetrics.registerFont(TTFont('Calibri-Light', r'C:\Windows\Fonts\calibril.ttf'))
except Exception as e:
    print(f"⚠️ Algunas fuentes no se pudieron registrar: {e}")

# Configuración de Rutas
DATA_PATH = "data/catalogo_db.xlsx"
IMG_PATH = "imagenes_procesadas"
OUTPUT_PATH = "output/catalogo_final.pdf"

# ==========================================
# PALETA DE COLORES CORPORATIVOS (Extraídos del Logo)
# ==========================================
COLOR_TEXT_MAIN = colors.HexColor("#081233")   # Azul Marino Oscuro (Texto Principal)
COLOR_TEXT_MUTED = colors.HexColor("#6B6E7A")  # Gris Medio (Textos secundarios)
COLOR_ACCENT = colors.HexColor("#F5AD14")      # Amarillo/Dorado (Precios y Destaques)
COLOR_LINE = colors.HexColor("#E3D2AB")        # Dorado suave (Líneas divisorias)

def crear_marca_de_agua(logo_path, watermark_path, opacidad=0.05):
    """Generate a translucent version of the logo for use as a watermark."""
    if not os.path.exists(logo_path):
        return False
        
    # Refresh watermark if logo is newer or watermark doesn't exist
    if not os.path.exists(watermark_path) or os.path.getmtime(logo_path) > os.path.getmtime(watermark_path):
        try:
            img = PILImage.open(logo_path).convert("RGBA")
            # Reducir la opacidad de todos los píxeles
            data = img.getdata()
            new_data = []
            for item in data:
                # El canal alfa es el índice 3
                new_data.append((item[0], item[1], item[2], int(item[3] * opacidad)))
            img.putdata(new_data)
            img.save(watermark_path, "PNG")
            return True
        except Exception as e:
            print(f"⚠️ No se pudo crear la marca de agua: {e}")
            return False
    return True

def quitar_fondo_blanco(img_path):
    """
    Converts white pixels of an image to transparent and saves to cache.
    Re-processes if the source image is newer than the cached one.
    """
    if not os.path.exists(img_path):
        return img_path
        
    cache_dir = "imagenes_transparentes_cache"
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)
    
    filename = os.path.basename(img_path)
    base_name = os.path.splitext(filename)[0]
    out_path = os.path.join(cache_dir, base_name + ".png")  # PNG con alfa: necesario para que el watermark del fondo sea visible
    
    # Check if cache exists and is up to date
    if os.path.exists(out_path) and os.path.getmtime(img_path) <= os.path.getmtime(out_path):
        # print(f"  [Cache] Usando versión existente: {base_name}.png")
        return out_path
        
    try:
        print(f"  [Procesando] Limpiando fondo de: {filename} -> {base_name}.png")
        img = PILImage.open(img_path).convert("RGBA")
        pixels = img.load()
        width, height = img.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                # Si el pixel es "casi blanco", lo hacemos transparente
                if r > 240 and g > 240 and b > 240:
                    pixels[x, y] = (255, 255, 255, 0)

        # Reducir a 250x250 como solicitado
        # + compresión máxima PNG: reduce ~75% vs 600x600 sin comprimir
        CACHE_SIZE = (250, 250)
        img = img.resize(CACHE_SIZE, PILImage.Resampling.LANCZOS)
        img.save(out_path, "PNG", compress_level=9, optimize=True)
        return out_path
    except Exception as e:
        print(f"⚠️ Error limpiando fondo de {filename}: {e}")
        return img_path

# Caché global para imágenes de ReportLab (evita duplicar objetos en el PDF)
_IMAGE_CACHE = {}

_PAGE_CATEGORIES = {}

def get_cached_image(path):
    if path not in _IMAGE_CACHE and os.path.exists(path):
        _IMAGE_CACHE[path] = ImageReader(path)
    return _IMAGE_CACHE.get(path)

def draw_corporate_header(canvas, category, width, height):
    """Dibuja el encabezado corporativo con logo y categoría."""
    logo_path = "logo_horizontal.png"
    logo = get_cached_image(logo_path)
    if logo:
        w, h = logo.getSize()
        aspect = w / float(h)
        target_h = 1.3 * cm
        target_w = target_h * aspect
        canvas.drawImage(logo, 1.5*cm, height - 1.8*cm, width=target_w, height=target_h, mask='auto')
    else:
        canvas.setFont('Helvetica-Bold', 9)
        canvas.setFillColor(COLOR_TEXT_MUTED)
        canvas.drawString(1.5*cm, height - 1.2*cm, "CATÁLOGO DE PRODUCTOS EPP")
        
    # Texto de la categoría a la derecha
    canvas.setFont('Helvetica-Bold', 12)
    canvas.setFillColor(COLOR_TEXT_MAIN)
    canvas.drawRightString(width - 1.5*cm, height - 1.4*cm, str(category).upper())
    
    # Línea divisoria del header (Dorada)
    canvas.setStrokeColor(COLOR_ACCENT)
    canvas.setLineWidth(1)
    canvas.line(1.5*cm, height - 2.0*cm, width - 1.5*cm, height - 2.0*cm)

def draw_corporate_footer(canvas, page_num, width, height):
    """Dibuja el pie de página corporativo con información de contacto y paginación."""
    footer_h = 1.4 * cm  # Altura de la barra del footer
    footer_y = 0          # Pegado al borde inferior
    
    # Fondo Azul Marino Corporativo
    canvas.setFillColor(COLOR_TEXT_MAIN)
    canvas.rect(0, footer_y, width, footer_h, fill=1, stroke=0)
    
    # Línea dorada superior decorativa
    canvas.setStrokeColor(COLOR_ACCENT)
    canvas.setLineWidth(2)
    canvas.line(0, footer_h, width, footer_h)
    
    # --- Sección Izquierda: Contacto ---
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(1.5*cm, footer_h - 0.60*cm, "Más información en:")
    
    canvas.setFont('Helvetica', 9)
    contact_y = footer_h - 1.05*cm
    # Correo
    email_text = "ventas@prosegin.com"
    canvas.drawString(1.5*cm, contact_y, email_text)
    email_w = canvas.stringWidth(email_text, 'Helvetica', 9)
    # Área clicable extendida para facilitar el toque
    canvas.linkURL(f"mailto:{email_text}", (1.5*cm, 0, 1.5*cm + email_w, footer_h), relative=0)
    
    # Separador
    canvas.setFillColor(COLOR_ACCENT)
    canvas.drawString(1.5*cm + email_w + 0.2*cm, contact_y, "|")
    # Teléfono
    canvas.setFillColor(colors.white)
    canvas.drawString(1.5*cm + email_w + 0.5*cm, contact_y, "989 983 227")
    
    # Link clickable para WhatsApp en el número (Área extendida)
    phone_x = 1.5*cm + email_w + 0.5*cm
    phone_w = canvas.stringWidth("989 983 227", 'Helvetica', 9)
    whatsapp_url = "https://wa.me/51989983227?text=Hola%2C%20quiero%20cotizar%21"
    canvas.linkURL(whatsapp_url, (phone_x, 0, phone_x + phone_w, footer_h), relative=0)
    
    # Espacio extra entre el número y la nueva sección (1.5 cm)
    address_x = phone_x + phone_w + 1.5*cm
    
    # Título "Encuéntranos aquí:"
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(address_x, footer_h - 0.60*cm, "Encuéntranos aquí:")
    
    # Dirección
    canvas.setFont('Helvetica', 9)
    address_text = "Av. Guillermo Dansey Nro. 354"
    canvas.drawString(address_x, contact_y, address_text)
    
    # Link clickable para Google Maps en la dirección (Área extendida)
    address_w = canvas.stringWidth(address_text, 'Helvetica', 9)
    gmaps_url = "https://maps.app.goo.gl/KQthqjJ5AKSJXRWWA"
    canvas.linkURL(gmaps_url, (address_x, 0, address_x + address_w, footer_h), relative=0)
    
    # --- Paginación ---
    if page_num:
        canvas.setFillColor(COLOR_ACCENT)
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawRightString(width - 1.5*cm, footer_h - 0.85*cm, f"Pág. {page_num}")

def draw_header_footer(canvas, doc):
    """Callback para ReportLab que dibuja header, footer y marca de agua."""
    canvas.saveState()
    width, height = A4
    
    # --- WATERMARK ---
    logo_path = "logo_horizontal.png"
    watermark_path = "watermark_temp_v3.png"
    if crear_marca_de_agua(logo_path, watermark_path):
        logo_wm = get_cached_image(watermark_path)
        if logo_wm:
            w, h = logo_wm.getSize()
            wm_width = 16 * cm
            wm_height = wm_width * (h / float(w))
            x = (width - wm_width) / 2
            y = (height - wm_height) / 2
            canvas.drawImage(logo_wm, x, y, width=wm_width, height=wm_height, mask='auto')

    # --- HEADER ---
    cat_actual = _PAGE_CATEGORIES.get(doc.page, "")
    draw_corporate_header(canvas, cat_actual, width, height)
    
    # --- FOOTER ---
    draw_corporate_footer(canvas, doc.page, width, height)
    
    canvas.restoreState()

def generar_indice_dinamico(cat_start_pages, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 1. WATERMARK
    logo_path = "logo_horizontal.png"
    watermark_path = "watermark_temp_v3.png"
    if crear_marca_de_agua(logo_path, watermark_path):
        logo_wm = get_cached_image(watermark_path)
        if logo_wm:
            w, h = logo_wm.getSize()
            wm_width = 16 * cm
            wm_height = wm_width * (h / float(w))
            x = (width - wm_width) / 2
            y = (height - wm_height) / 2
            c.drawImage(logo_wm, x, y, width=wm_width, height=wm_height, mask='auto')

    # 2. HEADER CORPORATIVO
    # El índice suele ser la página 2 del documento final (Portada + Índice)
    # Sin embargo, aquí lo generamos como un PDF independiente que luego se une.
    draw_corporate_header(c, "ÍNDICE", width, height)
    
    # 3. LISTA DE CATEGORÍAS
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
    espaciado = 45
    
    for idx, (cat_name, cat_order) in enumerate(orden_categorias):
        y_pos = start_y - (idx * espaciado)
        page_num = cat_start_pages.get(cat_name, "-")
        
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(COLOR_TEXT_MAIN)
        texto_cat = f"{cat_order}. {cat_name}"
        c.drawString(50, y_pos, texto_cat)
        
        c.setFont("Georgia-Bold", 28)
        c.setFillColor(COLOR_ACCENT)
        c.drawRightString(width - 50, y_pos - 4, str(page_num))
        
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.setLineWidth(0.5)
        c.line(50, y_pos - 15, width - 50, y_pos - 15)

    # 4. FOOTER CORPORATIVO (Reemplaza al footer anterior)
    # Para el índice no mostramos número de página por ahora o pasamos None
    draw_corporate_footer(c, None, width, height)

    c.save()

def generar_pdf():
    # Sincronizar imágenes automáticamente antes de empezar
    print("🔄 Sincronizando imágenes...")
    procesar_imagenes.procesar_imagenes()
    
    pathlib.Path("output").mkdir(parents=True, exist_ok=True)

    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: No se encontró el archivo {DATA_PATH}")
        return
    
    try:
        df = pd.read_excel(DATA_PATH)
        df.columns = df.columns.str.strip()
        
        # Mapeo Inteligente (Añadido SKU para el look premium)
        mapping = {}
        for col in df.columns:
            normalized = col.lower().replace('ó', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ú', 'u')
            if normalized == 'nombre': mapping[col] = 'Nombre'
            elif normalized == 'descripcion': mapping[col] = 'Descripcion'
            elif normalized == 'tallas': mapping[col] = 'Tallas'
            elif normalized == 'precio': mapping[col] = 'Precio'
            elif normalized == 'imagen': mapping[col] = 'Imagen'
            elif normalized == 'sku': mapping[col] = 'SKU'
            elif normalized == 'precios_especiales': mapping[col] = 'Precios_Especiales'
            elif normalized == 'colores': mapping[col] = 'Colores'

        
        df = df.rename(columns=mapping)
        
        # --- PROCESAMIENTO DE CATEGORÍAS (Lógica Dinámica) ---
        def asignar_categoria(sku):
            if not sku or pd.isna(sku): return "ACCESORIOS DE PROTECCIÓN VARIOS"
            prefix = str(sku).split('-')[0].upper()
            mapping_cats = {
                'CAS': 'PROTECCIÓN DE CABEZA',
                'LEN': 'PROTECCIÓN VISUAL',
                'GUA': 'PROTECCIÓN MANUAL',
                'ROP': 'PROTECCIÓN CORPORAL',
                'CHA': 'PROTECCIÓN CORPORAL',
                'ZAP': 'CALZADO DE SEGURIDAD',
                'BOT': 'CALZADO DE SEGURIDAD',
                'AU':  'PROTECCIÓN AUDITIVA',
                'RES': 'PROTECCIÓN RESPIRATORIA',
                'FAC': 'PROTECCIÓN FACIAL',
                'SEN': 'SEÑALÉTICAS',
                'ACC': 'ACCESORIOS DE PROTECCIÓN VARIOS'
            }
            return mapping_cats.get(prefix, "ACCESORIOS DE PROTECCIÓN VARIOS")

        def asignar_orden(sku):
            if not sku or pd.isna(sku): return 99
            prefix = str(sku).split('-')[0].upper()
            order_cats = {
                'ZAP': 1,
                'BOT': 2,
                'ROP': 3,
                'CHA': 4,
                'CAS': 5,
                'GUA': 6,
                'LEN': 7,
                'AU':  8,
                'RES': 9,
                'FAC': 10,
                'SEN': 11,
                'ACC': 12
            }
            return order_cats.get(prefix, 99)

        df['Categoria'] = df['SKU'].apply(asignar_categoria)
        df['Orden_Cat'] = df['SKU'].apply(asignar_orden)
        
        # Ordenamos primero por nuestro orden personalizado de categorías y luego por SKU (ej. ROP-001, ROP-002)
        df = df.sort_values(by=['Orden_Cat', 'SKU']).drop(columns=['Orden_Cat'])
        
        # Filtramos filas vacías
        df = df.dropna(subset=['Nombre'])
        df = df[df['Nombre'].astype(str).str.strip() != ""]
        
        required = ['Nombre', 'Descripcion', 'Tallas', 'Precio', 'Imagen']
        missing = [col for col in required if col not in df.columns]
        if missing:
            print(f"❌ Error: Faltan las siguientes columnas: {missing}")
            return
    except Exception as e:
        print(f"❌ Error al leer el Excel: {e}")
        return

    # Configuración del documento base
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,      # Más espacio para respirar arriba
        bottomMargin=1.5*cm, # Un poco menos de margen inferior para que el 4to producto no salte
        title="Catálogo Premium EPP"
    )

    styles = getSampleStyleSheet()
    
    # ==========================================
    # ESTILOS TIPOGRÁFICOS EDITORIALES
    # ==========================================
    style_nombre = ParagraphStyle(
        'NombreProd', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=13,
        textColor=COLOR_TEXT_MAIN, spaceAfter=6, leading=15
    )
    
    style_desc = ParagraphStyle(
        'DescProd', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5,
        textColor=COLOR_TEXT_MUTED, leading=14, spaceAfter=12 # Buen interlineado
    )
    
    style_tallas = ParagraphStyle(
        'Tallas', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5,
        textColor=COLOR_TEXT_MAIN, spaceAfter=0
    )
    
    style_precio = ParagraphStyle(
        'PrecioProd', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=15,
        textColor=COLOR_ACCENT, alignment=TA_RIGHT
    )
    
    style_precios_esp = ParagraphStyle(
        'PreciosEsp', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5,
        textColor=COLOR_TEXT_MUTED, leading=10, leftIndent=10
    )

    story = []
    
    last_category = None
    tabla_data = []
    productos_en_pagina = 0
    
    page_count = 1
    global _PAGE_CATEGORIES
    _PAGE_CATEGORIES.clear()
    
    cat_start_pages = {}
    
    for _, row in df.iterrows():
        current_cat = row.get('Categoria', 'ACCESORIOS DE PROTECCIÓN VARIOS')
        
        if current_cat not in cat_start_pages:
            # Si es la primera vez que vemos esta categoría, anotamos la página
            # Pero cuidado: si acabamos de saltar de página, el page_count ya es el correcto
            cat_start_pages[current_cat] = page_count
        
        # --- CAMBIO DE CATEGORÍA ---
        if current_cat != last_category:
            # Si hay productos en la página actual, la cerramos y forzamos salto
            if tabla_data:
                t_page = Table(tabla_data, colWidths=[18*cm])
                t_page.setStyle(TableStyle([
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(t_page)
                story.append(PageBreak())
                page_count += 1
                tabla_data = []
                productos_en_pagina = 0
                # Al saltar de página por cambio de categoría, la nueva categoría empieza aquí
                cat_start_pages[current_cat] = page_count
            
            # Espaciado extra al inicio de la página
            story.append(Spacer(1, 0.5*cm))
            
            last_category = current_cat

        if productos_en_pagina == 0:
            _PAGE_CATEGORIES[page_count] = current_cat

        # --- 1. PROCESAMIENTO IMAGEN ---
        raw_img = row.get('Imagen', '')
        
        # Manejar el caso donde Excel lee números como 1.0, 2.0, etc.
        if isinstance(raw_img, float) and raw_img.is_integer():
            img_filename = str(int(raw_img))
        else:
            img_filename = str(raw_img).strip()
        
        # Buscar archivo con cualquier extensión soportada
        EXTENSIONES_IMAGEN = ['.webp', '.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        if img_filename and img_filename.lower() != 'nan' and img_filename != "":
            if '.' not in img_filename:
                encontrado = False
                for ext in EXTENSIONES_IMAGEN:
                    candidato = os.path.join(IMG_PATH, img_filename + ext)
                    if os.path.exists(candidato):
                        img_filename += ext
                        encontrado = True
                        break
                if not encontrado:
                    img_filename += ".webp" 
        
        img_file_path = os.path.join(IMG_PATH, img_filename)
        
        # --- LIMPIAR FONDO BLANCO ---
        img_file_path = quitar_fondo_blanco(img_file_path)
        
        img_size = 5.3*cm # Ajuste fino para evitar salto de página

        if os.path.exists(img_file_path) and img_filename.lower() != 'nan' and img_filename != "":
            try:
                img_render = Image(img_file_path, width=img_size, height=img_size)
            except:
                img_render = Table([['Img Error']], colWidths=[img_size], rowHeights=[img_size], style=[('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')])
        else:
            # Marcador sutil y elegante sin imagen
            img_render = Table([['Fotografía\nNo Disponible']], colWidths=[img_size], rowHeights=[img_size], 
                               style=[('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
                                      ('TEXTCOLOR', (0,0), (-1,-1), COLOR_TEXT_MUTED),
                                      ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                                      ('VALIGN', (0,0), (-1,-1), 'MIDDLE')])

        # --- 2. TEXTOS Y JERARQUÍA ---
        # Línea divisoria muy fina y sutil bajo el título
        linea_elegante = HRFlowable(width="100%", thickness=0.5, color=COLOR_LINE, spaceBefore=0, spaceAfter=10)
        
        # --- VALIDAR DESCRIPCIÓN ---
        desc_str = str(row.get('Descripcion', '')).strip()
        if not desc_str or desc_str.lower() == 'nan':
            parrafo_desc = Spacer(1, 0)
        else:
            parrafo_desc = Paragraph(desc_str, style_desc)

        detalles = [
            Paragraph(str(row['Nombre']), style_nombre),
            linea_elegante,
            parrafo_desc,
        ]

        # --- 2.1 TABLA DE TALLAS Y PRECIO PRINCIPAL ---
        tallas_str = str(row.get('Tallas', '')).strip()
        if not tallas_str or tallas_str.lower() == 'nan':
            parrafo_tallas = Paragraph("", style_tallas)
        else:
            parrafo_tallas = Paragraph(f"<b>Tallas:</b> {tallas_str}", style_tallas)

        detalles.append(
            Table([
                [parrafo_tallas, 
                 Paragraph(f"S/ {row['Precio']:,.2f}", style_precio)]
            ], colWidths=[4.5*cm, 5*cm], style=[('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('VALIGN', (0,0), (-1,-1), 'BOTTOM')])
        )

        # --- 2.2 AGREGAR PRECIOS ESPECIALES DEBAJO SI EXISTEN ---
        precios_esp_raw = str(row.get('Precios_Especiales', '')).strip()
        if precios_esp_raw and precios_esp_raw.lower() != 'nan' and precios_esp_raw != "":
            detalles.append(Spacer(1, 4))
            detalles.append(Paragraph("<b>Variaciones de precio:</b>", style_precios_esp))
            for variacion in precios_esp_raw.split(','):
                v_str = variacion.strip()
                if ':' in v_str:
                    partes = v_str.split(':', 1)
                    etiqueta = partes[0].strip()
                    valor_crudo = partes[1].replace('S/', '').replace('s/', '').strip()
                    try:
                        precio_float = float(valor_crudo)
                        texto_final = f"• {etiqueta}: S/ {precio_float:,.2f}"
                    except ValueError:
                        texto_final = f"• {v_str}"
                else:
                    texto_final = f"• {v_str}"
                    
                detalles.append(Paragraph(texto_final, style_precios_esp))

        # --- 2.3 AGREGAR CÍRCULOS DE COLORES SI EXISTEN ---
        colores_raw = str(row.get('Colores', '')).strip()
        if colores_raw and colores_raw.lower() != 'nan' and colores_raw != "":
            # Si el valor es 'xxx', usamos la lista completa de colores solicitada
            if colores_raw.lower() == 'xxx':
                lista_colores = list(PRODUCT_COLORS.keys())
            else:
                # Si no, asumimos que es una lista separada por comas
                lista_colores = [c.strip() for c in colores_raw.split(',')]
            
            detalles.append(Spacer(1, 8))
            detalles.append(ColorCircles(lista_colores))


        # --- 3. MAQUETACIÓN DE LA TARJETA ---
        tarjeta_interna = Table([
            [img_render, detalles]
        ], colWidths=[8*cm, 10*cm])
        
        tarjeta_interna.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (0,0), 0),      # Imagen pegada a la izquierda
            ('RIGHTPADDING', (0,0), (0,0), 0.5*cm),# Espacio entre imagen y texto
            ('LEFTPADDING', (1,0), (1,0), 0.5*cm), # Espacio antes del texto
            ('RIGHTPADDING', (1,0), (1,0), 0),     # Texto pegado a la derecha
            # Borde sutil inferior para separar productos en lugar de cajas cerradas
            ('LINEBELOW', (0,0), (-1,-1), 0.5, COLOR_LINE),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0.35*cm),
            ('TOPPADDING', (0,0), (-1,-1), 0.35*cm),
        ]))

        tabla_data.append([tarjeta_interna])
        productos_en_pagina += 1

        # --- CIERRE DE PÁGINA (Si llegamos a 4 productos) ---
        if productos_en_pagina == 4:
            t_page = Table(tabla_data, colWidths=[18*cm])
            t_page.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(t_page)
            story.append(PageBreak())
            page_count += 1
            tabla_data = []
            productos_en_pagina = 0

    # Cerrar cualquier tabla sobrante al final del documento
    if tabla_data:
        t_page = Table(tabla_data, colWidths=[18*cm])
        t_page.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_page)
        # No ponemos PageBreak al final para no dejar hojas en blanco

    print(f"DEBUG PAGE CATEGORIES: {_PAGE_CATEGORIES}")
    print(f"🔨 Generando PDF Premium...")
    # Pasamos la función header_footer para que se dibuje en cada página
    doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    
    # ==========================================
    # UNIR PORTADA, ÍNDICE, CATÁLOGO Y CONTRAPORTADA
    # ==========================================
    portada_path = "templates/PORTADA.pdf"
    indice_path = "templates/INDICE.pdf"
    contra_path = "templates/CONTRAPORTADA.pdf"
    
    if any(os.path.exists(p) for p in [portada_path, indice_path, contra_path]):
        print(f"📖 Generando Índice Dinámico y uniendo PDFs...")
        try:
            generar_indice_dinamico(cat_start_pages, indice_path)
            
            doc_final = fitz.open()
            
            # 1. Insertar Portada
            num_portada = 0
            if os.path.exists(portada_path):
                doc_p = fitz.open(portada_path)
                num_portada = len(doc_p)
                doc_final.insert_pdf(doc_p)
                doc_p.close()
            
            # 2. Insertar Índice
            num_indice = 0
            if os.path.exists(indice_path):
                doc_i = fitz.open(indice_path)
                num_indice = len(doc_i)
                doc_final.insert_pdf(doc_i)
                doc_i.close()
            
            # 3. Insertar Catálogo generado
            doc_c = fitz.open(OUTPUT_PATH)
            doc_final.insert_pdf(doc_c)
            doc_c.close()
            
            # 4. Insertar Contraportada
            if os.path.exists(contra_path):
                doc_cp = fitz.open(contra_path)
                doc_final.insert_pdf(doc_cp)
                doc_cp.close()

            # --- AÑADIR ENLACES AL ÍNDICE (EN EL DOC FINAL) ---
            if num_indice > 0:
                print(f"🔗 Creando enlaces interactivos en el índice...")
                print(f"DEBUG: Categorías encontradas y sus páginas iniciales: {cat_start_pages}")
                # El índice comienza después de la portada
                # Offset para el catálogo: portada + índice
                catalog_offset = num_portada + num_indice
                
                for cat_name, cat_page in cat_start_pages.items():
                    encontrado = False
                    # Buscamos en cada página del índice (usualmente solo 1)
                    for idx in range(num_portada, num_portada + num_indice):
                        page_i = doc_final[idx]
                        
                        # Lista de términos de búsqueda simplificados para mayor robustez
                        # (Buscamos la palabra clave principal de cada categoría)
                        search_term = ""
                        if "ZAP" in cat_name or "CALZADO" in cat_name: search_term = "CALZADO"
                        elif "CORPO" in cat_name or "ROPA" in cat_name: search_term = "CORPORAL"
                        elif "CABEZA" in cat_name or "CASCO" in cat_name: search_term = "CABEZA"
                        elif "MANUAL" in cat_name or "GUANTE" in cat_name: search_term = "MANUAL"
                        elif "VISUAL" in cat_name or "LENT" in cat_name: search_term = "VISUAL"
                        elif "AUDI" in cat_name: search_term = "AUDITIVA"
                        elif "RESPIRATORIA" in cat_name or "RES" in cat_name: search_term = "RESPIRATORIA"
                        elif "FACIAL" in cat_name or "FAC" in cat_name: search_term = "FACIAL"
                        elif "SEÑAL" in cat_name or "SEN" in cat_name: search_term = "SEÑAL"
                        elif "ACCESORIOS" in cat_name: search_term = "ACCESORIOS"
                        
                        if search_term:
                            text_instances = page_i.search_for(search_term)
                            if text_instances:
                                for rect in text_instances:
                                    # Expandir el área clicable a lo ancho de la página para facilitar el clic
                                    # rect es (x0, y0, x1, y1). Lo extendemos en el eje X.
                                    click_rect = fitz.Rect(50, rect.y0 - 2, 550, rect.y1 + 2) 
                                    
                                    # Destino: catalog_offset + pagina_cat (1-based) - 1
                                    target_page = catalog_offset + cat_page - 1
                                    print(f"  ✅ Link creado: '{cat_name}' -> Pág {target_page + 1}")
                                    
                                    page_i.insert_link({
                                        'kind': fitz.LINK_GOTO,
                                        'page': target_page,
                                        'from': click_rect
                                        # 'border': {'width': 0.5, 'color': (0.8, 0, 0)} # Borde eliminado tras verificación
                                    })
                                encontrado = True
                                break 
                    
                    if not encontrado:
                        print(f"  ⚠️ No se encontró la ubicación de '{cat_name}' en el índice PDF.")

                # --- AÑADIR ENLACES EN LOS LOGOS (VOLVER AL ÍNDICE) ---
                print(f"🏠 Añadiendo enlaces 'Volver al Índice' en los logos de cada página...")
                # El logo está en el header de todas las páginas del catálogo (desde catalog_offset en adelante)
                # Coordenadas calculadas para coincidir con el logo en el header
                # x: 1.5cm, y_top: 0.5cm, x_right: 6.5cm, y_bottom: 1.9cm
                pts = 28.3465 # puntos por cm
                logo_rect = fitz.Rect(1.4 * pts, 0.4 * pts, 6.5 * pts, 2.0 * pts)
                
                for idx in range(catalog_offset, doc_final.page_count):
                    # Omitimos la contraportada si existe (asumiendo que es la última página)
                    if os.path.exists(contra_path) and idx == doc_final.page_count - 1:
                        continue
                        
                    page = doc_final[idx]
                    page.insert_link({
                        'kind': fitz.LINK_GOTO,
                        'page': num_portada, # El índice está después de la portada (pág num_portada)
                        'from': logo_rect
                    })
            
            # Guardar el resultado final sobreescribiendo el temporal
            doc_final.save(OUTPUT_PATH, garbage=4, deflate=True)
            doc_final.close()

            # ==========================================
            # ENRIQUECER EL PDF FINAL (ENLACES GLOBALES)
            # ==========================================
            enriquecer_pdf_final(OUTPUT_PATH)

            print(f"✨ ¡Catálogo completo con Portada y Contraportada en: {OUTPUT_PATH}!")
        except Exception as e:
            print(f"⚠️ Error al unir PDFs: {e}")
            print(f"✨ El catálogo se guardó sin uniones en: {OUTPUT_PATH}")
    else:
        # También enriquecer si no hubo uniones (por si acaso)
        enriquecer_pdf_final(OUTPUT_PATH)
        print(f"✨ ¡Catálogo Premium creado con éxito en: {OUTPUT_PATH}!")

def enriquecer_pdf_final(pdf_path):
    """
    Escanea todo el PDF en busca de textos de contacto y añade enlaces si faltan.
    Esto es útil para la Portada y Contraportada que son PDFs estáticos.
    """
    if not os.path.exists(pdf_path):
        return
        
    print(f"🔎 Escaneando PDF para activar enlaces globales...")
    try:
        doc = fitz.open(pdf_path)
        enlaces_añadidos = 0
        
        email_text = "ventas@prosegin.com"
        phone_text = "989 983 227"
        address_text = "AV. GUILLERMO DANSEY NRO. 354"
        
        whatsapp_url = "https://wa.me/51989983227?text=Hola%2C%20quiero%20cotizar%21"
        gmaps_url = "https://maps.app.goo.gl/KQthqjJ5AKSJXRWWA"
        
        for page in doc:
            # Solo añadir si no hay muchos links ya (evita duplicar en páginas del catálogo)
            # Pero para ser más seguros, buscamos instancias y verificamos colisión.
            
            # Buscar Correo
            for inst in page.search_for(email_text):
                # Si no hay un link en esta posición, lo añadimos
                if not any(inst.intersects(l['from']) for l in page.get_links()):
                    page.insert_link({'kind': fitz.LINK_GOTO, 'uri': f"mailto:{email_text}", 'from': inst, 'kind': fitz.LINK_URI})
                    enlaces_añadidos += 1
            
            # Buscar Teléfono
            for inst in page.search_for(phone_text):
                if not any(inst.intersects(l['from']) for l in page.get_links()):
                    page.insert_link({'kind': fitz.LINK_GOTO, 'uri': whatsapp_url, 'from': inst, 'kind': fitz.LINK_URI})
                    enlaces_añadidos += 1
                    
            # Buscar Dirección (parcial para ser más flexible)
            for inst in page.search_for(address_text):
                if not any(inst.intersects(l['from']) for l in page.get_links()):
                    # Expandir un poco el área de la dirección
                    page.insert_link({'kind': fitz.LINK_GOTO, 'uri': gmaps_url, 'from': inst, 'kind': fitz.LINK_URI})
                    enlaces_añadidos += 1
        
        if enlaces_añadidos > 0:
            doc.saveIncr() # Guardar cambios de forma incremental
            print(f"  ✅ Se activaron {enlaces_añadidos} enlaces adicionales en páginas estáticas.")
        doc.close()
    except Exception as e:
        print(f"  ⚠️ No se pudo enriquecer el PDF: {e}")

if __name__ == "__main__":
    generar_pdf()
