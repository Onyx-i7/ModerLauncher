# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Función para obtener rutas de recursos
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# Archivos de datos a incluir
datas = [
    ('assets', 'assets'),
    ('sounds', 'sounds'),
    ('css', 'css'),
    ('ui', 'ui'),
    ('core', 'core'),
    ('managers', 'managers'),
    ('utils', 'utils'),
    ('main.py', '.'),  # Incluir main.py como archivo de datos
    ('favicon.ico', '.'),
    ('favicon.png', '.'),
    ('tailwind.config.js', '.'),
    ('google6e21c377546f1291.html', '.'),
    ('LICENSE', '.'),
    ('README.md', '.'),
]

# Binarios ocultos (librerías del sistema que podrían necesitarse)
hiddenimports = [
    'minecraft_launcher_lib',
    'PIL',
    'PIL.Image',
    'pygame',
    'pygame.mixer',
    'cryptography',
    'cryptography.fernet',
    'requests',
    'certifi',
    'uuid',
    'json',
    'subprocess',
    'webbrowser',
    'threading',
    'queue',
    'time',
    'datetime',
    'shutil',
    'tempfile',
    'zipfile',
    'tkinter',
    'tkinter.ttk',
    'psutil',
    'PyQt5',
    'PyQt5.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
]

a = Analysis(
    ['1.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ModerLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo/icon.ico',
)