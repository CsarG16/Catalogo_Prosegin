import os
from PIL import Image, ImageOps
import pathlib

# Configuración
FOLDER_ORIGINAL = "imagenes_originales"
FOLDER_PROCESADA = "imagenes_procesadas"
TARGET_SIZE = (600, 600)
WEBP_QUALITY = 80  # 80 = excelente balance calidad/peso (40-60% menos que JPEG q90)
BG_COLOR = (255, 255, 255)

def inicializar_carpetas():
    """Asegura que existan los directorios necesarios."""
    pathlib.Path(FOLDER_PROCESADA).mkdir(parents=True, exist_ok=True)
    pathlib.Path(FOLDER_ORIGINAL).mkdir(parents=True, exist_ok=True)

def procesar_imagenes():
    inicializar_carpetas()
    
    if not os.path.exists(FOLDER_ORIGINAL):
        print(f"❌ Error: La carpeta '{FOLDER_ORIGINAL}' no existe.")
        return

    archivos = [f for f in os.listdir(FOLDER_ORIGINAL) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if not archivos:
        print(f"ℹ️ No se encontraron imágenes en '{FOLDER_ORIGINAL}'.")
        return

    print(f"🚀 Iniciando procesamiento de {len(archivos)} imágenes...")

    for nombre_archivo in archivos:
        ruta_input = os.path.join(FOLDER_ORIGINAL, nombre_archivo)
        # Siempre guardar como .webp sin importar la extensión original
        nombre_salida = os.path.splitext(nombre_archivo)[0] + ".webp"
        ruta_output = os.path.join(FOLDER_PROCESADA, nombre_salida)

        # OPTIMIZACIÓN: Solo procesar si la original es más nueva que la procesada
        if os.path.exists(ruta_output):
            if os.path.getmtime(ruta_input) <= os.path.getmtime(ruta_output):
                continue

        try:
            with Image.open(ruta_input) as img:
                # Arreglo para el fondo negro: Si la imagen tiene transparencia,
                # primero la pegamos sobre un fondo blanco puro.
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert("RGBA")
                    fondo_blanco = Image.new("RGBA", img.size, "WHITE")
                    fondo_blanco.paste(img, (0, 0), img)
                    img = fondo_blanco.convert("RGB")
                else:
                    img = img.convert("RGB")

                # Crear padding para que sea cuadrada manteniendo el ratio
                img_procesada = ImageOps.pad(img, TARGET_SIZE, color=BG_COLOR, centering=(0.5, 0.5))
                
                # Garantizar redimensión exacta con alta calidad
                img_procesada = img_procesada.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

                # Guardar como WebP optimizado (40-60% más liviano que JPEG q90)
                img_procesada.save(ruta_output, "WEBP", quality=WEBP_QUALITY, method=6)
                print(f"✅ Procesada: {nombre_archivo} → {nombre_salida}")

        except Exception as e:
            print(f"⚠️ Error procesando '{nombre_archivo}': {e}")

if __name__ == "__main__":
    procesar_imagenes()
