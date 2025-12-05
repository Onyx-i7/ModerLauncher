from typing import Optional, Dict
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QGraphicsDropShadowEffect, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QColor
import webbrowser


class JavaErrorWindow(QDialog):
    """
    Ventana de error moderna para notificar la falta de Java.
    
    Features:
    - Diseño moderno con sombras y animaciones
    - Auto-cierre después de 15 segundos
    - Links directos a descargas de Java
    - Animación de aparición suave
    """
    
    # ===== CONSTANTES =====
    WINDOW_WIDTH = 450
    WINDOW_HEIGHT = 320
    AUTO_CLOSE_TIME = 15000  # 15 segundos
    
    # URLs de descarga
    JAVA_DOWNLOAD_URLS: Dict[str, str] = {
        "8": "https://adoptium.net/temurin/releases/?version=8",
        "11": "https://adoptium.net/temurin/releases/?version=11",
        "17": "https://adoptium.net/temurin/releases/?version=17",
        "21": "https://adoptium.net/temurin/releases/?version=21"
    }
    
    DEFAULT_JAVA_URL = "https://adoptium.net/temurin/releases/"
    
    # Emojis para diferentes tipos de alerta
    ICONS = {
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "java": "☕"
    }
    
    # ===== ESTILOS =====
    MAIN_STYLE = """
        QDialog {
            background-color: #2b2b2b;
            border-radius: 12px;
        }
    """
    
    WARNING_ICON_STYLE = """
        color: #FFB900;
        padding: 10px;
    """
    
    MESSAGE_STYLE = """
        color: white;
        font-size: 15px;
        font-weight: bold;
        padding: 10px;
    """
    
    SUBMESSAGE_STYLE = """
        color: #CCCCCC;
        font-size: 12px;
        padding: 5px;
        line-height: 1.5;
    """
    
    DOWNLOAD_BTN_STYLE = """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8c40;
        }
    """
    
    SETTINGS_BTN_STYLE = """
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
    """
    
    CANCEL_BTN_STYLE = """
        QPushButton {
            background-color: #757575;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #616161;
        }
        QPushButton:pressed {
            background-color: #424242;
        }
    """
    
    def __init__(self, parent: Optional[QDialog] = None, 
                 minecraft_version: str = "Unknown", 
                 required_java: str = "17"):
        """
        Inicializar ventana de error de Java.
        
        Args:
            parent: Widget padre
            minecraft_version: Versión de Minecraft que requiere Java
            required_java: Versión de Java requerida (8, 17, 21, etc.)
        """
        super().__init__(parent)
        
        self.minecraft_version = minecraft_version
        self.required_java = self._validate_java_version(required_java)
        self.auto_close_timer: Optional[QTimer] = None
        self.countdown_timer: Optional[QTimer] = None
        self.remaining_seconds = self.AUTO_CLOSE_TIME // 1000
        
        self._setup_ui()
        self._apply_effects()
        self._start_animations()
        self._setup_auto_close()
        
        # Centrar en pantalla
        self._center_on_screen()
    
    def _validate_java_version(self, version: str) -> str:
        """Validar y normalizar versión de Java"""
        version = str(version).strip()
        
        # Extraer solo números
        version_clean = ''.join(filter(str.isdigit, version))
        
        # Validar versiones conocidas
        if version_clean in self.JAVA_DOWNLOAD_URLS:
            return version_clean
        
        # Default a 17 si no es válida
        print(f"⚠️ Versión de Java no reconocida: {version}, usando 17 por defecto")
        return "17"
    
    def _setup_ui(self):
        """Configurar interfaz de usuario"""
        self.setWindowTitle("☕ Java no encontrado")
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(self.MAIN_STYLE)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # ===== Icono de advertencia =====
        self.warning_icon = QLabel(self.ICONS["java"])
        self.warning_icon.setFont(QFont("Segoe UI Emoji", 56))
        self.warning_icon.setStyleSheet(self.WARNING_ICON_STYLE)
        self.warning_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.warning_icon)
        
        # ===== Mensaje principal =====
        message_text = f"Se requiere Java {self.required_java}\npara Minecraft {self.minecraft_version}"
        self.message_label = QLabel(message_text)
        self.message_label.setStyleSheet(self.MESSAGE_STYLE)
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)
        
        # ===== Submensaje =====
        submessage_text = (
            "Por favor, instala la versión correcta de Java\n"
            "o selecciona otra versión de Minecraft compatible"
        )
        self.submessage_label = QLabel(submessage_text)
        self.submessage_label.setStyleSheet(self.SUBMESSAGE_STYLE)
        self.submessage_label.setAlignment(Qt.AlignCenter)
        self.submessage_label.setWordWrap(True)
        layout.addWidget(self.submessage_label)
        
        # ===== Contador de auto-cierre =====
        self.countdown_label = QLabel(f"Se cerrará en {self.remaining_seconds}s")
        self.countdown_label.setStyleSheet("color: #FFB900; font-size: 11px;")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.countdown_label)
        
        # ===== Botones =====
        self._create_buttons(layout)
        
        layout.addStretch()
    
    def _create_buttons(self, layout: QVBoxLayout):
        """Crear botones de acción"""
        # Botón descargar Java
        self.download_btn = QPushButton(f"☕ Descargar Java {self.required_java}")
        self.download_btn.setStyleSheet(self.DOWNLOAD_BTN_STYLE)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self._download_java)
        layout.addWidget(self.download_btn)
        
        # Botón ir a ajustes
        self.settings_btn = QPushButton("⚙️ Ir a Ajustes de Java")
        self.settings_btn.setStyleSheet(self.SETTINGS_BTN_STYLE)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self._go_to_settings)
        layout.addWidget(self.settings_btn)
        
        # Botón cancelar
        self.cancel_btn = QPushButton("✕ Cancelar")
        self.cancel_btn.setStyleSheet(self.CANCEL_BTN_STYLE)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.close)
        layout.addWidget(self.cancel_btn)
    
    def _apply_effects(self):
        """Aplicar efectos visuales (sombras)"""
        # Sombra principal del diálogo
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def _start_animations(self):
        """Iniciar animaciones de entrada"""
        # Animación de fade-in
        self.setWindowOpacity(0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
    
    def _setup_auto_close(self):
        """Configurar auto-cierre con countdown"""
        # Timer para cerrar
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.timeout.connect(self.close)
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.start(self.AUTO_CLOSE_TIME)
        
        # Timer para countdown
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.start(1000)  # Cada segundo
    
    def _update_countdown(self):
        """Actualizar contador de segundos"""
        self.remaining_seconds -= 1
        
        if self.remaining_seconds > 0:
            self.countdown_label.setText(f"Se cerrará en {self.remaining_seconds}s")
        else:
            self.countdown_label.setText("Cerrando...")
            if self.countdown_timer:
                self.countdown_timer.stop()
    
    def _center_on_screen(self):
        """Centrar ventana en la pantalla"""
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
        
        print(f"📥 Abriendo descarga de Java {self.required_java}: {url}")
        
        try:
            webbrowser.open(url)
            
            # Cambiar texto del botón
            self.download_btn.setText("✓ Navegador abierto")
            self.download_btn.setEnabled(False)
            
            # Cerrar después de 2 segundos
            QTimer.singleShot(2000, self.close)
            
        except Exception as e:
            print(f"❌ Error abriendo navegador: {e}")
            self.message_label.setText("Error al abrir navegador")
            self.message_label.setStyleSheet("color: #f44336; font-size: 13px;")
    
    def _go_to_settings(self):
        """Ir a ajustes (cerrar con código específico)"""
        print("⚙️ Abriendo ajustes de Java...")
        self.done(1)  # Código 1 = ir a ajustes
    
    def mousePressEvent(self, event):
        """Permitir arrastrar la ventana"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Mover ventana al arrastrar"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def closeEvent(self, event):
        """Cleanup al cerrar"""
        # Detener timers
        if self.auto_close_timer:
            self.auto_close_timer.stop()
        if self.countdown_timer:
            self.countdown_timer.stop()
        
        # Animación de fade-out
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)
        fade_out.finished.connect(lambda: event.accept())
        fade_out.start()
        
        event.ignore()  # Ignorar hasta que termine la animación
        QTimer.singleShot(200, lambda: super(JavaErrorWindow, self).close())
    
    # Propiedad para animación de opacidad
    @pyqtProperty(float)
    def opacity(self):
        return self.windowOpacity()
    
    @opacity.setter
    def opacity(self, value):
        self.setWindowOpacity(value)


# ===== FUNCIÓN DE CONVENIENCIA =====
def show_java_error(parent: Optional[QDialog] = None, 
                    mc_version: str = "Unknown", 
                    required_java: str = "17") -> int:
    """
    Mostrar diálogo de error de Java.
    
    Args:
        parent: Widget padre
        mc_version: Versión de Minecraft
        required_java: Versión de Java requerida
        
    Returns:
        0 si se cerró normalmente
        1 si se debe abrir ajustes
    """
    dialog = JavaErrorWindow(parent, mc_version, required_java)
    return dialog.exec_()


# Alias para compatibilidad
JavaVersionAlert = JavaErrorWindow


# ===== TESTING =====
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton
    
    app = QApplication(sys.argv)
    
    # Ventana de prueba
    window = QMainWindow()
    window.setWindowTitle("Java Error Window - Testing")
    window.setGeometry(100, 100, 800, 600)
    
    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setSpacing(20)
    layout.setContentsMargins(50, 50, 50, 50)
    
    # Título
    title = QLabel("<h1>☕ Testing Java Error Window</h1>")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)
    
    # Botones de prueba
    test_cases = [
        ("Minecraft 1.19.2 - Java 17", "1.19.2", "17"),
        ("Minecraft 1.16.5 - Java 8", "1.16.5", "8"),
        ("Minecraft 1.20.1 - Java 21", "1.20.1", "21"),
        ("Minecraft Unknown - Java 17", "Unknown", "17"),
    ]
    
    for label, mc_ver, java_ver in test_cases:
        btn = QPushButton(f"🧪 Test: {label}")
        btn.setMinimumHeight(50)
        btn.clicked.connect(
            lambda checked, m=mc_ver, j=java_ver: show_java_error(window, m, j)
        )
        layout.addWidget(btn)
    
    # Test con callback
    def test_with_callback():
        result = show_java_error(window, "1.19.4", "17")
        if result == 1:
            print("✓ Usuario quiere ir a ajustes")
        else:
            print("✓ Diálogo cerrado normalmente")
    
    btn_callback = QPushButton("🎯 Test con Callback")
    btn_callback.setMinimumHeight(50)
    btn_callback.clicked.connect(test_with_callback)
    layout.addWidget(btn_callback)
    
    layout.addStretch()
    
    window.setCentralWidget(central)
    
    # Estilo de la ventana principal
    window.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
        }
        QLabel {
            color: white;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8c40;
        }
    """)
    
    window.show()
    sys.exit(app.exec_())