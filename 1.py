from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
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
from PIL import Image
from pygame import mixer

# Tus importaciones personalizadas
from managers.auth_manager import AuthManager
from managers.game_window import GameWindow, VersionManager
from managers.profile_window import ProfileWindow
from managers.settings_window import SettingsWindow
from utils.bye import ask_quit


# ==================== UTILIDADES ====================

def resource_path(relative_path):
    """Obtiene la ruta absoluta de un recurso"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==================== SPLASH SCREEN ====================

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Cargando')
        self.setFixedSize(300, 300)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Centrar en pantalla
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 300) // 2
        y = (screen.height() - 300) // 2
        self.move(x, y)
        
        self.counter = 0
        self.dot_count = 0
        self.texts = ['Iniciando', 'Cargando módulos', 'Preparando launcher']
        
        self.setup_ui()
        self.start_timers()

    def setup_ui(self):
        # Container
        container = QWidget(self)
        container.setFixedSize(300, 300)
        container.setStyleSheet("QWidget{background-color:#1a1a1a;border-radius:20px}")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Logo
        logo = QLabel()
        try:
            logo_pixmap = QPixmap(resource_path('assets/logo/logo.png')).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(logo_pixmap)
        except:
            logo.setText("ML")
            logo.setFont(QFont('Segoe UI', 48, QFont.Bold))
            logo.setStyleSheet("color: #FFF;")
        
        logo.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(logo)
        layout.addStretch()
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar{border:none;border-radius:4px;background-color:#2d2d2d}
            QProgressBar::chunk{border-radius:4px;background-color:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4CAF50,stop:1 #45a049)}
        """)
        
        # Loading Text
        self.loading_text = QLabel('Iniciando...')
        self.loading_text.setAlignment(Qt.AlignCenter)
        self.loading_text.setStyleSheet("QLabel{color:#FFF;font-size:14px;font-family:'Segoe UI';margin-top:10px}")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.loading_text)

    def start_timers(self):
        QTimer.singleShot(0, lambda: [
            QTimer.singleShot(i * 40, self.progress) for i in range(201)
        ])
        
        self.dot_timer = QTimer(self)
        self.dot_timer.timeout.connect(self.update_text)
        self.dot_timer.start(500)

    def update_text(self):
        current_text = self.texts[min(2, int(self.counter / 33))]
        self.loading_text.setText(f"{current_text}{'.' * ((self.dot_count % 3) + 1)}")
        self.dot_count += 1

    def progress(self):
        self.progress_bar.setValue(int(self.counter))
        if self.counter >= 100:
            self.dot_timer.stop()
            self.close()
            self.launch_main_app()
        self.counter += 0.5

    def launch_main_app(self):
        """Lanzar aplicación principal"""
        self.main_window = MinecraftLauncher()
        self.main_window.show()


# ==================== OBSERVADOR DE VERSIONES ====================

class VersionObserver(QObject):
    versions_changed = pyqtSignal()

    def __init__(self, version_manager):
        super().__init__()
        self.version_manager = version_manager
        self.running = False
        self.known_versions = set()

    @pyqtSlot()
    def observe(self):
        """Inicia el bucle de observación."""
        self.running = True
        while self.running:
            try:
                current_versions = set(self.version_manager.load_installed_versions().keys())
                if current_versions != self.known_versions:
                    self.known_versions = current_versions
                    self.versions_changed.emit()
            except Exception as e:
                print(f"Error en VersionObserver: {e}")
            time.sleep(2) # Comprobar cada 2 segundos

    @pyqtSlot()
    def stop(self):
        self.running = False


