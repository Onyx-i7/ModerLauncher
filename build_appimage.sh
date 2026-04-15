#!/bin/sh
set -e

APP_NAME="ModerLauncher"
APPDIR="$(pwd)/AppDir"
DIST_DIR="$(pwd)/dist"
BUILD_DIR="$(pwd)/build"
INSTALL_DIR="$APPDIR/usr/bin"
ICON_SRC="assets/logo/logo.png"
ICON_DST="$APPDIR/usr/share/icons/hicolor/256x256/apps/moderlauncher.png"

# Verificar dependencias
command -v python3 >/dev/null 2>&1 || {
    echo "ERROR: python3 no está instalado en el host." >&2
    exit 1
}

command -v pyinstaller >/dev/null 2>&1 || {
    echo "ERROR: pyinstaller no está instalado. Instala con: pip install pyinstaller" >&2
    exit 1
}

command -v appimagetool >/dev/null 2>&1 || {
    echo "ERROR: appimagetool no está instalado." >&2
    echo "Instala appimagetool desde https://github.com/AppImage/AppImageKit" >&2
    exit 1
}

# Limpiar directorios anteriores
rm -rf "$APPDIR" "$DIST_DIR" "$BUILD_DIR"

# Crear bundle con PyInstaller
echo "Creando bundle con PyInstaller..."
pyinstaller --clean --noconfirm moderlauncher.spec

# Verificar que se creó el ejecutable
if [ ! -f "$DIST_DIR/ModerLauncher" ]; then
    echo "ERROR: PyInstaller no creó el ejecutable ModerLauncher" >&2
    exit 1
fi

echo "Bundle creado exitosamente."

# Crear estructura AppDir
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copiar el ejecutable empaquetado
cp "$DIST_DIR/ModerLauncher" "$INSTALL_DIR/"

# Copiar icono
if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$ICON_DST"
fi

# AppRun - ejecuta el bundle empaquetado
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
EXECUTABLE="$HERE/usr/bin/ModerLauncher"
exec "$EXECUTABLE" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Desktop entry
cat > "$APPDIR/usr/share/applications/moderlauncher.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=ModerLauncher
Exec=ModerLauncher
Icon=moderlauncher
Categories=Game;Utility;
Terminal=false
EOF

# Copiar el .desktop y el icono a la raíz de AppDir para que appimagetool los encuentre
cp "$APPDIR/usr/share/applications/moderlauncher.desktop" "$APPDIR/"
cp "$ICON_DST" "$APPDIR/moderlauncher.png"

# Si existe el AppImage, eliminarlo para evitar errores al crear uno nuevo
if [ -f "${APP_NAME}.AppImage" ]; then
    rm -f "${APP_NAME}.AppImage"
fi

# Crear AppImage
ARCH=x86_64 appimagetool "$APPDIR" "${APP_NAME}.AppImage"

# Dar permisos de ejecución al AppImage
chmod +x "${APP_NAME}.AppImage"

echo "AppImage creada: ${APP_NAME}.AppImage"
