import os
import sys

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path.replace('/', os.sep))

def verify_gif_path(gif_path):
    """Verifica si el archivo GIF existe"""
    if not os.path.exists(gif_path):
        print(f"Error: No se encontró el archivo {gif_path}")
        return False
    return True
