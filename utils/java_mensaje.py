from typing import Optional, Dict
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QWidget,
    QGraphicsDropShadowEffect, QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QColor
import webbrowser
import os
import sys

# Pygame mixer - importación segura
try:
    from pygame import mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


def resource_path(relative_path):
    """Obtiene la ruta absoluta de un recurso (compatible con PyInstaller)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class JavaErrorWindow(QDialog):
    """Ventana de error moderna para notificar la falta de Java - MEJORADA"""
    
    # ===== CONSTANTES AJUSTADAS =====
    WINDOW_WIDTH = 520
    WINDOW_HEIGHT = 560  # ⬆️ AUMENTADO MÁS (era 520)
    AUTO_CLOSE_TIME = 15000  # 15 segundos
    
    JAVA_DOWNLOAD_URLS: Dict[str, str] = {
        "8": "https://adoptium.net/temurin/releases/?version=8",
        "11": "https://adoptium.net/temurin/releases/?version=11",
        "17": "https://adoptium.net/temurin/releases/?version=17",
        "21": "https://adoptium.net/temurin/releases/?version=21"
    }
    DEFAULT_JAVA_URL = "https://adoptium.net/temurin/releases/"
    
    # ===== ESTILOS MEJORADOS =====
    MAIN_STYLE = """
        QDialog {
            background-color: #1E1E1E;
            border-radius: 15px;
        }
    """
    
    def __init__(self, parent: Optional[QWidget] = None, 
                 mc_version: str = "Unknown", 
                 required_java: str = "17"):
        super().__init__(parent)
        
        self.mc_version = mc_version
        self.required_java = self._validate_java_version(required_java)
        self.auto_close_timer: Optional[QTimer] = None
        self.countdown_timer: Optional[QTimer] = None
        self.remaining_seconds = self.AUTO_CLOSE_TIME // 1000
        self.is_closing = False  # ✅ NUEVO: Flag para controlar cierre
        
        self._setup_ui()
        self._apply_effects()
        self._start_animations()
        self._setup_auto_close()
        self._center_on_screen()
    
    def _validate_java_version(self, version: str) -> str:
        """Validar y normalizar versión de Java"""
        version_clean = ''.join(filter(str.isdigit, str(version)))
        
        if version_clean in self.JAVA_DOWNLOAD_URLS:
            return version_clean
        
        return "17"
    
    def _setup_ui(self):
        """Configurar interfaz de usuario - MEJORADA"""
        self.setWindowTitle("☕ Java No Encontrado")
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(self.MAIN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)  # ✅ Reducido más (era 15)
        
        # ===== ICONO =====
        icon = QLabel("☕")
        icon.setFont(QFont("Segoe UI Emoji", 52))  # ✅ Reducido más
        icon.setStyleSheet("color: #FFB900; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedHeight(65)
        layout.addWidget(icon)
        
        # ===== TÍTULO =====
        title = QLabel(f"Java {self.required_java} Requerido")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(35)
        layout.addWidget(title)
        
        # ===== MENSAJE =====
        message = QLabel(
            f"Para ejecutar Minecraft {self.mc_version}\n"
            f"necesitas tener Java {self.required_java} instalado.\n\n"
            f"Por favor, descarga e instala Java\n"
            f"o ajusta la configuración."
        )
        message.setFont(QFont("Segoe UI", 11))
        message.setStyleSheet("color: #CCCCCC; background: transparent;")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setMinimumHeight(90)  # ✅ Altura mínima para el texto
        layout.addWidget(message)
        
        layout.addSpacing(5)  # ✅ Espacio pequeño
        
        # ===== COUNTDOWN =====
        self.countdown_label = QLabel(f"Esta ventana se cerrará en {self.remaining_seconds} segundos")
        self.countdown_label.setFont(QFont("Segoe UI", 9))
        self.countdown_label.setStyleSheet("color: #FFB900; background: transparent;")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setFixedHeight(30)  # ✅ Más altura
        layout.addWidget(self.countdown_label)
        
        layout.addSpacing(10)
        
        # ===== Botones =====
        self._create_buttons(layout)
    
    def _create_buttons(self, layout: QVBoxLayout):
        """Crear botones de acción - MEJORADOS"""
        button_style = """
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 13px;
                font-weight: bold;
                min-height: 42px;
                max-height: 52px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
        """
        
        # Descargar Java
        self.download_btn = QPushButton(f"☕ Descargar Java {self.required_java}")
        self.download_btn.setStyleSheet(button_style.format(
            bg="#4CAF50", hover="#45a049", pressed="#3d8c40"
        ))
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self._download_java)
        layout.addWidget(self.download_btn)
        
        # ✅ TEXTO CAMBIADO
        self.settings_btn = QPushButton("⚙️ Configura Java en Ajustes")
        self.settings_btn.setStyleSheet(button_style.format(
            bg="#2196F3", hover="#1976D2", pressed="#0D47A1"
        ))
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self._go_to_settings)
        layout.addWidget(self.settings_btn)
        
        # Cancelar (Cerrar)
        self.cancel_btn = QPushButton("✕ Cancelar")
        self.cancel_btn.setStyleSheet(button_style.format(
            bg="#757575", hover="#616161", pressed="#424242"
        ))
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._force_close)  # ✅ CORREGIDO
        layout.addWidget(self.cancel_btn)
    
    def _apply_effects(self):
        """Aplicar efectos visuales"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
    
    def _start_animations(self):
        """Iniciar animaciones de entrada"""
        self.setWindowOpacity(0)
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_in.start()
    
    def _setup_auto_close(self):
        """Configurar auto-cierre con countdown"""
        # ✅ CORREGIDO: Usar _force_close en vez de close
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.timeout.connect(self._auto_close)
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.start(self.AUTO_CLOSE_TIME)
        
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.start(1000)
    
    def _update_countdown(self):
        """Actualizar countdown"""
        self.remaining_seconds -= 1
        
        if self.remaining_seconds > 0:
            self.countdown_label.setText(
                f"Esta ventana se cerrará en {self.remaining_seconds} segundos"
            )
        else:
            self.countdown_label.setText("Cerrando...")
            if self.countdown_timer:
                self.countdown_timer.stop()
    
    def _center_on_screen(self):
        """Centrar ventana"""
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _download_java(self):
        """Abrir navegador para descargar Java"""
        url = self.JAVA_DOWNLOAD_URLS.get(
            self.required_java, 
            self.DEFAULT_JAVA_URL
        )
        
        try:
            webbrowser.open(url)
            self.download_btn.setText("✓ Navegador abierto")
            self.download_btn.setEnabled(False)
            QTimer.singleShot(2000, self._force_close)  # ✅ CORREGIDO
        except Exception as e:
            print(f"❌ Error abriendo navegador: {e}")
    
    def _go_to_settings(self):
        """Ir a configuración"""
        print("🔧 Abriendo ajustes de Java...")  # ✅ Debug
        self._force_close()  # ✅ Cerrar primero
        # Aquí puedes emitir una señal o llamar a otra función
        # para abrir la configuración en tu launcher
    
    # ✅ NUEVO MÉTODO: Forzar cierre
    def _force_close(self):
        """Cerrar ventana inmediatamente sin animación"""
        if self.is_closing:
            return
        
        self.is_closing = True
        
        # Detener timers
        if self.auto_close_timer:
            self.auto_close_timer.stop()
        if self.countdown_timer:
            self.countdown_timer.stop()
        
        # Cerrar directamente
        super().close()
    
    # ✅ NUEVO MÉTODO: Auto-cierre con animación
    def _auto_close(self):
        """Cierre automático por timeout"""
        if self.is_closing:
            return
        
        self.is_closing = True
        
        # Detener timers
        if self.countdown_timer:
            self.countdown_timer.stop()
        
        # Animación de salida
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(lambda: super(JavaErrorWindow, self).close())
        self.fade_out.start()
    
    def mousePressEvent(self, event):
        """Permitir arrastrar"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Mover ventana"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    # ✅ SIMPLIFICADO
    def closeEvent(self, event):
        """Cleanup al cerrar"""
        if not self.is_closing:
            event.ignore()
            self._auto_close()
        else:
            event.accept()
    
    @pyqtProperty(float)
    def opacity(self):
        return self.windowOpacity()
    
    @opacity.setter
    def opacity(self, value):
        self.setWindowOpacity(value)


# ===== FUNCIÓN DE CONVENIENCIA =====
def show_java_alert(parent: Optional[QWidget] = None,
                    mc_version: str = "Unknown",
                    required_java: str = "17") -> int:
    """Mostrar alerta de Java - FUNCIÓN PRINCIPAL"""
    dialog = JavaErrorWindow(parent, mc_version, required_java)
    return dialog.exec_()


# Alias para compatibilidad
JavaVersionAlert = JavaErrorWindow