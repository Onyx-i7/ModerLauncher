"""
Minecraft Launcher Principal - Clase principal del ModerLauncher
"""
import os
import sys
import json
import uuid
import time
import subprocess
import webbrowser
import minecraft_launcher_lib
from threading import Thread
from queue import Queue

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PIL import Image
from pygame import mixer

# Importaciones locales
from managers.auth_manager import AuthManager
from managers.game_window import GameWindow, VersionManager
from managers.profile_window import ProfileWindow
from managers.settings_window import SettingsWindow
from utils.bye import ask_quit
from utils.resource_manager import resource_path, get_local_data_dir, get_minecraft_dir
from core.version_observer import VersionObserver


class MinecraftLauncher(QMainWindow):
    # Colores
    DARK_BG = "#1E1E1E"
    LIGHTER_BG = "#252525"
    ACCENT_COLOR = "#4CAF50"
    TEXT_COLOR = "#FFFFFF"
    SECONDARY_TEXT = "#AAAAAA"
    
    # Señales
    status_changed = pyqtSignal(str)
    game_started = pyqtSignal()
    game_ended = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        # Usar ventana normal con barra de título estándar de Windows
        # self.setWindowFlags(Qt.FramelessWindowHint)  # Comentado
        # self.setAttribute(Qt.WA_TranslucentBackground)  # Comentado
        
        self.current_window = None
        self.main_content_frame = None
        self.nav_buttons = {}
        self.active_section = "home"
        self.observer_thread = None
        self.version_loader_thread = None
        self.loading_overlay = None
        self.preload_thread = None
        self.all_mc_versions = None
        self.drag_pos = None
        
        # Definir _update_status antes de conectar la señal
        def _update_status(self, text):
            """Actualizar texto de estado"""
            if hasattr(self, 'status_label'):
                self.status_label.setText(text)
        
        # Asignar el método
        self._update_status = _update_status.__get__(self)
        
        # Conectar señales
        self.status_changed.connect(self._update_status)
        self.game_started.connect(self._on_game_started)
        self.game_ended.connect(self._on_game_ended)
        
        self.setup_window()
        self.setup_directories()
        self.setup_managers()
        self.load_config()
        self.setup_audio()
        self.setup_ui()
        self.observer_thread.start()
        self.preload_all_versions()
    
    # ========== CONFIGURACIÓN INICIAL ==========
    
    def setup_window(self):
        """Configuración de la ventana principal"""
        self.setWindowTitle("ModerLauncher")
        self.setFixedSize(1200, 700)
        
        # Estilo para la ventana principal sin bordes redondeados
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {self.DARK_BG};
            }}
        """)
        
        # Centrar ventana
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1200) // 2
        y = (screen.height() - 700) // 2
        self.move(x, y)
        
        # Widget central ocupando toda la ventana (sin barra personalizada)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet(f"background: {self.DARK_BG};")

    def setup_directories(self):
        """Configurar directorios de Minecraft"""
        self.minecraft_directory = get_local_data_dir('moderlauncher')
        self.config_file = os.path.join(self.minecraft_directory, "launcher_config.json")
        
        os.makedirs(self.minecraft_directory, exist_ok=True)
        for directory in ['versions', 'assets', 'libraries', 'natives']:
            path = os.path.join(self.minecraft_directory, directory)
            os.makedirs(path, exist_ok=True)
    
    def setup_managers(self):
        """Inicializar managers"""
        self.auth_manager = AuthManager()
        self.version_manager = VersionManager()
        self.setup_version_observer()
    
    def setup_audio(self):
        """Configurar sistema de audio"""
        mixer.init()
        try:
            sound_path = resource_path('sounds/click_botton.mp3')
            self.click_sound = mixer.Sound(sound_path)
            self.click_sound.set_volume(0.5)
        except:
            self.click_sound = None
    
    def load_config(self):
        """Cargar configuración del launcher"""
        default_config = {
            "RAM": "2",
            "Java": None,
            "Nombre": "Player",
            "offline_username": None
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Guardar configuración"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def setup_version_observer(self):
        """Configura el observador de versiones en un hilo separado."""
        if self.observer_thread is not None:
            return

        self.observer_thread = QThread()
        self.version_observer = VersionObserver(self.version_manager)
        self.version_observer.moveToThread(self.observer_thread)

        self.observer_thread.started.connect(self.version_observer.observe)
        self.version_observer.versions_changed.connect(self.refresh_version_list)
    
    def preload_all_versions(self):
        """Carga todas las versiones de Minecraft en segundo plano al iniciar."""
        print("Pre-cargando lista de versiones de Minecraft...")

        class PreloadVersionThread(QThread):
            finished = pyqtSignal(list)
            def run(self):
                try:
                    versions = minecraft_launcher_lib.utils.get_version_list()
                    self.finished.emit(versions)
                except Exception as e:
                    print(f"Error en pre-carga de versiones: {e}")
                    self.finished.emit([])

        self.preload_thread = PreloadVersionThread()
        self.preload_thread.finished.connect(self.on_versions_preloaded)
        self.preload_thread.start()

    def on_versions_preloaded(self, versions):
        """Guarda las versiones pre-cargadas."""
        if versions:
            self.all_mc_versions = versions
            print(f"✅ Pre-carga completa: {len(self.all_mc_versions)} versiones guardadas.")
        else:
            print("❌ Falló la pre-carga de versiones. Se intentará de nuevo al abrir la ventana.")

    # ========== INTERFAZ DE USUARIO ==========
    
    def setup_ui(self):
        """Crear interfaz completa"""
        self.create_sidebar()
        self.show_home_window()
    
    def create_sidebar(self):
        """Crear barra lateral de navegación"""
        sidebar = QWidget(self.central_widget)
        sidebar.setGeometry(0, 0, 80, 700)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #121212;
            }
        """)
        
        # Logo
        logo_label = QLabel("ML", sidebar)
        logo_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        logo_label.setStyleSheet("color: white; background-color: transparent;")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setGeometry(0, 10, 80, 80)
        
        # Frame de usuario
        self.sidebar_user_frame = QWidget(sidebar)
        self.sidebar_user_frame.setGeometry(0, 90, 80, 60)
        self.sidebar_user_frame.setStyleSheet("background-color: transparent;")
        
        # Botones de navegación
        nav_items = [
            ("👤", "Cuenta", self.show_profile_window, "profile", 160),
            ("🏠", "Iniciar", self.show_home_window, "home", 245),
            ("🧩", "Mods", self.show_mods_window, "mods", 330),
            ("📂", "Versiones", self.show_game_window, "games", 415),
            ("⚙️", "Ajustes", self.show_settings_window, "settings", 500)
        ]
        
        for icon, label, command, section, y_pos in nav_items:
            self.create_nav_button(sidebar, icon, label, command, section, y_pos)
    
    def create_nav_button(self, parent, icon, label, command, section, y_pos):
        """Crear un botón de navegación"""
        btn_frame = QWidget(parent)
        btn_frame.setGeometry(0, y_pos, 80, 70)
        btn_frame.setStyleSheet("background-color: #121212;")
        
        # Icono
        btn = QLabel(icon, btn_frame)
        btn.setFont(QFont("Segoe UI", 20))
        btn.setStyleSheet("color: #888888; background-color: #121212;")
        btn.setAlignment(Qt.AlignCenter)
        btn.setGeometry(0, 0, 80, 40)
        btn.setCursor(Qt.PointingHandCursor)
        
        # Texto
        text_label = QLabel(label, btn_frame)
        text_label.setFont(QFont("Segoe UI", 8))
        text_label.setStyleSheet("color: #888888; background-color: #121212;")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setGeometry(0, 40, 80, 20)
        text_label.setCursor(Qt.PointingHandCursor)
        
        # Indicador
        indicator = QWidget(btn_frame)
        indicator.setGeometry(0, 20, 4, 30)
        indicator.setStyleSheet("background-color: #121212;")
        
        self.nav_buttons[section] = (btn, indicator, text_label)
        
        # Eventos
        btn.mousePressEvent = lambda e: self.on_nav_click(section, command)
        text_label.mousePressEvent = lambda e: self.on_nav_click(section, command)
    
    def on_nav_click(self, section, command):
        """Manejar click en navegación"""
        self.play_click_sound()
        self.active_section = section
        self.update_nav_buttons()
        command()
    
    def update_nav_buttons(self):
        """Actualizar estado visual de botones de navegación"""
        for section, (btn, indicator, text_label) in self.nav_buttons.items():
            if section == self.active_section:
                btn.setStyleSheet("color: white; background-color: #121212;")
                text_label.setStyleSheet("color: white; background-color: #121212;")
                indicator.setStyleSheet(f"background-color: {self.ACCENT_COLOR};")
            else:
                btn.setStyleSheet("color: #888888; background-color: #121212;")
                text_label.setStyleSheet("color: #888888; background-color: #121212;")
                indicator.setStyleSheet("background-color: #121212;")
    
    # ========== VENTANAS ==========
    
    def show_home_window(self):
        """Mostrar ventana principal"""
        print("📍 Navegando a ventana Iniciar")
        self.close_current_window()
        self.active_section = "home"
        self.update_nav_buttons()
        QTimer.singleShot(200, self.create_main_content)
    
    def show_profile_window(self):
        """Mostrar ventana de perfil"""
        print("📍 Navegando a ventana Perfil")
        self.close_current_window()
        self.active_section = "profile"
        self.update_nav_buttons()
        
        def create_profile_content():
            self.main_content_frame = QWidget(self.central_widget)
            self.main_content_frame.setGeometry(80, 0, 1120, 700)
            self.main_content_frame.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.DARK_BG};
                }}
            """)
            
            self.current_window = ProfileWindow(self.main_content_frame, self.update_sidebar_user)
            self.main_content_frame.show()
            
        QTimer.singleShot(200, create_profile_content)
    
    def show_game_window(self):
        """Mostrar ventana de versiones"""
        print("📍 Navegando a ventana Versiones")
        self.close_current_window()
        self.active_section = "games"
        self.update_nav_buttons()
        
        def create_game_content():
            self.main_content_frame = QWidget(self.central_widget)
            self.main_content_frame.setGeometry(80, 0, 1120, 700)
            self.main_content_frame.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.DARK_BG};
                }}
            """)
            
            try:
                self.current_window = GameWindow(
                    initial_data=self.all_mc_versions if hasattr(self, 'all_mc_versions') else None,
                    parent=self.main_content_frame,
                    launcher=self
                )
                self.main_content_frame.show()
                print("✅ GameWindow creada y mostrada exitosamente")
            except Exception as e:
                print(f"❌ Error creando GameWindow: {e}")
                QMessageBox.critical(self, "Error", f"No se pudo cargar la ventana de versiones:\\n{str(e)}")
                self.show_home_window()
        
        QTimer.singleShot(200, create_game_content)
    
    def show_settings_window(self):
        """Mostrar ventana de ajustes"""
        print("📍 Navegando a ventana Ajustes")
        self.close_current_window()
        self.active_section = "settings"
        self.update_nav_buttons()
        
        def create_settings_content():
            self.main_content_frame = QWidget(self.central_widget)
            self.main_content_frame.setGeometry(80, 0, 1120, 700)
            self.main_content_frame.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.DARK_BG};
                }}
            """)
            
            try:
                self.current_window = SettingsWindow(self.main_content_frame, self.play_click_sound)
                self.main_content_frame.show()
            except Exception as e:
                print(f"Error cargando SettingsWindow: {e}")
                QMessageBox.critical(self, "Error", f"No se pudo cargar la ventana de ajustes:\\n{str(e)}")
                self.show_home_window()
        
        QTimer.singleShot(200, create_settings_content)
    
    def show_mods_window(self):
        """Mostrar ventana de mods"""
        print("📍 Navegando a ventana Mods")
        self.close_current_window()
        self.active_section = "mods"
        self.update_nav_buttons()
        
        def create_mods_content():
            self.main_content_frame = QWidget(self.central_widget)
            self.main_content_frame.setGeometry(80, 0, 1120, 700)
            self.main_content_frame.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.DARK_BG};
                }}
            """)
            
            # TODO: Implementar ModsWindow cuando esté disponible
            label = QLabel("Ventana de Mods (En desarrollo)", self.main_content_frame)
            label.setStyleSheet("color: white; font-size: 24px;")
            label.setAlignment(Qt.AlignCenter)
            label.setGeometry(0, 0, 1120, 700)
            
            self.main_content_frame.show()
        
        QTimer.singleShot(200, create_mods_content)
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def close_current_window(self):
        """Cerrar ventana actual"""
        print("🔒 Cerrando ventana actual...")
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            print("✅ Ocultando overlay")
            self.loading_overlay.hide()
        
        if self.current_window:
            try:
                if hasattr(self.current_window, 'close'):
                    self.current_window.close()
                if hasattr(self.current_window, 'deleteLater'):
                    self.current_window.deleteLater()
            except Exception as e:
                print(f"Error cerrando ventana: {e}")
        
        if self.main_content_frame:
            try:
                self.main_content_frame.close()
                self.main_content_frame.deleteLater()
            except Exception as e:
                print(f"Error cerrando frame: {e}")
        
        self.current_window = None
        self.main_content_frame = None
        print("✅ Ventana cerrada")
    
    def play_click_sound(self):
        """Reproducir sonido de click"""
        try:
            if self.click_sound:
                self.click_sound.play()
        except:
            pass
    
    def create_main_content(self):
        """Crear contenido principal (placeholder)"""
        self.main_content_frame = QWidget(self.central_widget)
        self.main_content_frame.setGeometry(80, 0, 1120, 700)
        self.main_content_frame.setStyleSheet(f"""
            QWidget {{
                background-color: {self.DARK_BG};
            }}
        """)
        
        # Contenido temporal
        label = QLabel("Ventana Principal\\nModerLauncher", self.main_content_frame)
        label.setStyleSheet("color: white; font-size: 32px;")
        label.setAlignment(Qt.AlignCenter)
        label.setGeometry(0, 0, 1120, 700)
        
        self.main_content_frame.show()
    
    # Métodos placeholder que serán implementados después
    def update_sidebar_user(self, *args):
        """Actualizar información de usuario en sidebar"""
        pass
    
    def refresh_version_list(self):
        """Refrescar lista de versiones"""
        pass
    
    def _on_game_started(self):
        """Callback cuando inicia el juego"""
        pass
    
    def _on_game_ended(self, success, message):
        """Callback cuando termina el juego"""
        pass
    
    def closeEvent(self, event):
        """Manejar cierre de la aplicación"""
        print("🛑 Iniciando secuencia de cierre...")
        
        # Detener observer
        if hasattr(self, 'version_observer') and self.version_observer:
            print("🛑 Deteniendo VersionObserver...")
            self.version_observer.stop()
        
        if hasattr(self, 'observer_thread') and self.observer_thread:
            self.observer_thread.quit()
            self.observer_thread.wait(1000)
        
        # Limpiar audio
        print("🛑 Limpiando recursos de audio...")
        try:
            mixer.quit()
        except:
            pass
        
        print("✅ Aplicación lista para cerrar. Saliendo...")
        event.accept()