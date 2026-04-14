"""
Resource Manager - Gestiona las rutas de recursos del launcher
"""
import os
import sys


def resource_path(relative_path):
    """Obtiene la ruta absoluta de un recurso"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def is_windows():
    """Determina si el sistema operativo actual es Windows."""
    return os.name == 'nt'


def get_local_data_dir(app_name='moderlauncher'):
    """Obtiene el directorio de datos del usuario según la plataforma."""
    if is_windows():
        base = os.getenv('APPDATA') or os.getenv('LOCALAPPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
    else:
        base = os.getenv('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')
    return os.path.join(base, app_name)


def get_minecraft_dir():
    """Obtiene el directorio de Minecraft según la plataforma."""
    if is_windows():
        base = os.getenv('APPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
        return os.path.join(base, '.minecraft')
    return os.path.join(os.path.expanduser('~'), '.minecraft')
