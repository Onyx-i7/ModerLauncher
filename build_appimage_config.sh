#!/bin/bash

# Configuración
APP_NAME="ModerLauncher"
APP_DIR="AppDir"
ICON_SOURCE="$APP_DIR/usr/share/icons/hicolor/256x256/apps/moderlauncher.png"
DESKTOP_SOURCE="$APP_DIR/usr/share/applications/moderlauncher.desktop"

# Asegurar que los archivos estén en la raíz de AppDir
if [ -f "$DESKTOP_SOURCE" ]; then
    ln -sf "usr/share/applications/moderlauncher.desktop" "$APP_DIR/moderlauncher.desktop"
else
    echo "Error: No se encontró el archivo .desktop en $DESKTOP_SOURCE"
    exit 1
fi

if [ -f "$ICON_SOURCE" ]; then
    ln -sf "usr/share/icons/hicolor/256x256/apps/moderlauncher.png" "$APP_DIR/moderlauncher.png"
else
    #
    echo "Icono no encontrado en usr/share, usando favicon.png como fallback."
    cp favicon.png "$APP_DIR/moderlauncher.png"
fi

# Verificar AppRun
if [ ! -f "$APP_DIR/AppRun" ]; then
    echo "❌ Error: Falta el archivo AppRun en $APP_DIR"
    exit 1
fi
chmod +x "$APP_DIR/AppRun"

# Ejecutar appimagetool
echo "Ejecutando appimagetool..."
appimagetool "$APP_DIR"

echo "Proceso terminado"
