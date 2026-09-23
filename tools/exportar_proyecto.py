import os

def exportar_proyecto(archivo_salida="todo_el_proyecto.txt", extensiones=(".py",)):
    with open(archivo_salida, "w", encoding="utf-8") as outfile:
        for root, dirs, files in os.walk("."):
            # Ignorar carpetas que no queremos procesar
            if ".git" in dirs: dirs.remove(".git")
            if "__pycache__" in dirs: dirs.remove("__pycache__")
            if ".venv" in dirs: dirs.remove(".venv")
            
            for file in files:
                if file.endswith(extensiones):
                    path_completo = os.path.join(root, file)
                    outfile.write(f"\n{'='*20}\nARCHIVO: {path_completo}\n{'='*20}\n\n")
                    with open(path_completo, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                        outfile.write("\n")

if __name__ == "__main__":
    exportar_proyecto()
    print("Exportación completada: todo_el_proyecto.txt")

