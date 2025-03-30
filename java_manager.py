import os
import winreg
import subprocess
import webbrowser
import json
import tkinter as tk
from tkinter import messagebox

class JavaManager:
    def __init__(self):
        self.java_paths = {
            "Java 8 (Minecraft 1.1 - 1.16.5)": None,
            "Java 17 (Minecraft 1.17 - 1.20.4)": None
        }
        self.load_settings()
        
    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    if 'java_versions' in settings:
                        self.java_paths.update(settings['java_versions'])
        except Exception as e:
            print(f"Error cargando settings.json: {e}")

    def save_settings(self):
        try:
            settings = {}
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
            
            settings['java_versions'] = self.java_paths
            
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error guardando settings.json: {e}")

    def find_java_installations(self):
        java_paths = []
        
        # Buscar en el registro de Windows
        try:
            # Buscar Java 8
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Runtime Environment")
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    version_name = winreg.EnumKey(key, i)
                    version_key = winreg.OpenKey(key, version_name)
                    java_home = winreg.QueryValueEx(version_key, "JavaHome")[0]
                    java_exe = os.path.join(java_home, "bin", "java.exe")
                    if os.path.exists(java_exe):
                        java_paths.append((version_name, java_exe))
                except:
                    continue
        except:
            pass

        try:
            # Buscar Java 17
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JDK")
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    version_name = winreg.EnumKey(key, i)
                    version_key = winreg.OpenKey(key, version_name)
                    java_home = winreg.QueryValueEx(version_key, "JavaHome")[0]
                    java_exe = os.path.join(java_home, "bin", "java.exe")
                    if os.path.exists(java_exe):
                        java_paths.append((version_name, java_exe))
                except:
                    continue
        except:
            pass

        # Buscar en Program Files
        program_files = [os.environ.get("ProgramFiles", "C:/Program Files"),
                        os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")]
        
        for pf in program_files:
            java_dirs = [d for d in os.listdir(pf) if "java" in d.lower() or "jdk" in d.lower()]
            for jd in java_dirs:
                java_exe = os.path.join(pf, jd, "bin", "java.exe")
                if os.path.exists(java_exe):
                    version = self.get_java_version(java_exe)
                    if version:
                        java_paths.append((version, java_exe))

        return java_paths

    def get_java_version(self, java_path):
        try:
            result = subprocess.run([java_path, "-version"], 
                                 capture_output=True, 
                                 text=True, 
                                 stderr=subprocess.STDOUT)
            if "version" in result.stdout:
                version = result.stdout.split('"')[1]
                return version
        except:
            pass
        return None

    def suggest_java_download(self, required_java):
        download_urls = {
            "Java 8": "https://www.java.com/es/download/",
            "Java 17": "https://www.oracle.com/java/technologies/downloads/#java17"
        }
        
        response = messagebox.askyesno(
            "Java no encontrado",
            f"No se encontró {required_java}. ¿Desea descargarlo ahora?"
        )
        
        if response:
            version = "Java 8" if "8" in required_java else "Java 17"
            webbrowser.open(download_urls[version])
            
            # Mostrar instrucciones
            messagebox.showinfo(
                "Instrucciones",
                "1. Descarga e instala Java\n" +
                "2. Una vez instalado, cierra esta ventana\n" +
                "3. El launcher buscará automáticamente la nueva instalación"
            )
            
            # Buscar nuevamente las instalaciones de Java
            java_paths = self.find_java_installations()
            self.update_java_paths(java_paths)
            self.save_settings()
            
            return True
        return False

    def update_java_paths(self, java_paths):
        for version, path in java_paths:
            if "1.8" in version:
                self.java_paths["Java 8 (Minecraft 1.1 - 1.16.5)"] = path
            elif "17" in version:
                self.java_paths["Java 17 (Minecraft 1.17 - 1.20.4)"] = path
