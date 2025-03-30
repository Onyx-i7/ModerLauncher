from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QProgressBar, QWidget
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPixmap
import sys
import os
import importlib.util

def resource_path(relative_path):
    """Obtiene la ruta absoluta para recursos"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Para cargar imágenes
def load_image(path):
    return resource_path(os.path.join('assets', path))

# Para cargar sonidos
def load_sound(path):
    return resource_path(os.path.join('sonidos', path))

# Lista de módulos del proyecto
MODULES = [
    '1',
    'auth_manager',
    'bye',
    'download_progress',
    'game_window',
    'Java_Downloader',
    'java_error_window',
    'java_manager',
    'javaMensaje',
    'MCVersionSelector',
    'mensajeDoloand',
    'mods_window',
    'profile_window',
    'settings_window'
]

# Para importar módulos dinámicamente
def import_module(module_name):
    try:
        # Agregar debug para rastrear la carga
        print(f"\nIniciando importación de {module_name}")
        
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            print(f"Ejecutando desde exe - MEIPASS: {base_path}")
            
            # Listar archivos en MEIPASS para debug
            print("Archivos en MEIPASS:")
            for f in os.listdir(base_path):
                print(f"- {f}")
            
            module_path = os.path.join(base_path, f"{module_name}.py")
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(base_path, f"{module_name}.py")
            
        print(f"Buscando módulo en: {module_path}")
        
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"No se encuentra el módulo: {module_path}")
            
        print(f"Módulo encontrado, cargando...")
        
        # Cargar el módulo usando importlib
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        
        # Agregar el directorio del módulo al sys.path
        module_dir = os.path.dirname(module_path)
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
            
        # Ejecutar el módulo
        spec.loader.exec_module(module)
        sys.modules[module_name] = module
        
        print(f"Módulo {module_name} cargado exitosamente")
        return module

    except Exception as e:
        print(f"\nERROR importando {module_name}:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print(f"sys.path: {sys.path}")
        import traceback
        traceback.print_exc()
        raise

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Cargando')
        self.setFixedSize(300, 300)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.counter = 0
        
        # Crear contenedor interno
        self.container = QWidget(self)
        self.container.setFixedSize(300, 300)
        self.container.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 20px;
            }
        """)

        self.layout_setup()
        self.timer = QTimer()
        self.timer.timeout.connect(self.progress)
        self.timer.start(100)  # mantener 100ms para una animación suave
        self.show()

    def layout_setup(self):
        # Cambiar self por self.container como padre
        self.logo = QLabel(self.container)
        pixmap = QPixmap(load_image("logo/logo.png"))
        scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo.setPixmap(scaled_pixmap)
        self.logo.setGeometry(75, 80, 150, 150)

        self.loading_text = QLabel("Cargando...", self.container)
        self.loading_text.setStyleSheet("color: white; font-size: 16px;")
        self.loading_text.setAlignment(Qt.AlignCenter)
        self.loading_text.setGeometry(0, 250, 300, 30)

        self.progress_bar = QProgressBar(self.container)
        self.progress_bar.setGeometry(50, 280, 200, 10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #4a9fff;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setTextVisible(False)

    def progress(self):
        self.progress_bar.setValue(int(self.counter))
        if self.counter >= 100:
            self.timer.stop()
            self.close()
            try:
                print("\n=== Iniciando carga de módulos ===")
                
                # Asegurar que tkinter está disponible
                import tkinter as tk
                print("Tkinter importado correctamente")
                
                # Importar módulos principales
                print("Importando módulos principales...")
                for module_name in ['1', 'bye']:
                    try:
                        module = import_module(module_name)
                        print(f"Módulo {module_name} importado correctamente")
                        globals()[module_name] = module
                    except Exception as e:
                        print(f"Error importando {module_name}: {e}")
                        raise

                # Crear ventana principal
                print("Creando ventana principal...")
                root = tk.Tk()
                
                # Inicializar MinecraftLauncher
                print("Inicializando MinecraftLauncher...")
                main_window = globals()['1'].MinecraftLauncher(root)
                
                def on_closing():
                    if globals()['bye'].ask_quit(root):
                        root.destroy()
                
                root.protocol("WM_DELETE_WINDOW", on_closing)
                print("=== Inicialización completa ===\n")
                
                root.mainloop()
                
            except Exception as e:
                print("\n=== ERROR CRÍTICO ===")
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
                import time
                time.sleep(10)  # Mantener visible el error por 10 segundos
                sys.exit(1)
        self.counter += 2.5

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher_module = import_module('1')
    splash = launcher_module.SplashScreen(app)
    splash.show()
    sys.exit(app.exec_())
