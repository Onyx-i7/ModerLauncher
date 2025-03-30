import os
import sys
import requests
import subprocess
from tkinter import messagebox
import tempfile
import shutil
import tkinter as tk
from tkinter import ttk

class DownloadProgressWindow:
    def __init__(self, parent, title, version):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("300x150")
        self.window.configure(bg="#161616")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Centrar ventana
        self.window.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()/2 - 150,
            parent.winfo_rooty() + parent.winfo_height()/2 - 75))

        # Marco principal
        main_frame = tk.Frame(self.window, bg="#161616")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Mensaje
        self.message = tk.Label(
            main_frame,
            text=f"Descargando Java {version}...",
            font=("Segoe UI", 10),
            fg="white",
            bg="#161616"
        )
        self.message.pack(pady=(0, 10))

        # Barra de progreso
        self.progress = ttk.Progressbar(
            main_frame,
            orient="horizontal",
            length=260,
            mode="determinate"
        )
        self.progress.pack(pady=(0, 10))

        # Texto de porcentaje
        self.percent_label = tk.Label(
            main_frame,
            text="0%",
            font=("Segoe UI", 9),
            fg="white",
            bg="#161616"
        )
        self.percent_label.pack()

    def update_progress(self, current, total):
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress["value"] = percentage
            self.percent_label["text"] = f"{percentage}%"
            size_mb = total / 1048576  # Convertir a MB
            self.message["text"] = f"Descargando Java... {percentage}% ({size_mb:.1f} MB)"
        self.window.update()

    def close(self):
        self.window.grab_release()
        self.window.destroy()

class JavaDownloader:
    def __init__(self):
        self.java_urls = {
            "8": {
                "windows": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u382-b05/OpenJDK8U-jre_x64_windows_hotspot_8u382b05.zip",
                "install_dir": "jre1.8.0_382"
            },
            "17": {
                "windows": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.8%2B7/OpenJDK17U-jre_x64_windows_hotspot_17.0.8_7.zip",
                "install_dir": "jdk-17.0.8+7-jre"
            }
        }
        self.base_path = os.path.join(os.getenv('APPDATA'), '.minecraft', 'runtime', 'java-runtime')

    def download_and_install(self, java_version, callback, parent_window=None):
        try:
            # Crear directorio base si no existe
            version_path = os.path.join(self.base_path, f'java-{java_version}')
            os.makedirs(version_path, exist_ok=True)

            # Verificar si Java ya está instalado
            java_path = os.path.join(version_path, self.java_urls[java_version]["install_dir"], "bin", "java.exe")
            if os.path.exists(java_path):
                print(f"Java {java_version} ya está instalado")
                callback(True, java_path)
                return

            # Crear ventana de progreso usando la ventana padre proporcionada
            progress_window = DownloadProgressWindow(parent_window or tk.Tk(), "Instalando Java", java_version)

            # Descargar Java
            url = self.java_urls[java_version]["windows"]
            print(f"Descargando Java {java_version} desde {url}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Obtener tamaño total
            total_size = int(response.headers.get('content-length', 0))
            
            # Guardar en archivo temporal
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, f"java{java_version}.zip")
            
            block_size = 8192
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        downloaded += len(chunk)
                        f.write(chunk)
                        progress_window.update_progress(downloaded, total_size)

            progress_window.message["text"] = "Instalando Java..."
            progress_window.update_progress(100, 100)

            # Extraer archivos
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(version_path)

            # Verificar instalación
            if os.path.exists(java_path):
                print(f"Java {java_version} instalado correctamente")
                progress_window.close()
                callback(True, java_path)
            else:
                raise Exception(f"No se pudo encontrar java.exe después de la instalación")

        except Exception as e:
            print(f"Error instalando Java {java_version}: {e}")
            if 'progress_window' in locals():
                progress_window.close()
            callback(False, None)
        finally:
            # Limpiar archivos temporales
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def get_java_path(self, java_version):
        """Obtiene la ruta de Java si está instalado"""
        version_path = os.path.join(self.base_path, f'java-{java_version}')
        java_path = os.path.join(version_path, self.java_urls[java_version]["install_dir"], "bin", "java.exe")
        return java_path if os.path.exists(java_path) else None
