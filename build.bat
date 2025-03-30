@echo off
setlocal

:: Limpiar pantalla
cls

:: Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python no esta instalado o no esta en el PATH
    echo Por favor, instale Python desde https://www.python.org/downloads/
    echo Asegurese de marcar la opcion "Add Python to PATH" durante la instalacion
    pause
    exit /b 1
)

:: Verificar/Instalar pip
python -m ensurepip --upgrade
python -m pip install --upgrade pip

:: Instalar dependencias usando python -m pip para asegurar la ruta correcta
echo Instalando dependencias...
python -m pip install --upgrade pyinstaller
echo.

:: Rutas principales
set PROJECT_DIR=%~dp0
set DIST_DIR=%PROJECT_DIR%dist
set BUILD_DIR=%PROJECT_DIR%build

:: Limpiar compilaciones anteriores
echo Limpiando directorios anteriores...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
echo.

:: Compilar usando el archivo .spec
echo Creando ejecutable...
python -m PyInstaller --clean --distpath "%DIST_DIR%" ModerLauncher.spec
python -m PyInstaller --clean --distpath "%DIST_DIR%" moder.spec


if errorlevel 1 (
    echo Error en la compilacion!
    echo Verifique que todas las dependencias esten instaladas correctamente
    pause
    exit /b 1
)

echo.
echo Compilacion exitosa!
echo El ejecutable esta en: %DIST_DIR%\ModerLauncher\ModerLauncher.exe
pause