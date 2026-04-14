from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os

class CustomMessageBox(QDialog):
    def __init__(self, icon_path=None, title="", text="", accept_text="Aceptar", cancel_text=None, parent=None):
        super().__init__(parent)
        
        # Configuración básica
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(400)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container principal con bordes redondeados
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #252526;
                border: 2px solid #3C3C41;
                border-radius: 10px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # Header con título
        header = QLabel(title)
        header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }
        """)
        container_layout.addWidget(header)
        
        # Contenido
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # Icono
        if icon_path and os.path.exists(icon_path):
            icon = QLabel()
            pixmap = QPixmap(icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon.setPixmap(pixmap)
            content_layout.addWidget(icon)
        
        # Mensaje
        message = QLabel(text)
        message.setWordWrap(True)
        message.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 14px;
                font-family: 'Segoe UI';
            }
        """)
        content_layout.addWidget(message, 1)
        container_layout.addWidget(content)
        
        # Botones
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        button_style = """
            QPushButton {
                background-color: #2D2D30;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 14px;
                font-family: 'Segoe UI';
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3E3E42;
            }
            QPushButton:pressed {
                background-color: #0E639C;
            }
            QPushButton#accept {
                background-color: #0E639C;
            }
            QPushButton#accept:hover {
                background-color: #1177BB;
            }
        """
        
        # Agregar botón de cancelar si se especificó
        if cancel_text:
            cancel_btn = QPushButton(cancel_text)
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.setStyleSheet(button_style)
            cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        # Botón de aceptar
        accept_btn = QPushButton(accept_text)
        accept_btn.setObjectName("accept")
        accept_btn.setCursor(Qt.PointingHandCursor)
        accept_btn.setStyleSheet(button_style)
        accept_btn.clicked.connect(self.accept)
        button_layout.addWidget(accept_btn)
        
        container_layout.addWidget(button_container)
        layout.addWidget(container)
        
        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 100))
        container.setGraphicsEffect(shadow)
        
        # Centrar en la pantalla padre
        if parent:
            center = parent.geometry().center()
            geo = self.geometry()
            geo.moveCenter(center)
            self.setGeometry(geo)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()
