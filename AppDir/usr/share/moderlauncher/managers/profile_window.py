import sys
import json
import os
import uuid
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from managers.auth_manager import AuthManager


# ==================== DIÁLOGO PERSONALIZADO ====================

class CustomDialog(QDialog):
    """Diálogo personalizado con estilo moderno"""
    def __init__(self, parent=None, title="", message="", dialog_type="info"):
        super().__init__(parent)
        self.dialog_type = dialog_type
        self.setup_ui(title, message)
        
    def setup_ui(self, title, message):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(450, 200)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Frame principal
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        
        # Colores según tipo
        colors = {
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FF9800",
            "info": "#2196F3"
        }
        
        accent_color = colors.get(self.dialog_type, "#2196F3")
        
        main_frame.setStyleSheet(f"""
            QFrame#mainFrame {{
                background-color: #2B2B2B;
                border-radius: 12px;
                border: 2px solid {accent_color};
            }}
        """)
        
        # Layout del frame
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(30, 25, 30, 25)
        frame_layout.setSpacing(15)
        
        # Header con línea de acento
        header_widget = QWidget()
        header_widget.setFixedHeight(4)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {accent_color};
                border-radius: 2px;
            }}
        """)
        frame_layout.addWidget(header_widget)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {accent_color};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                background: transparent;
                padding: 5px 0;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)
        
        # Mensaje
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 14px;
                font-family: 'Segoe UI', Arial;
                background: transparent;
                padding: 10px 0;
            }
        """)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        frame_layout.addWidget(message_label)
        
        frame_layout.addStretch()
        
        # Botón de cerrar
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        close_btn = QPushButton("Aceptar")
        close_btn.setFixedSize(120, 35)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                border-radius: 17px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }}
            QPushButton:hover {{
                background-color: {self.adjust_color(accent_color, -20)};
            }}
            QPushButton:pressed {{
                background-color: {self.adjust_color(accent_color, -40)};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        
        frame_layout.addWidget(button_container)
        
        layout.addWidget(main_frame)
        
        # Centrar en la ventana padre
        if self.parent():
            self.center_on_parent()
    
    def adjust_color(self, hex_color, brightness_offset):
        """Ajustar brillo del color"""
        color = QColor(hex_color)
        h, s, l, a = color.getHsl()
        l = max(0, min(255, l + brightness_offset))
        color.setHsl(h, s, l, a)
        return color.name()
    
    def center_on_parent(self):
        """Centrar diálogo en la ventana padre"""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.center().x() - self.width() // 2
            y = parent_rect.center().y() - self.height() // 2
            self.move(x, y)

    @staticmethod
    def show_message(parent, title, message, dialog_type="info"):
        """Método estático para mostrar el diálogo"""
        dialog = CustomDialog(parent, title, message, dialog_type)
        dialog.exec_()


class ConfirmDialog(QDialog):
    """Diálogo de confirmación personalizado"""
    def __init__(self, parent=None, title="", message=""):
        super().__init__(parent)
        self.setup_ui(title, message)
        
    def setup_ui(self, title, message):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(450, 200)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Frame principal
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: #2B2B2B;
                border-radius: 12px;
                border: 2px solid #FF9800;
            }
        """)
        
        # Layout del frame
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(30, 25, 30, 25)
        frame_layout.setSpacing(15)
        
        # Header con línea de acento
        header_widget = QWidget()
        header_widget.setFixedHeight(4)
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #FF9800;
                border-radius: 2px;
            }
        """)
        frame_layout.addWidget(header_widget)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #FF9800;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                background: transparent;
                padding: 5px 0;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)
        
        # Mensaje
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 14px;
                font-family: 'Segoe UI', Arial;
                background: transparent;
                padding: 10px 0;
            }
        """)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        frame_layout.addWidget(message_label)
        
        frame_layout.addStretch()
        
        # Botones
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15)
        
        # Botón Cancelar
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedSize(120, 35)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C41;
                color: white;
                border: none;
                border-radius: 17px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton:hover {
                background-color: #4A4A4E;
            }
            QPushButton:pressed {
                background-color: #2D2D30;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        # Botón Confirmar
        confirm_btn = QPushButton("Confirmar")
        confirm_btn.setFixedSize(120, 35)
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 17px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        confirm_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        button_layout.addStretch()
        
        frame_layout.addWidget(button_container)
        
        layout.addWidget(main_frame)
        
        # Centrar en la ventana padre
        if self.parent():
            self.center_on_parent()
    
    def center_on_parent(self):
        """Centrar diálogo en la ventana padre"""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.center().x() - self.width() // 2
            y = parent_rect.center().y() - self.height() // 2
            self.move(x, y)
    
    @staticmethod
    def ask(parent, title, message):
        """Método estático para mostrar el diálogo"""
        dialog = ConfirmDialog(parent, title, message)
        return dialog.exec_() == QDialog.Accepted


# ==================== WORKER PARA AUTENTICACIÓN ELY.BY ====================

class ElyAuthWorker(QThread):
    """Worker para autenticación Ely.by sin bloquear UI"""
    auth_success = pyqtSignal(dict)
    auth_failed = pyqtSignal(str)
    
    def __init__(self, login, password, auth_manager):
        super().__init__()
        self.login = login
        self.password = password
        self.auth_manager = auth_manager
    
    def run(self):
        try:
            result = self.auth_manager.create_ely_account(self.login, self.password)
            if result:
                self.auth_success.emit(result)
            else:
                self.auth_failed.emit("Credenciales inválidas o error de conexión")
        except Exception as e:
            self.auth_failed.emit(f"Error: {str(e)}")


# ==================== WORKER PARA AUTENTICACIÓN PREMIUM ====================

class PremiumAuthWorker(QThread):
    """Worker para autenticación premium sin bloquear UI"""
    auth_success = pyqtSignal(dict)
    auth_failed = pyqtSignal(str)
    
    def __init__(self, email, password, auth_manager):
        super().__init__()
        self.email = email
        self.password = password
        self.auth_manager = auth_manager
    
    def run(self):
        try:
            result = self.auth_manager.authenticate_premium(self.email, self.password)
            if result:
                self.auth_success.emit(result)
            else:
                self.auth_failed.emit("Credenciales inválidas o error de conexión")
        except Exception as e:
            self.auth_failed.emit(f"Error: {str(e)}")


# ==================== TARJETA DE PERFIL DE USUARIO ====================

class UserProfileCard(QFrame):
    """Tarjeta de perfil cuando hay usuario logueado"""
    logout_clicked = pyqtSignal()
    
    def __init__(self, account_data, parent=None):
        super().__init__(parent)
        self.account_data = account_data
        self.setup_ui()
    
    def setup_ui(self):
        # Tarjeta más ancha y horizontal
        self.setFixedSize(650, 260)
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 15px;
                border: 2px solid #4CAF50;
            }
        """)
        
        # Layout horizontal principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(35)
        
        # === SECCIÓN IZQUIERDA: Avatar ===
        left_section = QVBoxLayout()
        left_section.setSpacing(0)
        left_section.setAlignment(Qt.AlignCenter)
        
        avatar = QLabel("👤")
        avatar.setFixedSize(100, 100)
        avatar.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                border-radius: 50px;
                font-size: 50px;
                border: 3px solid #4CAF50;
            }
        """)
        avatar.setAlignment(Qt.AlignCenter)
        left_section.addWidget(avatar)
        
        main_layout.addLayout(left_section)
        
        # === SECCIÓN CENTRAL: Información del usuario ===
        center_section = QVBoxLayout()
        center_section.setSpacing(10)
        center_section.setAlignment(Qt.AlignVCenter)
        
        # Nombre de usuario
        username = QLabel(self.account_data.get("username", "Unknown"))
        username.setFont(QFont("Segoe UI", 24, QFont.Bold))
        username.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        center_section.addWidget(username)
        
        # Tipo de cuenta
        account_type = self.account_data.get("type", "offline")
        if account_type == "premium":
            type_text = "✨ Premium Account"
            type_color = "#FFD700"
        elif account_type == "ely":
            type_text = "🎨 Ely.by Account"
            type_color = "#2196F3"
        else:
            type_text = "⚡ Offline Account"
            type_color = "#4CAF50"

        type_label = QLabel(type_text)
        type_label.setFont(QFont("Segoe UI", 12))
        type_label.setStyleSheet(f"""
            QLabel {{
                color: {type_color};
                background: transparent;
                border: none;
            }}
        """)
        center_section.addWidget(type_label)
        
        # Email (solo para premium)
        if "email" in self.account_data:
            email = QLabel(self.account_data["email"])
            email.setFont(QFont("Segoe UI", 10))
            email.setStyleSheet("""
                QLabel {
                    color: #AAAAAA;
                    background: transparent;
                    border: none;
                }
            """)
            center_section.addWidget(email)
        
        main_layout.addLayout(center_section)
        
        # === SECCIÓN DERECHA: Botón de cerrar sesión ===
        right_section = QVBoxLayout()
        right_section.setAlignment(Qt.AlignCenter)
        
        logout_btn = QPushButton("🚪 Cerrar Sesión")
        logout_btn.setFixedSize(160, 50)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_clicked.emit)
        right_section.addWidget(logout_btn)
        
        main_layout.addLayout(right_section)


# ==================== VENTANA PRINCIPAL DE PERFIL ====================

class ProfileWindow(QWidget):
    """Ventana de gestión de perfil de usuario"""
    profile_updated = pyqtSignal()
    
    def __init__(self, parent, update_callback=None):
        super().__init__(parent)
        self.auth_manager = AuthManager()
        self.update_callback = update_callback
        self.current_account = self.auth_manager.get_current_account()
        
        # Ajustar al tamaño del parent
        if parent:
            self.setFixedSize(parent.width(), parent.height())
            self.setGeometry(0, 0, parent.width(), parent.height())
        
        self.setup_ui()
        self.setup_refresh_timer()
        self.show()  # Mostrar inmediatamente
    
    def setup_ui(self):
        """Crear interfaz de usuario"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: white;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(15)
        
        # Header
        self.create_header()
        
        # Contenido dinámico
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_container)
        
        # Cargar vista apropiada
        self.refresh_view()
    
    def create_header(self):
        """Crear header de la ventana"""
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 10px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Icono y título
        icon_title_layout = QVBoxLayout()
        
        title = QLabel("👤 Gestión de Perfil")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        icon_title_layout.addWidget(title)
        
        subtitle = QLabel("Administra tu cuenta de Minecraft")
        subtitle.setStyleSheet("color: #AAAAAA; font-size: 11px; background: transparent;")
        icon_title_layout.addWidget(subtitle)
        
        header_layout.addLayout(icon_title_layout)
        header_layout.addStretch()
        
        self.main_layout.addWidget(header)
    
    def refresh_view(self):
        """Actualizar vista según estado de autenticación"""
        # Limpiar contenido actual
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Recargar cuenta actual
        self.current_account = self.auth_manager.get_current_account()
        
        if self.current_account:
            # Mostrar perfil de usuario
            self.create_logged_in_view()
        else:
            # Mostrar formularios de login
            self.create_login_view()
    
    def create_logged_in_view(self):
        """Vista cuando hay usuario logueado"""
        # Centrar contenido
        spacer_top = QWidget()
        spacer_top.setFixedHeight(20)
        self.content_layout.addWidget(spacer_top)
        
        # Tarjeta de perfil
        profile_card = UserProfileCard(self.current_account, self)
        profile_card.logout_clicked.connect(self.logout)
        self.content_layout.addWidget(profile_card, alignment=Qt.AlignCenter)
        
        # Spacer inferior
        self.content_layout.addStretch()
    
    def create_login_view(self):
        """Vista de login con tabs profesionales"""
        # Tabs personalizadas
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background-color: #252526;
                border-radius: 0 8px 8px 8px;
                border: 1px solid #3C3C41;
            }
            QTabBar {
                background: transparent;
                qproperty-drawBase: 0;
            }
            QTabBar::tab {
                background-color: #2D2D30;
                color: #AAAAAA;
                padding: 18px 80px;
                min-width: 100px;
                min-height: 30px;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                margin-right: 8px;
            }
            QTabBar::tab:selected {
                background-color: #252526;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3C3C41;
                color: #DDDDDD;
            }
            QTabBar::tab:first:selected {
                border-bottom: 4px solid #FFD700;
            }
            QTabBar::tab:nth-child(2):selected {
                border-bottom: 4px solid #2196F3;
            }
            QTabBar::tab:last:selected {
                border-bottom: 4px solid #00BCD4;
            }
        """)
        
        # Tab Ely.by
        ely_tab = self.create_ely_tab()
        tab_widget.addTab(ely_tab, "ELY.BY")

        # Tab Premium
        premium_tab = self.create_premium_tab()
        tab_widget.addTab(premium_tab, "PREMIUM")
        
        # Tab Offline
        offline_tab = self.create_offline_tab()
        tab_widget.addTab(offline_tab, "OFFLINE")
        
        # Establecer la pestaña de Ely.by como la predeterminada
        tab_widget.setCurrentIndex(0)

        self.content_layout.addWidget(tab_widget)
    
    def create_premium_tab(self):
        """Crear pestaña premium con scroll"""
        # Widget contenedor con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2D2D30;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4A4A4E;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5A5A5E;
            }
        """)
        
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        
        # Layout principal
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)
        
        # Badge de estado
        badge = QLabel("Cuenta Original de Minecraft")
        badge.setFixedHeight(38)
        badge.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 215, 0, 0.15);
                color: #FFD700;
                padding: 0 25px;
                border-radius: 19px;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid rgba(255, 215, 0, 0.5);
            }
        """)
        badge.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(badge, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(40)
        
        # Formulario
        form_container = QWidget()
        form_container.setFixedWidth(460)
        form_container.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(0)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Email/Username
        email_label = QLabel("Email o Usuario")
        email_label.setFixedHeight(22)
        email_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                padding-left: 5px;
            }
        """)
        form_layout.addWidget(email_label)
        
        form_layout.addSpacing(10)
        
        self.premium_email = QLineEdit()
        self.premium_email.setPlaceholderText("nombre@ejemplo.com")
        self.premium_email.setFixedHeight(52)
        self.premium_email.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2A;
                color: white;
                border: 2px solid #3C3C41;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #FFD700;
                background-color: #2D2D30;
            }
            QLineEdit:hover {
                border-color: #4A4A4E;
            }
        """)
        form_layout.addWidget(self.premium_email)
        
        form_layout.addSpacing(24)
        
        # Password
        password_label = QLabel("Contraseña")
        password_label.setFixedHeight(22)
        password_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                padding-left: 5px;
            }
        """)
        form_layout.addWidget(password_label)
        
        form_layout.addSpacing(10)
        
        self.premium_password = QLineEdit()
        self.premium_password.setPlaceholderText("••••••••••••")
        self.premium_password.setEchoMode(QLineEdit.Password)
        self.premium_password.setFixedHeight(52)
        self.premium_password.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2A;
                color: white;
                border: 2px solid #3C3C41;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                letter-spacing: 2px;
            }
            QLineEdit:focus {
                border-color: #FFD700;
                background-color: #2D2D30;
            }
            QLineEdit:hover {
                border-color: #4A4A4E;
            }
        """)
        form_layout.addWidget(self.premium_password)
        
        main_layout.addWidget(form_container, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(20)
        
        # Status label
        self.premium_status = QLabel("")
        self.premium_status.setMinimumHeight(24)
        self.premium_status.setStyleSheet("""
            QLabel {
                color: #FF6B6B;
                font-size: 12px;
                background: transparent;
            }
        """)
        self.premium_status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.premium_status, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(16)
        
        # Botón
        self.premium_btn = QPushButton("Iniciar Sesión")
        self.premium_btn.setFixedSize(380, 52)
        self.premium_btn.setCursor(Qt.PointingHandCursor)
        self.premium_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: #1E1E1E;
                border: none;
                border-radius: 26px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFC700;
            }
            QPushButton:pressed {
                background-color: #E6B800;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        self.premium_btn.clicked.connect(self.login_premium)
        main_layout.addWidget(self.premium_btn, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(16)
        
        # Info
        info = QLabel("Inicia sesión con tu cuenta de Microsoft para jugar en servidores oficiales")
        info.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                background: transparent;
            }
        """)
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setMaximumWidth(400)
        main_layout.addWidget(info, alignment=Qt.AlignCenter)
        
        main_layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def create_offline_tab(self):
        """Crear pestaña offline con scroll"""
        # Widget contenedor con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2D2D30;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4A4A4E;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5A5A5E;
            }
        """)
        
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        
        # Layout principal
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)
        
        # Badge de advertencia
        badge = QLabel("Modo Solo Local")
        badge.setFixedHeight(38)
        badge.setStyleSheet("""
            QLabel {
                background-color: rgba(33, 150, 243, 0.15);
                color: #2196F3;
                padding: 0 25px;
                border-radius: 19px;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid rgba(33, 150, 243, 0.5);
            }
        """)
        badge.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(badge, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(40)
        
        # Formulario
        form_container = QWidget()
        form_container.setFixedWidth(460)
        form_container.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(0)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Username
        username_label = QLabel("Nombre de Usuario")
        username_label.setFixedHeight(22)
        username_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                padding-left: 5px;
            }
        """)
        form_layout.addWidget(username_label)
        
        form_layout.addSpacing(10)
        
        self.offline_username = QLineEdit()
        self.offline_username.setPlaceholderText("Steve")
        self.offline_username.setMaxLength(16)
        self.offline_username.setFixedHeight(52)
        self.offline_username.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2A;
                color: white;
                border: 2px solid #3C3C41;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
                background-color: #2D2D30;
            }
            QLineEdit:hover {
                border-color: #4A4A4E;
            }
        """)
        form_layout.addWidget(self.offline_username)
        
        form_layout.addSpacing(10)
        
        # Contador de caracteres
        self.char_counter = QLabel("0/16 caracteres")
        self.char_counter.setFixedHeight(18)
        self.char_counter.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 10px;
                background: transparent;
                padding-left: 5px;
            }
        """)
        form_layout.addWidget(self.char_counter)
        
        self.offline_username.textChanged.connect(
            lambda text: self.char_counter.setText(f"{len(text)}/16 caracteres")
        )
        
        main_layout.addWidget(form_container, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(26)
        
        # Botón
        offline_btn = QPushButton("Crear Cuenta")
        offline_btn.setFixedSize(380, 52)
        offline_btn.setCursor(Qt.PointingHandCursor)
        offline_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 26px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        offline_btn.clicked.connect(self.create_offline_account)
        main_layout.addWidget(offline_btn, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(16)
        
        # Info
        info = QLabel("Perfecta para jugar en modo individual o en partidas LAN locales")
        info.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                background: transparent;
            }
        """)
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setMaximumWidth(400)
        main_layout.addWidget(info, alignment=Qt.AlignCenter)
        
        main_layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll

    def create_ely_tab(self):
        """Crear pestaña de Ely.by con scroll"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #2D2D30; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #4A4A4E; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background: #5A5A5E; }
        """)
        
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)
        
        badge = QLabel("Inicia sesión con tu cuenta de Ely.by")
        badge.setFixedHeight(38)
        badge.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 188, 212, 0.15);
                color: #00BCD4;
                padding: 0 25px;
                border-radius: 19px;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid rgba(0, 188, 212, 0.5);
            }
        """)
        badge.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(badge, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(40)
        
        form_container = QWidget()
        form_container.setFixedWidth(460)
        form_container.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(0)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Email o Usuario
        username_label = QLabel("Email o Usuario de Ely.by")
        username_label.setFixedHeight(22)
        username_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC; font-size: 13px; font-weight: 600;
                background: transparent; padding-left: 5px;
            }
        """)
        form_layout.addWidget(username_label)
        
        form_layout.addSpacing(10)
        
        self.ely_username = QLineEdit()
        self.ely_username.setPlaceholderText("tu_email@ejemplo.com o TuUsuarioDeEly")
        self.ely_username.setFixedHeight(52)
        self.ely_username.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2A; color: white;
                border: 2px solid #3C3C41; border-radius: 8px;
                padding: 0 18px; font-size: 14px;
            }
            QLineEdit:focus { border-color: #00BCD4; background-color: #2D2D30; }
            QLineEdit:hover { border-color: #4A4A4E; }
        """)
        form_layout.addWidget(self.ely_username)
        
        form_layout.addSpacing(24)
        
        # Contraseña
        password_label = QLabel("Contraseña")
        password_label.setFixedHeight(22)
        password_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC; font-size: 13px; font-weight: 600;
                background: transparent; padding-left: 5px;
            }
        """)
        form_layout.addWidget(password_label)
        
        form_layout.addSpacing(10)
        
        self.ely_password = QLineEdit()
        self.ely_password.setPlaceholderText("••••••••••••")
        self.ely_password.setEchoMode(QLineEdit.Password)
        self.ely_password.setFixedHeight(52)
        self.ely_password.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2A; color: white;
                border: 2px solid #3C3C41; border-radius: 8px;
                padding: 0 18px; font-size: 14px;
                letter-spacing: 2px;
            }
            QLineEdit:focus { border-color: #00BCD4; background-color: #2D2D30; }
            QLineEdit:hover { border-color: #4A4A4E; }
        """)
        form_layout.addWidget(self.ely_password)
        
        main_layout.addWidget(form_container, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(20)
        
        # Status label
        self.ely_status = QLabel("")
        self.ely_status.setMinimumHeight(24)
        self.ely_status.setStyleSheet("""
            QLabel {
                color: #FF6B6B;
                font-size: 12px;
                background: transparent;
            }
        """)
        self.ely_status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.ely_status, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(16)
        
        self.ely_btn = QPushButton("Iniciar Sesión")
        self.ely_btn.setFixedSize(380, 52)
        self.ely_btn.setCursor(Qt.PointingHandCursor)
        self.ely_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4; color: white;
                border: none; border-radius: 26px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #00ACC1; }
            QPushButton:pressed { background-color: #0097A7; }
        """)
        self.ely_btn.clicked.connect(self.login_ely)
        main_layout.addWidget(self.ely_btn, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(16)
        
        info = QLabel("Inicia sesión con tu cuenta de Ely.by para usar tu skin y jugar en servidores compatibles.")
        info.setStyleSheet("""
            QLabel {
                color: #888888; font-size: 11px;
                background: transparent;
            }
        """)
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setMaximumWidth(400)
        main_layout.addWidget(info, alignment=Qt.AlignCenter)
        
        main_layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def setup_refresh_timer(self):
        """Configurar timer de actualización"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.check_account_changes)
        self.refresh_timer.start(1000)
    
    def check_account_changes(self):
        """Verificar si cambió la cuenta"""
        current = self.auth_manager.get_current_account()
        if current != self.current_account:
            self.current_account = current
            self.refresh_view()
            if self.update_callback:
                self.update_callback()
    
    def login_premium(self):
        """Iniciar sesión premium"""
        email = self.premium_email.text().strip()
        password = self.premium_password.text()
        
        if not email or not password:
            self.premium_status.setText("⚠️ Completa todos los campos")
            return
        
        self.premium_btn.setEnabled(False)
        self.premium_status.setText("🔄 Autenticando...")
        self.premium_status.setStyleSheet("color: #FFD700; font-size: 12px; background: transparent;")
        
        self.auth_worker = PremiumAuthWorker(email, password, self.auth_manager)
        self.auth_worker.auth_success.connect(self.on_premium_success)
        self.auth_worker.auth_failed.connect(self.on_premium_failed)
        self.auth_worker.start()
    
    def on_premium_success(self, account_data):
        """Callback de éxito en login premium"""
        self.premium_btn.setEnabled(True)
        self.premium_status.setText("✓ Inicio de sesión exitoso")
        self.premium_status.setStyleSheet("color: #4CAF50; font-size: 12px; background: transparent;")
        
        self.premium_email.clear()
        self.premium_password.clear()
        
        if self.update_callback:
            self.update_callback()
        
        self.refresh_view()
        
        # Usar diálogo personalizado
        CustomDialog.show_message(
            self, 
            "Sesión Iniciada",
            f"Has iniciado sesión correctamente con tu cuenta Premium",
            "success"
        )
        
        self.profile_updated.emit()
    
    def on_premium_failed(self, error_msg):
        """Callback de error en login premium"""
        self.premium_btn.setEnabled(True)
        self.premium_status.setText(f"❌ {error_msg}")
        self.premium_status.setStyleSheet("color: #FF6B6B; font-size: 12px; background: transparent;")
    
    def create_offline_account(self):
        """Crear cuenta offline"""
        username = self.offline_username.text().strip()
        
        if not username:
            CustomDialog.show_message(
                self,
                "Campo Vacío",
                "Por favor ingresa un nombre de usuario",
                "warning"
            )
            return
        
        if len(username) < 3:
            CustomDialog.show_message(
                self,
                "Nombre Inválido",
                "El nombre debe tener al menos 3 caracteres",
                "warning"
            )
            return
        
        if len(username) > 16:
            CustomDialog.show_message(
                self,
                "Nombre Inválido",
                "El nombre no puede tener más de 16 caracteres",
                "warning"
            )
            return
        
        if not all(c.isalnum() or c == '_' for c in username):
            CustomDialog.show_message(
                self,
                "Caracteres Inválidos",
                "Solo se permiten letras, números y guiones bajos (_)",
                "warning"
            )
            return
        
        try:
            result = self.auth_manager.create_offline_account(username)
            
            if result:
                self.offline_username.clear()
                
                if self.update_callback:
                    self.update_callback()
                
                self.refresh_view()
                
                # Usar diálogo personalizado
                CustomDialog.show_message(
                    self,
                    "Cuenta Creada",
                    f"La cuenta '{username}' ha sido creada exitosamente",
                    "success"
                )
                
                self.profile_updated.emit()
            else:
                CustomDialog.show_message(
                    self,
                    "Error",
                    "No se pudo crear la cuenta",
                    "error"
                )
        
        except Exception as e:
            CustomDialog.show_message(
                self,
                "Error",
                f"Error: {str(e)}",
                "error"
            )
    
    def login_ely(self):
        """Iniciar sesión con Ely.by usando credenciales"""
        login = self.ely_username.text().strip()
        password = self.ely_password.text()

        if not login or not password:
            self.ely_status.setText("⚠️ Completa todos los campos")
            self.ely_status.setStyleSheet("color: #FF6B6B; font-size: 12px; background: transparent;")
            return

        self.ely_btn.setEnabled(False)
        self.ely_status.setText("🔄 Autenticando...")
        self.ely_status.setStyleSheet("color: #00BCD4; font-size: 12px; background: transparent;")

        self.ely_auth_worker = ElyAuthWorker(login, password, self.auth_manager)
        self.ely_auth_worker.auth_success.connect(self.on_ely_auth_success)
        self.ely_auth_worker.auth_failed.connect(self.on_ely_auth_failed)
        self.ely_auth_worker.start()

    def on_ely_auth_success(self, account_data):
        """Callback de éxito en login Ely.by"""
        self.ely_btn.setEnabled(True)
        self.ely_status.setText("✓ Inicio de sesión exitoso")
        self.ely_status.setStyleSheet("color: #4CAF50; font-size: 12px; background: transparent;")
        self.ely_username.clear()
        self.ely_password.clear()
        
        if self.update_callback: 
            self.update_callback()
        
        self.refresh_view()
        
        # Usar diálogo personalizado
        CustomDialog.show_message(
            self,
            "Sesión Iniciada",
            f"Has iniciado sesión como '{account_data['username']}' con Ely.by",
            "success"
        )
        
        self.profile_updated.emit()

    def on_ely_auth_failed(self, error_msg):
        """Callback de error en login Ely.by"""
        self.ely_btn.setEnabled(True)
        self.ely_status.setText(f"❌ {error_msg}")
        self.ely_status.setStyleSheet("color: #FF6B6B; font-size: 12px; background: transparent;")

    def logout(self):
        """Cerrar sesión"""
        # Usar diálogo de confirmación personalizado
        if ConfirmDialog.ask(self, "Cerrar Sesión", "¿Estás seguro de que deseas cerrar sesión?"):
            if self.auth_manager.logout():
                if self.update_callback:
                    self.update_callback()
                
                self.refresh_view()
                
                # Usar diálogo personalizado
                CustomDialog.show_message(
                    self,
                    "Sesión Cerrada",
                    "Tu sesión ha sido cerrada correctamente",
                    "info"
                )
                
                self.profile_updated.emit()
            else:
                CustomDialog.show_message(
                    self,
                    "Error",
                    "Hubo un error al cerrar la sesión",
                    "error"
                )