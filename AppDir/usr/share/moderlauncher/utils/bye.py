from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QFont
from pygame import mixer
import os


class ByeWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.result = False
        self.drag_pos = QPoint()
        
        # Inicializar pygame mixer si no está inicializado
        if not mixer.get_init():
            mixer.init()
        
        # Configuración de ventana
        self.setFixedSize(300, 250)
        self.setup_ui()
        self.load_sounds()
        # Mover center_window al final del init
        self.center_window()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setStyleSheet("""
            QDialog {
                background-color: #161616;
                border: 2px solid #333333;
                border-radius: 10px;
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
            QPushButton {
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 10pt;
                min-width: 100px;
            }
            #btnNo {
                background-color: #4CAF50;
                color: white;
            }
            #btnNo:hover {
                background-color: #3d8c40;
            }
            #btnYes {
                background-color: #FF5252;
                color: white;
            }
            #btnYes:hover {
                background-color: #ff3333;
            }
        """)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Imagen
        img_label = QLabel()
        # Ir hacia atrás desde utils/ para llegar a assets/
        img_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'bye', 'bye.png')
        try:
            pixmap = QPixmap(img_path)
            pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pixmap)
        except:
            img_label.setText("ModerLauncher")
            img_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        
        img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)
        
        # Mensaje
        msg_label = QLabel("¿Quieres cerrar ModerLauncher?")
        msg_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        self.btn_no = QPushButton("No")
        self.btn_no.setObjectName("btnNo")
        self.btn_no.setCursor(Qt.PointingHandCursor)
        self.btn_no.clicked.connect(self.on_no)
        
        self.btn_yes = QPushButton("Sí")
        self.btn_yes.setObjectName("btnYes")
        self.btn_yes.setCursor(Qt.PointingHandCursor)
        self.btn_yes.clicked.connect(self.on_yes)
        
        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)
        
        layout.addLayout(btn_layout)
        
    def load_sounds(self):
        """Carga los archivos de sonido usando pygame mixer"""
        try:
            base_path = os.path.dirname(__file__)
            click_path = os.path.join(base_path, '..', 'sounds', 'click_botton.mp3')
            creeper_path = os.path.join(base_path, '..', 'sounds', 'creeper.mp3')
            
            self.click_sound = mixer.Sound(click_path)
            self.click_sound.set_volume(0.5)
            
            self.creeper_sound = mixer.Sound(creeper_path)
            self.creeper_sound.set_volume(0.5)
        except Exception as e:
            print(f"Error cargando sonidos: {e}")
            self.click_sound = None
            self.creeper_sound = None
    
    def on_no(self):
        """Acción del botón No"""
        try:
            if self.click_sound:
                self.click_sound.play()
        except:
            pass
        self.result = False
        self.close()
    
    def on_yes(self):
        """Acción del botón Sí"""
        try:
            if self.creeper_sound:
                self.creeper_sound.play()
                # Dar tiempo para que el sonido se reproduzca
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(800, self.close)
        except:
            self.close()
        self.result = True

    def center_window(self):
        """Centra la ventana en la pantalla"""
        if self.parent():
            parent_geo = self.parent().geometry()
            center = parent_geo.center()
            geo = self.geometry()
            geo.moveCenter(center)
            self.setGeometry(geo)
        else:
            # Si no hay padre, centrar en la pantalla
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.desktop().screenGeometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    # Hacer la ventana arrastrable
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()


def ask_quit(parent=None):
    """Función helper para mostrar el diálogo de confirmación"""
    try:
        # Asegurarse que mixer está inicializado
        if not mixer.get_init():
            mixer.init()
        
        # Intentar reproducir sonido de click
        try:
            base_path = os.path.dirname(__file__)
            click_path = os.path.join(base_path, '..', 'sounds', 'click_botton.mp3')
            click_sound = mixer.Sound(click_path)
            click_sound.set_volume(0.5)
            click_sound.play()
        except Exception as e:
            print(f"Error reproduciendo sonido: {e}")
        
        dialog = ByeWindow(parent)
        dialog.exec_()
        
        # Limpiar recursos de audio
        try:
            mixer.quit()
        except:
            pass
        
        return dialog.result
        
    except Exception as e:
        print(f"Error en ask_quit: {e}")
        return True  # En caso de error, permitir cerrar