import os
from rembg import remove
from PIL import Image

# Carpeta base
FOLDER = "imagenes_originales"

# Archivos a procesar
archivos_a_limpiar = ["302.jpg", "57.png", "338.png"]

for archivo in archivos_a_limpiar:
    ruta_input = os.path.join(FOLDER, archivo)
    
    if not os.path.exists(ruta_input):
        print(f"⚠️ No se encontró: {ruta_input}")
        continue
        
    print(f"🤖 IA analizando y removiendo fondo de: {archivo}...")
    try:
        # Abrir imagen original
        with Image.open(ruta_input) as img:
            # Convertir a formato soportado por rembg (RGBA) si no lo está
            img = img.convert("RGBA")
            
            # Remover fondo usando la IA
            img_sin_fondo = remove(img)
            
            # Guardar el resultado (forzamos PNG para preservar la transparencia)
            nombre_base = os.path.splitext(archivo)[0]
            ruta_output = os.path.join(FOLDER, nombre_base + ".png")
            
            img_sin_fondo.save(ruta_output, "PNG")
            print(f"✅ Fondo removido con éxito: {ruta_output}")
            
        # Si el archivo original no era PNG, lo eliminamos para evitar duplicados
        if archivo.lower() != nombre_base.lower() + ".png":
            os.remove(ruta_input)
            print(f"🗑️ Archivo original eliminado: {archivo}")
            
    except Exception as e:
        print(f"❌ Error procesando {archivo}: {e}")

print("✨ Proceso de limpieza con IA terminado.")
