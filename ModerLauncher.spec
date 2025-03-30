# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Usar ruta Windows específica
BASEDIR = 'C:\\Users\\jephersonRD\\Documents\\moderlauncher'

a = Analysis(
    ['main.py'],
    pathex=[BASEDIR],
    binaries=[],
    datas=[
        # Usar rutas relativas para los archivos redes
        ('assets\\redes\\*', 'assets\\redes'),

        # Resto de assets
        ('assets\\bye\\*', 'assets\\bye'),
        ('assets\\fondo\\*', 'assets\\fondo'),
        ('assets\\icon\\*', 'assets\\icon'),
        ('assets\\logo\\*', 'assets\\logo'),
        ('sonidos\\*', 'sonidos'),
        ('*.py', '.')
    ],
    hiddenimports=[
        'tkinter', 'PIL', 'PIL._imagingtk', 'PIL._tkinter_finder',
        'minecraft_launcher_lib', 'pygame', 'pygame.mixer',
        'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
        'auth_manager', 'game_window', 'profile_window', 'settings_window',
        'download_progress', 'bye', 'java_manager', 'Java_Downloader',
        'java_error_window', 'javaMensaje',
        'mensajeDoloand', 'mods_window'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ModerLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASEDIR, 'assets\\icon\\logo.ico')
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ModerLauncher'
)
