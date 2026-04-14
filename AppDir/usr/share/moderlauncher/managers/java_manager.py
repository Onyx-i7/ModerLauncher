import sys
import os
import json
import psutil
import webbrowser
import subprocess
import shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class JavaManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.java_paths = []
    
    def find_java_installations(self, show_progress=False):
        java_search_paths = [
            "C:/Program Files/Java",
            "C:/Program Files (x86)/Java",
            "C:/Program Files/Eclipse Adoptium",
            "C:/Program Files/Eclipse Foundation",
            "C:/Program Files/BellSoft",
            "C:/Program Files/Zulu",
            os.path.expanduser("~/AppData/Local/Programs/Eclipse Adoptium"),
            os.path.expanduser("~/AppData/Local/Programs/Eclipse Foundation")
        ]

        if os.name != 'nt':
            java_search_paths += [
                "/usr/bin",
                "/usr/local/bin",
                "/usr/lib/jvm",
                "/usr/lib/jvm/default-java/bin",
                "/usr/lib/jvm/java-11-openjdk-amd64/bin",
                "/usr/lib/jvm/java-17-openjdk-amd64/bin"
            ]

        java_paths = []
        for search_path in java_search_paths:
            if os.path.exists(search_path):
                try:
                    candidates = []
                    if os.path.isfile(search_path):
                        candidates.append(search_path)
                    elif os.path.isdir(search_path):
                        if os.name == 'nt':
                            for java_dir in os.listdir(search_path):
                                candidates.append(os.path.join(search_path, java_dir, "bin", "java.exe"))
                        else:
                            candidates.append(os.path.join(search_path, "java"))
                            for java_dir in os.listdir(search_path):
                                candidate_dir = os.path.join(search_path, java_dir)
                                if os.path.isdir(candidate_dir):
                                    candidates.append(os.path.join(candidate_dir, "bin", "java"))

                    for java_path in candidates:
                        if os.path.exists(java_path):
                            version = self.get_java_version(java_path)
                            if version:
                                java_paths.append((version, java_path))
                except:
                    continue

        java_bin = shutil.which('java')
        if java_bin:
            version = self.get_java_version(java_bin)
            if version:
                java_paths.append((version, java_bin))

        return java_paths

    def get_java_version(self, java_path):
        try:
            result = subprocess.run(
                [java_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=5
            )
            version_output = result.stderr
            if "version" in version_output:
                return version_output.split('\n')[0]
            return None
        except:
            return None


class ModernSettingsCard(QFrame):
    """Tarjeta moderna para cada sección de configuración"""
    def __init__(self, title, description="", parent=None):
        super().__init__(parent)
        self.setObjectName("settingsCard")
        # REMOVIDO: restricciones de altura mínima/máxima
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setup_ui(title, description)
    
    def setup_ui(self, title, description):
        self.setStyleSheet("""
            QFrame#settingsCard {
                background-color: #252525;
                border-radius: 10px;
                border: 1px solid #3C3C41;
            }
            QFrame#settingsCard:hover {
                border-color: #4CAF50;
                background-color: #2A2A2A;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(10)
        
        # Header
        header = QLabel(title)
        header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        header.setStyleSheet("color: white; background: transparent; border: none;")
        layout.addWidget(header)
        
        # Description
        if description:
            desc = QLabel(description)
            desc.setFont(QFont("Segoe UI", 8))
            desc.setStyleSheet("color: #888888; background: transparent; border: none;")
            desc.setWordWrap(True)
            layout.addWidget(desc)
        
        # Content container
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        layout.addLayout(self.content_layout)
        
        layout.addStretch()


class CompactSlider(QWidget):
    """Slider compacto con etiquetas"""
    valueChanged = pyqtSignal(int)
    
    def __init__(self, min_val, max_val, current_val, suffix="", parent=None):
        super().__init__(parent)
        self.suffix = suffix
        self.setup_ui(min_val, max_val, current_val)
    
    def setup_ui(self, min_val, max_val, current_val):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Value display
        self.value_label = QLabel(f"{current_val}{self.suffix}")
        self.value_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.value_label.setStyleSheet("color: #4CAF50; background: transparent;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Slider container
        slider_container = QHBoxLayout()
        slider_container.setSpacing(8)
        
        # Min label
        min_label = QLabel(str(min_val))
        min_label.setStyleSheet("color: #666666; font-size: 9px; background: transparent;")
        slider_container.addWidget(min_label)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(current_val)
        self.slider.setFixedHeight(22)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #1E1E1E;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #66BB6A;
                width: 20px;
                height: 20px;
                margin: -6px 0;
            }
            QSlider::add-page:horizontal {
                background: #1E1E1E;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #66BB6A);
                border-radius: 4px;
            }
        """)
        self.slider.valueChanged.connect(self.on_value_changed)
        slider_container.addWidget(self.slider)
        
        # Max label
        max_label = QLabel(str(max_val))
        max_label.setStyleSheet("color: #666666; font-size: 9px; background: transparent;")
        slider_container.addWidget(max_label)
        
        layout.addLayout(slider_container)
    
    def on_value_changed(self, value):
        self.value_label.setText(f"{value}{self.suffix}")
        self.valueChanged.emit(value)
    
    def value(self):
        return self.slider.value()
    
    def setValue(self, value):
        self.slider.setValue(value)


class SettingsWindow(QWidget):
    def __init__(self, parent=None, click_sound_callback=None):
        super().__init__(parent)
        self.click_sound_callback = click_sound_callback
        
        # CRÍTICO: Configurar para ocupar todo el espacio del parent
        if parent:
            self.setGeometry(0, 0, parent.width(), parent.height())
        self.system_ram = self.get_system_ram()
        self.cpu_cores = psutil.cpu_count()
        
        # Java versions data
        self.java_versions = {
            "Java 17 (MC 1.17+)": {
                "versions": ["1.17", "1.18", "1.19", "1.20"],
                "path": "",
                "min_version": "1.17",
                "download": "https://adoptium.net/temurin/releases/?version=17"
            },
            "Java 8 (MC 1.1-1.16)": {
                "versions": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", 
                           "1.9", "1.10", "1.11", "1.12", "1.13", "1.14", "1.15", "1.16"],
                "path": "",
                "min_version": "1.1",
                "download": "https://adoptium.net/temurin/releases/?version=8"
            }
        }
        
        self.load_settings()
        self.detect_java_installations()
        self.setup_ui()
    
    def get_system_ram(self):
        """Obtiene la RAM total del sistema en MB"""
        try:
            return int(psutil.virtual_memory().total / (1024 * 1024))
        except:
            return 4096
    
    def load_settings(self):
        """Carga o crea las configuraciones por defecto"""
        default_settings = {
            'ram': 2048,
            'java_path': '',
            'jvm_args': '-XX:+UseG1GC -XX:+ParallelRefProcEnabled',
            'language': 'es',
            'install_path': os.path.expanduser('~/.minecraft'),
            'compatibility_mode': False,
            'display_mode': 'window',
            'cpu_cores': psutil.cpu_count(),
            'process_priority': 'normal',
            'selected_java': '',
        }
        
        try:
            with open('settings.json', 'r') as f:
                self.settings = {**default_settings, **json.load(f)}
        except:
            self.settings = default_settings
    

    def setup_ui(self):
        # Asegurar que el widget ocupe todo el espacio
        self.setMinimumSize(1120, 668)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: white;
                font-family: 'Segoe UI';
            }
            QLabel {
                background: transparent;
            }
            QComboBox {
                background-color: #2A2A2A;
                border: 2px solid #3C3C41;
                border-radius: 6px;
                padding: 7px 10px;
                color: white;
                font-size: 10px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #4CAF50;
            }
            QComboBox:focus {
                border-color: #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2A2A2A;
                color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
                border: 1px solid #3C3C41;
                outline: none;
            }
            QLineEdit {
                background-color: #2A2A2A;
                border: 2px solid #3C3C41;
                border-radius: 6px;
                padding: 7px 10px;
                color: white;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QRadioButton {
                color: white;
                spacing: 8px;
                background: transparent;
                font-size: 10px;
                padding: 3px 0;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #3C3C41;
                background-color: #2A2A2A;
            }
            QRadioButton::indicator:hover {
                border-color: #4CAF50;
            }
            QRadioButton::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
            QPushButton#secondaryBtn {
                background-color: #2196F3;
                padding: 6px 12px;
                font-size: 9px;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #42A5F5;
            }
            QPushButton#secondaryBtn:pressed {
                background-color: #1976D2;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)  # Márgenes más amplios
        main_layout.setSpacing(20)  # Más espacio entre elementos
        
        # Header (tarjeta verde superior)
        self.create_header(main_layout)
        
        # Grid para las tarjetas (2 filas x 3 columnas)
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)  # Más espacio horizontal
        grid.setVerticalSpacing(20)    # Más espacio vertical
        grid.setContentsMargins(0, 0, 0, 0)
        
        # IMPORTANTE: Las columnas deben tener el mismo peso
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        
        # IMPORTANTE: Las filas deben tener el mismo peso
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        
        # Create cards
        self.ram_card = self.create_ram_card()
        self.java_card = self.create_java_card()
        self.cpu_card = self.create_cpu_card()
        self.display_card = self.create_display_card()
        self.language_card = self.create_language_card()
        self.priority_card = self.create_priority_card()
        
        # Add to grid (2 filas x 3 columnas)
        grid.addWidget(self.ram_card, 0, 0)
        grid.addWidget(self.java_card, 0, 1)
        grid.addWidget(self.cpu_card, 0, 2)
        grid.addWidget(self.display_card, 1, 0)
        grid.addWidget(self.language_card, 1, 1)
        grid.addWidget(self.priority_card, 1, 2)
        
        main_layout.addLayout(grid, stretch=1)
        
        # Save button (tarjeta verde inferior)
        self.create_save_button(main_layout)
    
    def create_header(self, parent_layout):
        """Crear header"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-radius: 10px;
                border: 1px solid #3C3C41;
            }
        """)
        header.setFixedHeight(70)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Title
        title = QLabel("⚙️ Configuración del Launcher")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent; border: none;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # System info
        info = QLabel(f"💻 {self.system_ram}MB RAM | 🔧 {self.cpu_cores} Núcleos")
        info.setFont(QFont("Segoe UI", 9))
        info.setStyleSheet("color: #888888; background: transparent; border: none;")
        header_layout.addWidget(info)
        
        parent_layout.addWidget(header)
    
    def create_ram_card(self):
        """Tarjeta de configuración RAM"""
        card = ModernSettingsCard(
            "🔧 Memoria RAM",
            f"Sistema: {self.system_ram}MB"
        )
        
        # Slider
        max_ram = min(self.system_ram, 16384)
        self.ram_slider = CompactSlider(
            1024, max_ram, self.settings['ram'], "MB"
        )
        self.ram_slider.valueChanged.connect(self.on_ram_changed)
        card.content_layout.addWidget(self.ram_slider)
        
        # GB indicator
        gb_label = QLabel()
        gb_label.setFont(QFont("Segoe UI", 9))
        gb_label.setStyleSheet("color: #888888;")
        gb_label.setAlignment(Qt.AlignCenter)
        self.ram_gb_label = gb_label
        self.on_ram_changed(self.settings['ram'])
        card.content_layout.addWidget(gb_label)
        
        return card
    
    def create_java_card(self):
        """Tarjeta de configuración Java"""
        card = ModernSettingsCard(
            "☕ Java",
            "Versión según Minecraft"
        )
        
        # Java selector
        java_layout = QHBoxLayout()
        java_layout.setSpacing(8)
        
        self.java_combo = QComboBox()
        self.java_combo.addItems(list(self.java_versions.keys()))
        selected_java = self.settings.get('selected_java', '')
        if selected_java in self.java_versions.keys():
            self.java_combo.setCurrentText(selected_java)
        java_layout.addWidget(self.java_combo)
        
        download_btn = QPushButton("⬇")
        download_btn.setObjectName("secondaryBtn")
        download_btn.setFixedWidth(35)
        download_btn.setToolTip("Descargar Java")
        download_btn.clicked.connect(self.download_java)
        download_btn.setCursor(Qt.PointingHandCursor)
        java_layout.addWidget(download_btn)
        
        card.content_layout.addLayout(java_layout)
        
        # JVM Arguments
        self.jvm_entry = QLineEdit()
        self.jvm_entry.setText(self.settings.get('jvm_args', '-XX:+UseG1GC'))
        self.jvm_entry.setPlaceholderText("Argumentos JVM")
        card.content_layout.addWidget(self.jvm_entry)
        
        return card
    
    def create_cpu_card(self):
        """Tarjeta de configuración CPU"""
        card = ModernSettingsCard(
            "⚙️ Núcleos del CPU",
            f"Total: {self.cpu_cores} núcleos"
        )
        
        # Slider
        self.cpu_slider = CompactSlider(
            1, self.cpu_cores, 
            self.settings.get('cpu_cores', self.cpu_cores), 
            " núcleos"
        )
        self.cpu_slider.valueChanged.connect(self.on_cpu_changed)
        card.content_layout.addWidget(self.cpu_slider)
        
        # Percentage
        percent_label = QLabel()
        percent_label.setFont(QFont("Segoe UI", 9))
        percent_label.setStyleSheet("color: #888888;")
        percent_label.setAlignment(Qt.AlignCenter)
        self.cpu_percent_label = percent_label
        self.on_cpu_changed(self.settings.get('cpu_cores', self.cpu_cores))
        card.content_layout.addWidget(percent_label)
        
        return card
    
    def create_display_card(self):
        """Tarjeta de modo de pantalla"""
        card = ModernSettingsCard(
            "📺 Modo de Pantalla",
            "Visualización del juego"
        )
        
        self.display_group = QButtonGroup()
        
        modes = [
            ("🪟 Ventana", "window"),
            ("🖥️ Pantalla Completa", "fullscreen"),
            ("🎯 Sin Bordes", "borderless")
        ]
        
        for i, (text, value) in enumerate(modes):
            rb = QRadioButton(text)
            rb.setProperty("value", value)
            if value == self.settings.get('display_mode', 'window'):
                rb.setChecked(True)
            self.display_group.addButton(rb, i)
            card.content_layout.addWidget(rb)
        
        return card
    
    def create_language_card(self):
        """Tarjeta de idioma"""
        card = ModernSettingsCard(
            "🌐 Idioma",
            "Idioma del launcher"
        )
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(['Español', 'English'])
        self.language_combo.setCurrentText(
            'Español' if self.settings['language'] == 'es' else 'English'
        )
        card.content_layout.addWidget(self.language_combo)
        
        # Icono de bandera
        flag_label = QLabel("🇪🇸 Español" if self.settings['language'] == 'es' else "🇺🇸 English")
        flag_label.setFont(QFont("Segoe UI", 10))
        flag_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        flag_label.setAlignment(Qt.AlignCenter)
        card.content_layout.addWidget(flag_label)
        
        # Conectar cambio
        self.language_combo.currentTextChanged.connect(
            lambda text: flag_label.setText("🇪🇸 Español" if text == 'Español' else "🇺🇸 English")
        )
        
        return card
    
    def create_priority_card(self):
        """Tarjeta de prioridad del proceso"""
        card = ModernSettingsCard(
            "🗂️ Prioridad",
            "Nivel de prioridad"
        )
        
        self.priority_group = QButtonGroup()
        
        priorities = [
            ("⬇️ Baja", "low"),
            ("⭐ Normal", "normal"),
            ("⬆️ Alta", "high"),
            ("⚡ Tiempo Real", "realtime")
        ]
        
        for i, (text, value) in enumerate(priorities):
            rb = QRadioButton(text)
            rb.setProperty("value", value)
            if value == self.settings.get('process_priority', 'normal'):
                rb.setChecked(True)
            self.priority_group.addButton(rb, i)
            card.content_layout.addWidget(rb)
        
        return card
    
    def create_save_button(self, parent_layout):
        """Botón de guardar"""
        button_container = QWidget()
        button_container.setFixedHeight(60)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.setFixedSize(240, 50)
        save_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        save_btn.clicked.connect(self.save_all)
        save_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(save_btn, alignment=Qt.AlignCenter)
        
        parent_layout.addWidget(button_container)
    
    def on_ram_changed(self, value):
        """Callback para cambio de RAM"""
        gb = value / 1024
        self.ram_gb_label.setText(f"≈ {gb:.1f} GB")
    
    def on_cpu_changed(self, value):
        """Callback para cambio de CPU"""
        percent = (value / self.cpu_cores) * 100
        self.cpu_percent_label.setText(f"{percent:.0f}% de CPU")
    
    def detect_java_installations(self):
        """Detecta las instalaciones de Java en el sistema"""
        java_search_paths = [
            "C:/Program Files/Java",
            "C:/Program Files (x86)/Java",
            "C:/Program Files/Eclipse Adoptium",
            "C:/Program Files/Eclipse Foundation",
            "C:/Program Files/BellSoft",
            "C:/Program Files/Zulu",
            os.path.expanduser("~/AppData/Local/Programs/Eclipse Adoptium"),
            os.path.expanduser("~/AppData/Local/Programs/Eclipse Foundation")
        ]
        
        for version in self.java_versions:
            self.java_versions[version]["path"] = ""

        for search_path in java_search_paths:
            if os.path.exists(search_path):
                try:
                    for java_dir in os.listdir(search_path):
                        java_path = os.path.join(search_path, java_dir, "bin", "java.exe")
                        if os.path.exists(java_path):
                            version_info = self.get_java_version(java_path)
                            if version_info:
                                for java_ver, data in self.java_versions.items():
                                    if version_info in java_ver and not data["path"]:
                                        data["path"] = java_path
                                        break
                except:
                    pass
    
    def get_java_version(self, java_path):
        """Obtiene la versión de Java de una instalación"""
        try:
            result = subprocess.run(
                [java_path, "-version"], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=10
            )
            version_output = result.stderr
            if "version" in version_output:
                if "17" in version_output:
                    return "17"
                elif "1.8" in version_output or '"8' in version_output:
                    return "8"
        except:
            pass
        return None
    
    def download_java(self):
        """Abre el enlace de descarga para Java"""
        selected = self.java_combo.currentText()
        if selected in self.java_versions:
            webbrowser.open(self.java_versions[selected]["download"])
    
    def save_all(self):
        """Guardar toda la configuración"""
        if self.click_sound_callback:
            self.click_sound_callback()
        try:
            settings = {
                'ram': self.ram_slider.value(),
                'java_versions': {
                    "Java 8 (Minecraft 1.1 - 1.16.5)": None,
                    "Java 17 (Minecraft 1.17 - 1.20.4)": None
                },
                'jvm_args': self.jvm_entry.text(),
                'language': 'es' if self.language_combo.currentText() == 'Español' else 'en',
                'cpu_cores': self.cpu_slider.value(),
                'process_priority': 'normal'
            }

            # Detectar instalaciones de Java
            java_manager = JavaManager(self)
            java_paths = java_manager.find_java_installations(show_progress=True)
            for version, path in java_paths:
                if "1.8" in version or "8" in version:
                    settings['java_versions']["Java 8 (Minecraft 1.1 - 1.16.5)"] = path
                elif "17" in version:
                    settings['java_versions']["Java 17 (Minecraft 1.17 - 1.20.4)"] = path

            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

            QMessageBox.information(self, "✅ Guardado", "Configuración guardada correctamente")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando configuración:\n{str(e)}")


# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Ventana principal
    window = QMainWindow()
    window.setWindowTitle("Configuración - ModernLauncher")
    window.setGeometry(100, 100, 1200, 700)
    window.setStyleSheet("background-color: #1E1E1E;")
    
    # Widget de configuración
    settings_widget = SettingsWindow()
    window.setCentralWidget(settings_widget)
    
    window.show()
    sys.exit(app.exec_())