# ==================== LAUNCHER PRINCIPAL ====================

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
        self.drag_pos = None  # Add this line to initialize drag_pos
        
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
        self.preload_all_versions() # <-- NUEVO: Cargar versiones al inicio
    
    # ========== CONFIGURACIÓN INICIAL ==========
    
    def setup_window(self):
        """Configuración de la ventana principal"""
        self.setWindowTitle("ModerLauncher")
        self.setFixedSize(1200, 700)  # Aumentado de 668 a 700
        
        # Estilo para la ventana principal sin bordes redondeados
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {self.DARK_BG};
            }}
        """)
        
        # Centrar ventana
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1200) // 2
        y = (screen.height() - 700) // 2  # Ajustado para nueva altura
        self.move(x, y)
        
        # Widget central ocupando toda la ventana (sin barra personalizada)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet(f"background: {self.DARK_BG};")

    # def create_title_bar(self, parent):
    #     """Crear barra de título personalizada - DESHABILITADO"""
    #     # Función comentada porque ahora usamos barra de título estándar de Windows
    #     pass

    # def mousePressEvent(self, event):
    #     """Evento para arrastrar la ventana - DESHABILITADO"""
    #     # Windows maneja esto automáticamente con la barra de título estándar
    #     pass

    # def mouseReleaseEvent(self, event):
    #     """Evento para soltar el arrastre de la ventana - DESHABILITADO"""
    #     # Windows maneja esto automáticamente con la barra de título estándar
    #     pass

    # def mouseMoveEvent(self, event):
    #     """Evento para mover la ventana mientras se arrastra - DESHABILITADO"""
    #     # Windows maneja esto automáticamente con la barra de título estándar
    #     pass

    def setup_directories(self):
        """Configurar directorios de Minecraft"""
        self.minecraft_directory = os.path.join(os.getenv('APPDATA'), '.moderlauncher')
        self.config_file = os.path.join(self.minecraft_directory, "launcher_config.json")
        
        # Crear directorios necesarios
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
        # El hilo se limpiará solo al terminar

    # ========== INTERFAZ DE USUARIO ==========
    
    def setup_ui(self):
        """Crear interfaz completa"""
        self.create_sidebar()
        self.show_home_window()
    
    def create_sidebar(self):
        """Crear barra lateral de navegación"""
        sidebar = QWidget(self.central_widget)
        sidebar.setGeometry(0, 0, 80, 700)  # Altura completa
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #121212;
            }
        """)
        
        # Ajustar las posiciones Y de los elementos del sidebar
        # Logo y frame de usuario
        logo_label = QLabel("ML", sidebar)
        logo_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        logo_label.setStyleSheet("color: white; background-color: transparent;")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setGeometry(0, 10, 80, 80)
        
        # Frame de usuario
        self.sidebar_user_frame = QWidget(sidebar)
        self.sidebar_user_frame.setGeometry(0, 90, 80, 60)
        self.sidebar_user_frame.setStyleSheet("background-color: transparent;")
        
        # Botones de navegación ajustados
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
        # Container
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
        
        # Efectos hover
        def enter_event(e):
            if self.active_section != section:
                btn.setStyleSheet("color: white; background-color: #121212;")
                text_label.setStyleSheet("color: white; background-color: #121212;")
                indicator.setStyleSheet(f"background-color: {self.ACCENT_COLOR};")
        
        def leave_event(e):
            if self.active_section != section:
                btn.setStyleSheet("color: #888888; background-color: #121212;")
                text_label.setStyleSheet("color: #888888; background-color: #121212;")
                indicator.setStyleSheet("background-color: #121212;")
        
        btn.enterEvent = enter_event
        btn.leaveEvent = leave_event
        text_label.enterEvent = enter_event
        text_label.leaveEvent = leave_event
    
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
            self.main_content_frame.setGeometry(80, 0, 1120, 660)  # Ajustado
            self.main_content_frame.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.DARK_BG};
                    border-bottom-right-radius: 18px;
                }}
            """)
            
            self.current_window = ProfileWindow(self.main_content_frame, self.update_sidebar_user)
            
            self.main_content_frame.show()
            self.main_content_frame.raise_()
            QApplication.processEvents()
            
        QTimer.singleShot(200, create_profile_content)
    
    def show_game_window(self):
        """Mostrar ventana de versiones - SIMPLIFICADO"""
        print("📍 Navegando a ventana Versiones")
        
        # ✅ Limpiar thread anterior si existe
        if hasattr(self, 'version_loader_thread') and self.version_loader_thread:
            try:
                self.version_loader_thread.finished.disconnect()
            except (TypeError, RuntimeError):
                pass
            
            if self.version_loader_thread.isRunning():
                self.version_loader_thread.quit()
                self.version_loader_thread.wait(500)
            
            self.version_loader_thread.deleteLater()
            self.version_loader_thread = None
        
        # Cerrar ventana anterior
        self.close_current_window()
        self.active_section = "games"
        self.update_nav_buttons()
        QApplication.processEvents()
        
        def create_game_content():
            """Crear ventana de versiones - SIMPLIFICADO"""
            self.main_content_frame = QWidget(self.central_widget)
            self.main_content_frame.setGeometry(80, 0, 1120, 660)  # Ajustado
            self.main_content_frame.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.DARK_BG};
                    border-bottom-right-radius: 18px;
                }}
            """)
            
            def on_refresh_needed():
                print("🔄 Petición de refresco de versiones, recargando...")
                self.show_game_window()
            
            try:
                # ✅ PATRÓN ModsWindow: Pasar caché opcional
                self.current_window = GameWindow(
                    initial_data=self.all_mc_versions if hasattr(self, 'all_mc_versions') else None,
                    parent=self.main_content_frame,
                    refresh_callback=on_refresh_needed,
                    launcher=self
                )
                
                self.main_content_frame.show()
                self.main_content_frame.raise_()
                QApplication.processEvents()
                print("✅ GameWindow creada y mostrada exitosamente")
                
            except Exception as e:
                print(f"❌ Error creando GameWindow: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"No se pudo cargar la ventana de versiones:\n{str(e)}")
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
            self.main_content_frame.setGeometry(80, 0, 1120, 660)  # Ajustado
            self.main_content_frame.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.DARK_BG};
                    border-bottom-right-radius: 18px;
                }}
            """)
            try:
                self.current_window = SettingsWindow(self.main_content_frame, self.play_click_sound)
                self.main_content_frame.show()
                self.main_content_frame.raise_()
                QApplication.processEvents()
            except Exception as e:
                print(f"Error cargando SettingsWindow: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"No se pudo cargar la ventana de ajustes:\n{str(e)}")
                self.show_home_window()
        QTimer.singleShot(200, create_settings_content)
    
    def show_mods_window(self):
        """Mostrar ventana de mods"""
        print("📍 Navegando a ventana Mods")
        self.close_current_window()
        self.active_section = "mods"
        self.update_nav_buttons()

        QApplication.processEvents()
        
        def create_mods_content():
            """Crear ventana de mods"""
            self.main_content_frame = QWidget(self.central_widget)
            self.main_content_frame.setGeometry(80, 0, 1120, 660)  # Ajustado
            self.main_content_frame.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.DARK_BG};
                    border-bottom-right-radius: 18px;
                }}
            """)
            
            try:
                from ui.windows.mods_window import ModsWindow
                self.current_window = ModsWindow(
                    initial_data=None, # ModsWindow cargará sus propios datos
                    parent=self.main_content_frame,
                    launcher=self
                )
                
                self.main_content_frame.show()
                self.main_content_frame.raise_()
                QApplication.processEvents()
                print("✅ ModsWindow creada y mostrada exitosamente")
                
            except Exception as e:
                print(f"❌ Error creando ModsWindow: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"No se pudo cargar la ventana de mods:\n{str(e)}")
                self.show_home_window()
        
        QTimer.singleShot(200, create_mods_content)

    def show_loading_overlay(self, text="Cargando..."):
        """Muestra una capa de carga sobre el contenido principal."""
        print(f"🔄 Mostrando overlay: {text}")
        
        # Ocultar overlay anterior si existe
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.deleteLater()
        
        self.loading_overlay = QLabel(text, self.central_widget)
        self.loading_overlay.setGeometry(80, 0, 1120, 668)
        self.loading_overlay.setStyleSheet("background-color: rgba(30, 30, 30, 0.9); color: white; font-size: 24px; font-weight: bold;")
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.show()
        self.loading_overlay.raise_()
        QApplication.processEvents()

    def hide_loading_overlay(self):
        """Oculta la capa de carga."""
        print("✅ Ocultando overlay")
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.hide()
            self.loading_overlay.deleteLater()
            self.loading_overlay = None
            QApplication.processEvents()

    def close_current_window(self):
        """Cerrar ventana actual de manera segura - CORREGIDO"""
        print("🔒 Cerrando ventana actual...")
        
        # ✅ OCULTAR OVERLAY PRIMERO
        self.hide_loading_overlay()
        
        if self.current_window is None and self.main_content_frame is None:
            print("✅ No hay ventana que cerrar")
            return
        
        try:
            if self.current_window:
                # ✅ BLOQUEAR SEÑALES
                self.current_window.blockSignals(True)
                
                if hasattr(self.current_window, 'stop_sound'):
                    self.current_window.stop_sound()
                if hasattr(self.current_window, 'disconnect_signals'):
                    self.current_window.disconnect_signals()
                if hasattr(self.current_window, 'stop_threads'):
                    self.current_window.stop_threads()
                # Específicamente para GameWindow, que tiene su propio método
                if isinstance(self.current_window, GameWindow):
                    self.current_window.stop_threads()
                
                self.current_window.hide()
            
            if self.main_content_frame:
                self.main_content_frame.blockSignals(True)
                self.main_content_frame.hide()
            
            QTimer.singleShot(100, self._cleanup_window)
            
        except Exception as e:
            print(f"❌ Error cerrando ventana: {e}")

    def _cleanup_window(self):
        """Limpieza final de la ventana - MEJORADO"""
        print("🧹 Limpiando ventana...")
        try:
            if self.current_window:
                self.current_window.blockSignals(True)
                self.current_window.deleteLater()
            if self.main_content_frame:
                self.main_content_frame.blockSignals(True)
                self.main_content_frame.deleteLater()
        except Exception as e:
            print(f"❌ Error en cleanup: {e}")
        finally:
            self.main_content_frame = None
            self.current_window = None
        QApplication.processEvents()
        print("✅ Ventana limpiada")
    
    # ========== CONTENIDO PRINCIPAL ==========
    
    def create_main_content(self):
        """Crear contenido de la ventana principal"""
        print("🏗️ Creando ventana principal")
        
        if self.main_content_frame is not None:
            self.main_content_frame.setParent(None)
            self.main_content_frame.deleteLater()
            self.main_content_frame = None
            QApplication.processEvents()
        
        self.main_content_frame = QWidget(self.central_widget)
        self.main_content_frame.setGeometry(80, 0, 1120, 660)  # Ajustado
        self.main_content_frame.setStyleSheet(f"""
            QWidget {{
                background-color: {self.DARK_BG};
                border-bottom-right-radius: 18px;
            }}
        """)
        
        try:
            self.create_banner()
            self.create_launch_section()
        except Exception as e:
            print(f"Error en create_main_content: {e}")
            import traceback
            traceback.print_exc()
        
        self.main_content_frame.show()
        self.main_content_frame.raise_()
        self.main_content_frame.setFocus()

        print("✅ Ventana principal creada")
    
    def create_banner(self):
        """Crear banner superior"""
        banner = QWidget(self.main_content_frame)
        banner.setGeometry(10, 10, 1100, 200)
        banner.setStyleSheet("""
            QWidget {
                background-color: #1A2327;
                border-radius: 15px;
            }
        """)
        
        title = QLabel("Minecraft", banner)
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: white; background-color: transparent;")
        title.setGeometry(30, 30, 400, 40)
        
        subtitle = QLabel("Custom Modpack", banner)
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #4CAF50; background-color: transparent;")
        subtitle.setGeometry(30, 70, 400, 30)
        
        description = ("La mejor versión de Minecraft Java para un rendimiento más fluido es la 1.20.1.\n"
                      "En esta versión, el juego corre mejor debido a varios factores que optimizan el rendimiento,\n"
                      "como los mods de FPS. Para Fabric, tenemos Sodium y Extra Sodium, que mejoran notablemente\n"
                      "la tasa de cuadros por segundo, y para Forge, están Embedium y Extra Embedium,\n"
                      "que también optimizan el rendimiento, haciendo que el juego sea más estable y rápido.")
        
        desc_label = QLabel(description, banner)
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet("color: #888888; background-color: transparent;")
        desc_label.setWordWrap(True)
        desc_label.setGeometry(30, 100, 900, 90)
        
        self.create_social_icons(banner)
    
    def create_social_icons(self, parent):
        """Crear iconos de redes sociales - CORREGIDO"""
        social_links = [
            ("assets/redes/github.gif", "GitHub", "https://github.com/jephersonRD", 900),
            ("assets/redes/youtube.gif", "YouTube", "https://www.youtube.com/@jeph_rd", 960),
            ("assets/redes/tiktok.gif", "TikTok", "https://www.tiktok.com/@jepherson_rd", 1020) # Corregido
        ]
        
        def make_click_handler(url):
            """Función auxiliar para crear el manejador de click"""
            def handler(event):
                self.play_click_sound()
                webbrowser.open(url)
            return handler
        
        for icon_path, label, url, x_pos in social_links:
            frame = QWidget(parent)
            frame.setGeometry(x_pos, 70, 50, 60)
            frame.setStyleSheet("background-color: transparent;")
            
            try:
                pixmap = QPixmap(resource_path(icon_path)).scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label = QLabel(frame)
                icon_label.setPixmap(pixmap)
            except:
                icon_label = QLabel("•", frame)
                icon_label.setFont(QFont("Segoe UI", 20))
                icon_label.setStyleSheet("color: #888888; background: transparent;")
            
            icon_label.setGeometry(10, 0, 30, 30)
            icon_label.setCursor(Qt.PointingHandCursor)
            
            text_label = QLabel(label, frame)
            text_label.setFont(QFont("Segoe UI", 8))
            text_label.setStyleSheet("color: #888888; background: transparent;")
            text_label.setAlignment(Qt.AlignCenter)
            text_label.setGeometry(0, 30, 50, 20)
            text_label.setCursor(Qt.PointingHandCursor)
            
            # ✅ FIX: Usar la función auxiliar en lugar de lambda
            click_handler = make_click_handler(url)
            icon_label.mousePressEvent = click_handler
            text_label.mousePressEvent = click_handler
    
    def create_launch_section(self):
        """Crear sección de lanzamiento"""
        launch_frame = QWidget(self.main_content_frame)
        launch_frame.setGeometry(300, 560, 520, 80)
        launch_frame.setStyleSheet(f"background-color: transparent;")
        
        version_label = QLabel("VERSION", launch_frame)
        version_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        version_label.setStyleSheet(f"color: {self.SECONDARY_TEXT}; background: transparent;")
        version_label.setGeometry(0, 0, 150, 20)
        
        self.version_combo = QComboBox(launch_frame)
        self.version_combo.setGeometry(0, 25, 200, 40)
        self.version_combo.setFont(QFont("Segoe UI", 11))
        self.version_combo.view().setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.version_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #3C3C41;
                border-radius: 8px;
                padding: 5px 15px;
                min-height: 40px;
                selection-background-color: {self.ACCENT_COLOR};
                selection-color: white;
            }}
            QComboBox:hover {{
                border-color: {self.ACCENT_COLOR};
                background-color: #353535;
            }}
            QComboBox:focus {{
                border-color: {self.ACCENT_COLOR};
                background-color: #353535;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 10px;
            }}
            QComboBox:on {{ /* cuando está abierto */
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2d2d2d;
                color: white;
                selection-background-color: {self.ACCENT_COLOR};
                selection-color: white;
                border: 1px solid {self.ACCENT_COLOR};
                padding: 5px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                background-color: #2d2d2d;
                color: white;
                min-height: 30px;
                padding: 5px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #3d8c40;
                color: white;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {self.ACCENT_COLOR};
                color: white;
            }}
            QComboBox QScrollBar:vertical {{
                background-color: #2d2d2d;
                width: 12px;
                margin: 0px;
            }}
            QComboBox QScrollBar::handle:vertical {{
                background-color: #4A4A4E;
                min-height: 30px;
                border-radius: 6px;
            }}
            QComboBox QScrollBar::add-line:vertical,
            QComboBox QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QComboBox QScrollBar::add-page:vertical,
            QComboBox QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        self.version_combo.addItems(self.get_installed_versions())
        current_version = self.version_manager.get_installed_version()
        if current_version:
            self.version_combo.setCurrentText(current_version)
        else:
            versions = self.get_installed_versions()
            if versions:
                self.version_combo.setCurrentIndex(0)
        
        self.create_play_button(launch_frame)
    
    def create_play_button(self, parent):
        """Crear botón de PLAY"""
        play_btn = QPushButton("", parent)
        play_btn.setGeometry(220, 0, 200, 60)
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ACCENT_COLOR};
                border: none;
                border-radius: 30px;
            }}
            QPushButton:hover {{
                background-color: #3d8c40;
            }}
            QPushButton:pressed {{
                background-color: #2d7030;
            }}
        """)
        
        btn_layout = QVBoxLayout(play_btn)
        btn_layout.setContentsMargins(0, 5, 0, 5)
        btn_layout.setSpacing(2)
        
        play_text = QLabel("PLAY")
        play_text.setFont(QFont("Segoe UI", 16, QFont.Bold))
        play_text.setStyleSheet(f"color: {self.TEXT_COLOR}; background: transparent;")
        play_text.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(play_text)
        
        self.status_label = QLabel("READY TO LAUNCH")
        self.status_label.setFont(QFont("Segoe UI", 8))
        self.status_label.setStyleSheet(f"color: {self.TEXT_COLOR}; background: transparent;")
        self.status_label.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(self.status_label)
        
        play_btn.clicked.connect(self.launch_game)
    
    # ========== GESTIÓN DE VERSIONES ==========
    
    @staticmethod
    def version_key(version):
        """Clave para ordenar versiones"""
        try:
            parts = version.split('.')
            return tuple(int(p) for p in parts[:3])
        except:
            return (0, 0, 0)
    
    def get_installed_versions(self):
        """Obtener lista de versiones instaladas ordenadas"""
        try:
            versions = list(self.version_manager.load_installed_versions().keys())
            return sorted(versions, key=self.version_key, reverse=True)
        except Exception as e:
            print(f"Error obteniendo versiones instaladas: {e}")
            return []
    
    def refresh_version_list(self):
        """Actualizar lista de versiones"""
        try:
            if self.active_section != "home":
                return
            
            if not hasattr(self, 'version_combo'):
                return
            
            self.version_manager.refresh_installed_versions()
            versions = self.get_installed_versions()
            
            current = self.version_combo.currentText()
            self.version_combo.clear()
            self.version_combo.addItems(versions)
            
            if current in versions:
                self.version_combo.setCurrentText(current)
            elif versions:
                self.version_combo.setCurrentIndex(0)
            
        except Exception as e:
            print(f"Error actualizando versiones: {e}")
    
    # ========== LANZAMIENTO DEL JUEGO ==========
    
    def check_java_version(self, mc_version):
        """Verificar versión de Java requerida"""
        try:
            # Usar parse_version_string para una comparación fiable
            parsed_version = minecraft_launcher_lib.utils.parse_version_string(mc_version)
            required_java = "17" if parsed_version >= (1, 17) else "8"
        except:
            # Fallback para versiones no estándar
            required_java = "8"

        java_path = None
        
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                java_versions = settings.get('java_versions', {})
                
                if required_java == "17":
                    java_path = java_versions.get("Java 17 (Minecraft 1.17 - 1.20.4)")
                else:
                    java_path = java_versions.get("Java 8 (Minecraft 1.1 - 1.16.5)")
        except:
            pass
            
        if not java_path or not os.path.exists(java_path):
            print(f"❌ Java {required_java} no encontrado para Minecraft {mc_version}. Mostrando alerta.")
            from javaMensaje import show_java_alert
            # Usar show_java_alert para mostrar el diálogo modalmente
            show_java_alert(self, mc_version, required_java)
            return False
            
        print(f"✅ Java {required_java} encontrado en: {java_path}")
        return java_path

    def launch_game(self):
        """Iniciar el juego"""
        try:
            selected_version = self.version_combo.currentText()
            if not selected_version:
                QMessageBox.warning(self, "Error", "Selecciona una versión de Minecraft")
                return
            print(f"🚀 Intentando lanzar la versión: {selected_version}")

            login_data = self.auth_manager.get_login_data()
            if not login_data:
                QMessageBox.warning(self, "Error", "No hay usuario configurado")
                return
            print(f"👤 Usando cuenta: {login_data.get('username')}")

            java_path = self.check_java_version(selected_version)
            if not java_path:
                self._update_status("JAVA NO ENCONTRADO")
                return

            self._update_status("Iniciando Minecraft...")

            logs_dir = os.path.join(self.minecraft_directory, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            log_path = os.path.join(logs_dir, f"launcher_log_{int(time.time())}.txt")

            launch_thread = Thread(
                target=self._launch_game_thread,
                args=(selected_version, java_path, login_data, log_path),
                daemon=True
            )
            launch_thread.start()

        except Exception as e:
            self._update_status("ERROR AL INICIAR")
            QMessageBox.critical(self, "Error", f"Error iniciando Minecraft:\n{str(e)}")

    def _launch_game_thread(self, version, java_path, login_data, log_path):
        """Thread separado para lanzar el juego"""
        try:
            try:
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    ram = settings.get('ram', 2048)
                    ram_gb = max(1, ram // 1024)
            except:
                ram_gb = 2

            jvm_args = [
                f"-Xmx{ram_gb}G",
                f"-Xms{ram_gb}G",
                "-XX:+UseG1GC",
                "-XX:+ParallelRefProcEnabled",
                "-XX:MaxGCPauseMillis=200",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+DisableExplicitGC",
                "-XX:+AlwaysPreTouch",
                "-XX:+UseFastAccessorMethods"
            ]

            options = {
                "username": login_data["username"],
                "uuid": login_data["uuid"],
                "token": login_data["accessToken"],
                "executablePath": java_path,
                "jvmArguments": jvm_args,
                "launcherName": "ModerLauncher",
                "launcherVersion": "1.0"
            }

            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                version=version,
                minecraft_directory=self.minecraft_directory,
                options=options
            )

            with open(log_path, "w", encoding="utf-8") as log_file:
                process = subprocess.Popen(
                    minecraft_command,
                    stdout=log_file,
                    stderr=log_file,
                    cwd=self.minecraft_directory,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                self.game_started.emit()
                process.wait()
                self.game_ended.emit(process.returncode == 0, log_path)

        except Exception as e:
            print(f"Error en launch thread: {e}")
            self.game_ended.emit(False, str(e))
    
    # ========== UTILIDADES ==========
    
    def play_click_sound(self):
        """Reproducir sonido de click"""
        try:
            if self.click_sound:
                # Asegurarnos que mixer está inicializado
                if not mixer.get_init():
                    mixer.init()
                channel = self.click_sound.play()
                if channel:
                    channel.set_volume(0.5)
        except Exception as e:
            print(f"Error reproduciendo sonido: {e}")
            # Intentar reinicializar mixer si falló
            try:
                mixer.quit()
                mixer.init()
            except:
                pass

    def closeEvent(self, event):
        """Evento al cerrar ventana"""
        try:
            # Intentar reproducir sonido antes de preguntar
            if hasattr(self, 'click_sound') and self.click_sound:
                try:
                    if not mixer.get_init():
                        mixer.init()
                    self.click_sound.play()
                except:
                    pass
            
            if ask_quit(self):
                print("🛑 Iniciando secuencia de cierre...")
                
                # Detener hilos de forma segura
                if self.observer_thread and self.observer_thread.isRunning():
                    print("🛑 Deteniendo VersionObserver...")
                    self.version_observer.stop()
                    self.observer_thread.quit()
                    self.observer_thread.wait(1000) # Esperar máx 1 seg
                
                if self.preload_thread and self.preload_thread.isRunning():
                    print("🛑 Deteniendo PreloadThread...")
                    self.preload_thread.quit()
                    self.preload_thread.wait(1000)

                if self.version_loader_thread and self.version_loader_thread.isRunning():
                    print("🛑 Deteniendo VersionLoaderThread...")
                    self.version_loader_thread.quit()
                    self.version_loader_thread.wait(1000)
                
                # Limpiar recursos de audio
                try:
                    print("🛑 Limpiando recursos de audio...")
                    mixer.quit()
                except:
                    pass
                    
                event.accept()
                print("✅ Aplicación lista para cerrar. Saliendo...")
                QApplication.quit() # Termina el bucle de eventos de Qt
                sys.exit(0) # Asegura que el proceso termine

            else:
                event.ignore()
        except Exception as e:
            print(f"Error en closeEvent: {e}")
            event.accept()

    def _update_status(self, text):
        """Actualizar texto de estado"""
        if hasattr(self, 'status_label'):
            self.status_label.setText(text)

    def _on_game_started(self):
        """Manejar inicio del juego"""
        self._update_status("RUNNING")
        self.hide()

    def _on_game_ended(self, success, log_path):
        """Manejar fin del juego"""
        self.show()
        if success:
            self._update_status("READY TO LAUNCH")
        else:
            self._update_status("ERROR")
            QMessageBox.critical(self, "Error", 
                               f"Minecraft cerró con error.\nRevisa el log: {log_path}")

    def update_sidebar_user(self):
        """Actualizar información de usuario en la barra lateral (placeholder)"""
        pass


# ==================== MAIN ====================

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Añadir icono a la aplicación
        icon_path = resource_path('assets/logo/icon.ico')
        app.setWindowIcon(QIcon(icon_path))
        
        app.setQuitOnLastWindowClosed(False)
        
        splash = SplashScreen()
        splash.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()