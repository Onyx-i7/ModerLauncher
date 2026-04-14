#!/bin/sh
set -e

APP_NAME="ModerLauncher"
APPDIR="$(pwd)/AppDir"
INSTALL_DIR="$APPDIR/usr/share/moderlauncher"
ICON_SRC="assets/logo/logo.png"
ICON_DST="$APPDIR/usr/share/icons/hicolor/256x256/apps/moderlauncher.png"

command -v python3 >/dev/null 2>&1 || {
echo "ERROR: python3 no está instalado en el host." >&2
exit 1
}

command -v appimagetool >/dev/null 2>&1 || {
echo "ERROR: appimagetool no está instalado." >&2
echo "Instala appimagetool." >&2
exit 1
}

rm -rf "$APPDIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copiar archivos
cp -r 1.py main.py assets core css favicon.ico favicon.png google6e21c377546f1291.html managers sounds tailwind.config.js ui utils LICENSE README.md "$INSTALL_DIR/"

# Icono
if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$ICON_DST"
fi

# AppRun
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
APP_SHARE="$HERE/usr/share/moderlauncher"
export PYTHONPATH="$APP_SHARE:$PYTHONPATH"
exec /usr/bin/env python3 "$APP_SHARE/main.py" "$@"
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

# --- ESTO ES LO QUE FALTABA ---
# Copiar el .desktop y el icono a la RAÍZ de AppDir para que appimagetool los vea
cp "$APPDIR/usr/share/applications/moderlauncher.desktop" "$APPDIR/"
cp "$ICON_DST" "$APPDIR/moderlauncher.png"
# ------------------------------

# Ejecutable de lanzamiento
cat > "$APPDIR/usr/bin/ModerLauncher" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
exec /usr/bin/env python3 "$HERE/../share/moderlauncher/main.py" "$@"
EOF
chmod +x "$APPDIR/usr/bin/ModerLauncher"

# Crear AppImage
ARCH=x86_64 appimagetool "$APPDIR" "${APP_NAME}.AppImage"

echo "AppImage creada: ${APP_NAME}.AppImage"
