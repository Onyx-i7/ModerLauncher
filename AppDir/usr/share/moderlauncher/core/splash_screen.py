"""
Splash Screen - Pantalla de carga inicial del launcher
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from utils.resource_manager import resource_path


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
        from core.launcher import MinecraftLauncher
        self.main_window = MinecraftLauncher()
        self.main_window.show()