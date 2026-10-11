import os

def exportar_proyecto(archivo_salida="todo_el_proyecto.txt", extensiones=None, ignorar_carpetas=None):
    """
    Exporta todos los archivos del proyecto a un único archivo de texto.
    
    Args:
        archivo_salida: Nombre del archivo de salida
        extensiones: Tupla de extensiones a incluir. Si es None, incluye todos los archivos.
        ignorar_carpetas: Lista de nombres de carpetas a ignorar
    """
    
    # Carpetas a ignorar por defecto
    if ignorar_carpetas is None:
        ignorar_carpetas = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            ".pytest_cache",
            ".godot",
            ".import",
            "node_modules",
            ".mypy_cache",
            "build",
            "dist",
            "*.egg-info"
        }
    
    # Archivos a ignorar
    archivos_ignorados = {
        archivo_salida,
        "todo_el_proyecto.txt",
        ".DS_Store",
        "Thumbs.db"
    }
    
    # Extensiones binarias que no se pueden leer como texto
    extensiones_binarias = {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
        ".mp3", ".wav", ".ogg", ".mp4", ".avi", ".mov",
        ".exe", ".dll", ".so", ".dylib",
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".pyc", ".pyo", ".class", ".o", ".obj",
        ".db", ".sqlite",
        ".tres", ".import"  # Archivos de Godot generados
    }
    
    archivos_procesados = 0
    archivos_omitidos = 0
    
    with open(archivo_salida, "w", encoding="utf-8") as outfile:
        outfile.write("EXPORTACIÓN COMPLETA DEL PROYECTO\n")
        outfile.write("=" * 80 + "\n\n")
        
        for root, dirs, files in os.walk("."):
            # Ignorar carpetas especificadas
            dirs[:] = [d for d in dirs if d not in ignorar_carpetas and not d.endswith(".egg-info")]
            
            for file in files:
                # Ignorar archivos específicos
                if file in archivos_ignorados:
                    continue
                
                # Verificar extensión si se especificó
                if extensiones is not None and not file.endswith(extensiones):
                    continue
                
                # Ignorar archivos binarios
                _, ext = os.path.splitext(file)
                if ext.lower() in extensiones_binarias:
                    archivos_omitidos += 1
                    continue
                
                path_completo = os.path.join(root, file)
                
                try:
                    # Intentar leer como texto
                    with open(path_completo, "r", encoding="utf-8") as infile:
                        contenido = infile.read()
                    
                    # Escribir en el archivo de salida
                    outfile.write(f"\n{'=' * 80}\n")
                    outfile.write(f"ARCHIVO: {path_completo}\n")
                    outfile.write(f"{'=' * 80}\n\n")
                    outfile.write(contenido)
                    outfile.write("\n")
                    
                    archivos_procesados += 1
                    
                except UnicodeDecodeError:
                    # Archivo binario o con codificación diferente
                    outfile.write(f"\n{'=' * 80}\n")
                    outfile.write(f"ARCHIVO: {path_completo}\n")
                    outfile.write(f"{'=' * 80}\n\n")
                    outfile.write("[ARCHIVO BINARIO O CON CODIFICACIÓN NO COMPATIBLE - OMITIDO]\n")
                    archivos_omitidos += 1
                    
                except Exception as e:
                    outfile.write(f"\n{'=' * 80}\n")
                    outfile.write(f"ARCHIVO: {path_completo}\n")
                    outfile.write(f"{'=' * 80}\n\n")
                    outfile.write(f"[ERROR AL LEER ARCHIVO: {e}]\n")
                    archivos_omitidos += 1
    
    print(f"✅ Exportación completada: {archivo_salida}")
    print(f"📄 Archivos procesados: {archivos_procesados}")
    print(f"⚠️  Archivos omitidos: {archivos_omitidos}")

if __name__ == "__main__":
    # Exportar TODOS los archivos de texto
    exportar_proyecto()
    
    # Si solo quieres archivos específicos, descomenta esta línea:
    #exportar_proyecto(extensiones=(".py", ".gd", ".tscn", ".tres", ".md", ".json", ".txt"))
