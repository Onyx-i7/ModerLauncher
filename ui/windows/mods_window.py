import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QLabel, QPushButton, QLineEdit, QGridLayout,
                             QFrame, QMessageBox, QProgressBar, QDialog, QTextEdit, QComboBox,
                             QListWidget, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl, QByteArray
from PyQt5.QtGui import QPixmap, QFont, QIcon, QPalette, QColor, QDesktopServices, QImage
import requests
import json
import urllib.request

# ==================== CARGADOR DE IMÁGENES ====================

class ImageLoader(QThread):
    """Hilo para cargar imágenes sin bloquear la UI"""
    image_loaded = pyqtSignal(QPixmap)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                image = QImage()
                image.loadFromData(response.content)
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    self.image_loaded.emit(pixmap)
        except:
            pass

# ==================== OBTENER VERSIONES Y LOADERS ====================

class VersionsFetcher(QThread):
    """Hilo para obtener todas las versiones disponibles del proyecto"""
    versions_fetched = pyqtSignal(list)  # Lista de versiones con sus datos
    error_occurred = pyqtSignal(str)
    
    def __init__(self, project_id):
        super().__init__()
        self.project_id = project_id
    
    def run(self):
        try:
            url = f"https://api.modrinth.com/v2/project/{self.project_id}/version"
            headers = {'User-Agent': 'ModerLauncher/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                versions = response.json()
                if versions:
                    self.versions_fetched.emit(versions)
                else:
                    self.error_occurred.emit("No se encontraron versiones disponibles")
            else:
                self.error_occurred.emit("Error al obtener versiones del servidor")
                
        except Exception as e:
            self.error_occurred.emit(f"Error de conexión: {str(e)}")

# ==================== HILO DE DESCARGA ====================

class DownloadThread(QThread):
    """Hilo para manejar la descarga en segundo plano"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    speed = pyqtSignal(str)
    size_info = pyqtSignal(str)
    
    def __init__(self, url, destination):
        super().__init__()
        self.url = url
        self.destination = destination
        self.is_cancelled = False
        self.start_time = None
        
    def run(self):
        try:
            import time
            self.start_time = time.time()
            
            def download_progress(block_num, block_size, total_size):
                if self.is_cancelled:
                    raise Exception("Descarga cancelada")
                    
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = int((downloaded / total_size) * 100)
                    self.progress.emit(min(percent, 100))
                    
                    # Calcular velocidad
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time > 0:
                        speed_bps = downloaded / elapsed_time
                        speed_mbps = speed_bps / (1024 * 1024)
                        self.speed.emit(f"{speed_mbps:.2f} MB/s")
                    
                    # Información de tamaño
                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    self.size_info.emit(f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB")
            
            urllib.request.urlretrieve(self.url, self.destination, download_progress)
            
            if not self.is_cancelled:
                self.finished.emit(True, "Descarga completada exitosamente")
            
        except Exception as e:
            if not self.is_cancelled:
                self.finished.emit(False, str(e))
    
    def cancel(self):
        self.is_cancelled = True

# ==================== VENTANA MODERNA DE DESCARGA ====================

class ModernDownloadDialog(QDialog):
    def __init__(self, parent=None, item_name="", project_id="", content_type="mod"):
        super().__init__(parent)
        self.item_name = item_name
        self.project_id = project_id
        self.content_type = content_type
        self.download_thread = None
        self.versions_fetcher = None
        self.destination_path = None
        self.current_speed = "0 MB/s"
        self.all_versions = []
        self.filtered_versions = []
        
        self.setWindowTitle("Descargar Contenido")
        self.setFixedSize(520, 420)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # Estilo moderno y limpio
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
            QLabel#titleLabel {
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QLabel#statusLabel {
                font-size: 13px;
                color: #AAAAAA;
            }
            QProgressBar {
                border: 2px solid #3C3C41;
                border-radius: 6px;
                background-color: #2D2D30;
                text-align: center;
                color: white;
                font-weight: bold;
                height: 28px;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QComboBox {
                background-color: #2D2D30;
                color: white;
                border: 1px solid #3C3C41;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                min-height: 28px;
            }
            QComboBox:hover {
                border: 1px solid #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D30;
                color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
                border: 1px solid #3C3C41;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #3C3C41;
                color: #666666;
            }
            QPushButton#cancelButton {
                background-color: #2D2D30;
                border: 1px solid #3C3C41;
            }
            QPushButton#cancelButton:hover {
                background-color: #3C3C41;
            }
            QPushButton#selectFolderButton {
                background-color: #0078D7;
            }
            QPushButton#selectFolderButton:hover {
                background-color: #006CC1;
            }
        """)
        
        self.setup_ui()
        self.load_versions()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Título
        title = QLabel(f"📦 {self.item_name}")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3C3C41;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Sección de selección (solo para mods y shaders)
        if self.content_type in ["mod", "shader"]:
            selection_frame = QFrame()
            selection_frame.setStyleSheet("""
                QFrame {
                    background-color: #252526;
                    border-radius: 6px;
                    border: 1px solid #3C3C41;
                }
            """)
            selection_layout = QVBoxLayout(selection_frame)
            selection_layout.setContentsMargins(15, 15, 15, 15)
            selection_layout.setSpacing(12)
            
            # Loader (solo para mods)
            if self.content_type == "mod":
                loader_label = QLabel("🔧 Seleccionar Mod Loader:")
                loader_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
                selection_layout.addWidget(loader_label)
                
                self.loader_combo = QComboBox()
                self.loader_combo.addItem("🔹 Todos los loaders", "all")
                self.loader_combo.addItem("⚒️ Forge", "forge")
                self.loader_combo.addItem("🧵 Fabric", "fabric")
                self.loader_combo.addItem("🔷 NeoForge", "neoforge")
                self.loader_combo.addItem("⚙️ Quilt", "quilt")
                self.loader_combo.currentIndexChanged.connect(self.filter_versions)
                selection_layout.addWidget(self.loader_combo)
            
            # Versión de Minecraft
            version_label = QLabel("🎮 Versión de Minecraft:")
            version_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
            selection_layout.addWidget(version_label)
            
            self.version_combo = QComboBox()
            self.version_combo.addItem("Cargando versiones...", None)
            self.version_combo.setEnabled(False)
            selection_layout.addWidget(self.version_combo)
            
            layout.addWidget(selection_frame)
        
        # Estado
        self.status_label = QLabel("⏳ Cargando información...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Información de descarga
        info_container = QWidget()
        info_container.setStyleSheet("background: transparent;")
        info_layout = QHBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        self.speed_label = QLabel("⚡ 0 MB/s")
        self.speed_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold;")
        self.speed_label.hide()
        info_layout.addWidget(self.speed_label)
        
        info_layout.addStretch()
        
        self.size_label = QLabel("0 MB / 0 MB")
        self.size_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.size_label.hide()
        info_layout.addWidget(self.size_label)
        
        layout.addWidget(info_container)
        
        layout.addStretch()
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.select_button = QPushButton("📁 Seleccionar Carpeta y Descargar")
        self.select_button.setObjectName("selectFolderButton")
        self.select_button.setMinimumHeight(40)
        self.select_button.setEnabled(False)
        self.select_button.clicked.connect(self.select_destination)
        self.select_button.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_versions(self):
        """Cargar todas las versiones disponibles"""
        self.versions_fetcher = VersionsFetcher(self.project_id)
        self.versions_fetcher.versions_fetched.connect(self.on_versions_loaded)
        self.versions_fetcher.error_occurred.connect(self.on_versions_error)
        self.versions_fetcher.start()
    
    def on_versions_loaded(self, versions):
        """Callback cuando las versiones se cargan"""
        self.all_versions = versions
        self.filter_versions()
        self.status_label.setText("✅ Seleccione las opciones y la carpeta de destino")
        self.select_button.setEnabled(True)
    
    def on_versions_error(self, error_msg):
        """Callback cuando hay error al cargar versiones"""
        self.status_label.setText(f"❌ {error_msg}")
        QMessageBox.critical(self, "Error", f"No se pudieron cargar las versiones:\n\n{error_msg}")
    
    def filter_versions(self):
        """Filtrar versiones según el loader seleccionado"""
        if self.content_type not in ["mod", "shader"]:
            return
        
        selected_loader = "all"
        if self.content_type == "mod" and hasattr(self, 'loader_combo'):
            selected_loader = self.loader_combo.currentData()
        
        # Agrupar versiones por versión de Minecraft
        minecraft_versions = {}
        
        for version in self.all_versions:
            loaders = version.get('loaders', [])
            game_versions = version.get('game_versions', [])
            
            # Filtrar por loader
            if selected_loader != "all" and selected_loader not in loaders:
                continue
            
            for mc_version in game_versions:
                if mc_version not in minecraft_versions:
                    minecraft_versions[mc_version] = {
                        'loaders': set(),
                        'version_data': version
                    }
                minecraft_versions[mc_version]['loaders'].update(loaders)
        
        # Actualizar combobox de versiones
        self.version_combo.clear()
        
        if not minecraft_versions:
            self.version_combo.addItem("❌ No hay versiones disponibles", None)
            self.version_combo.setEnabled(False)
            self.select_button.setEnabled(False)
            return
        
        # Ordenar versiones (más recientes primero)
        sorted_versions = sorted(minecraft_versions.keys(), reverse=True)
        
        for mc_version in sorted_versions:
            data = minecraft_versions[mc_version]
            loaders_str = ', '.join(sorted(data['loaders']))
            display_text = f"Minecraft {mc_version}"
            if selected_loader == "all":
                display_text += f" ({loaders_str})"
            
            self.version_combo.addItem(display_text, {
                'mc_version': mc_version,
                'version_data': data['version_data']
            })
        
        self.version_combo.setEnabled(True)
        self.select_button.setEnabled(True)
    
    def get_selected_version_data(self):
        """Obtener los datos de la versión seleccionada"""
        if self.content_type in ["mod", "shader"]:
            version_data = self.version_combo.currentData()
            if version_data:
                return version_data['version_data']
        elif self.all_versions:
            # Para texturas, usar la versión más reciente
            return self.all_versions[0]
        return None
    
    def select_destination(self):
        """Seleccionar carpeta de destino"""
        version_data = self.get_selected_version_data()
        
        if not version_data:
            QMessageBox.warning(self, "Error", "Por favor seleccione una versión válida")
            return
        
        # Obtener archivo de descarga
        files = version_data.get('files', [])
        if not files:
            QMessageBox.warning(self, "Error", "No se encontró archivo de descarga")
            return
        
        primary_file = files[0]
        download_url = primary_file.get('url')
        filename = primary_file.get('filename', 'download.jar')
        
        if not download_url:
            QMessageBox.warning(self, "Error", "No se pudo obtener URL de descarga")
            return
        
        # Abrir diálogo para seleccionar carpeta
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de destino",
            os.path.expanduser("~/Downloads"),
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self.destination_path = os.path.join(folder, filename)
            self.download_url = download_url
            self.filename = filename
            self.start_download()
    
    def start_download(self):
        """Iniciar descarga"""
        if not self.destination_path:
            return
        
        self.select_button.setEnabled(False)
        if hasattr(self, 'loader_combo'):
            self.loader_combo.setEnabled(False)
        if hasattr(self, 'version_combo'):
            self.version_combo.setEnabled(False)
        
        self.status_label.setText(f"⬇️ Descargando: {self.filename}")
        self.progress_bar.show()
        self.speed_label.show()
        self.size_label.show()
        
        # Iniciar descarga en segundo plano
        self.download_thread = DownloadThread(self.download_url, self.destination_path)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.speed.connect(self.update_speed)
        self.download_thread.size_info.connect(self.update_size)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_speed(self, speed):
        self.current_speed = speed
        self.speed_label.setText(f"⚡ {speed}")
    
    def update_size(self, size_text):
        self.size_label.setText(size_text)
    
    def download_finished(self, success, message):
        if success:
            self.status_label.setText("✅ Descarga completada")
            self.progress_bar.setValue(100)
            
            # Mostrar mensaje de éxito
            msg = QMessageBox(self)
            msg.setWindowTitle("Descarga Completada")
            msg.setText(f"✅ {self.item_name}")
            msg.setInformativeText(f"Guardado en:\n{self.destination_path}")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1E1E1E;
                }
                QMessageBox QLabel {
                    color: white;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 20px;
                    min-width: 80px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            msg.exec_()
            self.accept()
        else:
            self.status_label.setText("❌ Error en la descarga")
            
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("Error")
            error_msg.setText("❌ Error en la descarga")
            error_msg.setInformativeText(f"No se pudo completar la descarga:\n\n{message}")
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1E1E1E;
                }
                QMessageBox QLabel {
                    color: white;
                }
                QPushButton {
                    background-color: #E53935;
                    color: white;
                    border-radius: 5px;
                    padding: 8px 20px;
                    min-width: 80px;
                }
            """)
            error_msg.exec_()
            
            # Reactivar controles
            self.select_button.setEnabled(True)
            if hasattr(self, 'loader_combo'):
                self.loader_combo.setEnabled(True)
            if hasattr(self, 'version_combo'):
                self.version_combo.setEnabled(True)
    
    def cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            reply = QMessageBox.question(
                self, 
                "Cancelar Descarga",
                "¿Estás seguro de que deseas cancelar la descarga?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.download_thread.cancel()
                self.download_thread.wait()
                self.reject()
        else:
            self.reject()

# ==================== CARGADOR DE CONTENIDO ====================

class ContentLoader(QThread):
    """Hilo para cargar contenido (mods, shaders, texturas) sin bloquear la UI"""
    content_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, content_type="mod", page=0, page_size=20, search_query=""):
        super().__init__()
        self.content_type = content_type
        self.page = page
        self.page_size = page_size
        self.search_query = search_query
    
    def run(self):
        try:
            offset = self.page * self.page_size
            limit = self.page_size
            
            base_url = "https://api.modrinth.com/v2/search"
            params = f"?limit={limit}&offset={offset}&index=downloads"
            
            if self.search_query:
                params += f"&query={requests.utils.quote(self.search_query)}"
            
            if self.content_type == "shader":
                params += "&facets=[[%22project_type:shader%22]]"
            elif self.content_type == "resourcepack":
                params += "&facets=[[%22project_type:resourcepack%22]]"
            else:
                params += "&facets=[[%22categories:forge%22,%22categories:fabric%22],[%22project_type:mod%22]]"
            
            url = base_url + params
            
            headers = {
                'User-Agent': 'ModerLauncher/1.0 (contact@moderlauncher.com)'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                content_data = data.get('hits', [])
                self.content_loaded.emit(content_data)
            else:
                self.error_occurred.emit("Error al cargar contenido")
                
        except Exception as e:
            self.error_occurred.emit(f"Error de conexión: {str(e)}")

# ==================== TARJETA DE CONTENIDO ====================

class ContentCard(QFrame):
    """Tarjeta individual para cada elemento (mod, shader, textura)"""
    def __init__(self, content_data, content_type="mod", parent=None):
        super().__init__(parent)
        self.content_data = content_data
        self.content_type = content_type
        self.image_loader = None
        self.setFixedHeight(120)
        self.setup_ui()
        self.load_icon()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border-radius: 8px;
                border: 1px solid #3C3C41;
            }
            QFrame:hover {
                background-color: #333337;
                border: 1px solid #4CAF50;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Icono del contenido
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(80, 80)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                border-radius: 6px;
                border: 1px solid #3C3C41;
            }
        """)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setScaledContents(True)
        
        placeholder = QPixmap(80, 80)
        placeholder.fill(QColor("#1E1E1E"))
        self.icon_label.setPixmap(placeholder)
        
        layout.addWidget(self.icon_label)
        
        # Información del contenido
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title_label = QLabel(self.content_data.get('title', 'Sin título'))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        title_label.setWordWrap(False)
        info_layout.addWidget(title_label)
        
        description = self.content_data.get('description', 'Sin descripción')
        if len(description) > 100:
            description = description[:97] + "..."
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(40)
        info_layout.addWidget(desc_label)
        
        info_text = f"📥 {self.content_data.get('downloads', 0):,} descargas • "
        info_text += f"⭐ {self.content_data.get('follows', 0):,} seguidores"
        
        stats_label = QLabel(info_text)
        stats_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                background: transparent;
                border: none;
            }
        """)
        info_layout.addWidget(stats_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout, stretch=1)
        
        # Botones
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setAlignment(Qt.AlignCenter)
        
        self.install_btn = QPushButton("⬇ Descargar")
        self.install_btn.setFixedSize(100, 32)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3d8c40;
            }
            QPushButton:pressed {
                background-color: #2d7030;
            }
        """)
        self.install_btn.setCursor(Qt.PointingHandCursor)
        self.install_btn.clicked.connect(self.install_content)
        buttons_layout.addWidget(self.install_btn)
        
        details_btn = QPushButton("ℹ Detalles")
        details_btn.setFixedSize(100, 28)
        details_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C41;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #55555A;
            }
            QPushButton:pressed {
                background-color: #2A2A2E;
            }
        """)
        details_btn.setCursor(Qt.PointingHandCursor)
        details_btn.clicked.connect(self.show_details)
        buttons_layout.addWidget(details_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    
    def load_icon(self):
        icon_url = self.content_data.get('icon_url')
        
        if icon_url:
            self.image_loader = ImageLoader(icon_url)
            self.image_loader.image_loaded.connect(self.on_icon_loaded)
            self.image_loader.start()
        else:
            self.show_placeholder()
    
    def on_icon_loaded(self, pixmap):
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            self.show_placeholder()
    
    def show_placeholder(self):
        pixmap = QPixmap(80, 80)
        pixmap.fill(QColor("#1E1E1E"))
        self.icon_label.setPixmap(pixmap)
    
    def install_content(self):
        """Abrir ventana de descarga moderna"""
        project_id = self.content_data.get('project_id') or self.content_data.get('slug')
        content_name = self.content_data.get('title', 'Contenido')
        
        if not project_id:
            QMessageBox.warning(self, "Error", "No se pudo obtener el ID del proyecto")
            return
        
        dialog = ModernDownloadDialog(self, content_name, project_id, self.content_type)
        dialog.exec_()
    
    def show_details(self):
        details_dialog = ContentDetailsDialog(self.content_data, self.content_type, self)
        details_dialog.exec_()

# ==================== DIÁLOGO DE DETALLES ====================

class ContentDetailsDialog(QDialog):
    """Diálogo para mostrar detalles del contenido"""
    def __init__(self, content_data, content_type="mod", parent=None):
        super().__init__(parent)
        self.content_data = content_data
        self.content_type = content_type
        self.image_loader = None
        self.setup_ui()
        self.load_icon()
    
    def setup_ui(self):
        type_name = {"mod": "Mod", "shader": "Shader", "resourcepack": "Textura"}
        self.setWindowTitle(f"Detalles - {self.content_data.get('title', 'Contenido')}")
        self.setFixedSize(650, 550)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header con icono y título
        header_layout = QHBoxLayout()
        
        # Icono grande
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(100, 100)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #2D2D30;
                border-radius: 8px;
                border: 1px solid #3C3C41;
            }
        """)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setScaledContents(True)
        header_layout.addWidget(self.icon_label)
        
        # Título y autor
        title_layout = QVBoxLayout()
        
        title_label = QLabel(self.content_data.get('title', 'Sin título'))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_label.setWordWrap(True)
        title_layout.addWidget(title_label)
        
        author_label = QLabel(f"Por: {self.content_data.get('author', 'Desconocido')}")
        author_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 13px;
                background: transparent;
            }
        """)
        title_layout.addWidget(author_label)
        
        title_layout.addStretch()
        header_layout.addLayout(title_layout, stretch=1)
        
        layout.addLayout(header_layout)
        
        # Descripción completa
        desc_group = QFrame()
        desc_group.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border-radius: 8px;
                border: 1px solid #3C3C41;
            }
        """)
        desc_layout = QVBoxLayout(desc_group)
        desc_layout.setContentsMargins(15, 10, 15, 10)
        desc_layout.setSpacing(8)
        
        desc_title = QLabel("📝 Descripción")
        desc_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        desc_layout.addWidget(desc_title)
        
        desc_text = QTextEdit()
        desc_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: white;
                border: 1px solid #3C3C41;
                border-radius: 4px;
                font-size: 13px;
                padding: 8px;
            }
        """)
        desc_text.setPlainText(self.content_data.get('description', 'Sin descripción'))
        desc_text.setReadOnly(True)
        desc_text.setFixedHeight(100)
        desc_layout.addWidget(desc_text)
        
        layout.addWidget(desc_group)
        
        # Estadísticas
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #3C3C41;
                border-radius: 8px;
            }
        """)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(15, 10, 15, 10)
        stats_layout.setSpacing(10)
        
        stats_title = QLabel("📊 Estadísticas")
        stats_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        stats_layout.addWidget(stats_title)
        
        # Grid de estadísticas
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)
        stats_grid.setContentsMargins(0, 5, 0, 0)
        
        stats_data = [
            ("📥 Descargas:", f"{self.content_data.get('downloads', 0):,}"),
            ("⭐ Seguidores:", f"{self.content_data.get('follows', 0):,}"),
            ("🎯 Puntos:", f"{self.content_data.get('points', 0):,}"),
            ("📅 Actualizado:", self.content_data.get('date_modified', 'N/A')[:10]),
            ("🏷️ Categorías:", ', '.join(self.content_data.get('categories', [])[:3])),
            ("📖 Tipo:", type_name.get(self.content_type, 'Contenido'))
        ]
        
        row = 0
        for label_text, value_text in stats_data:
            label = QLabel(label_text)
            label.setStyleSheet("""
                QLabel {
                    color: #AAAAAA;
                    font-size: 12px;
                    background: transparent;
                    border: none;
                }
            """)
            stats_grid.addWidget(label, row, 0)
            
            value = QLabel(str(value_text))
            value.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                }
            """)
            value.setWordWrap(True)
            stats_grid.addWidget(value, row, 1)
            row += 1
        
        stats_layout.addLayout(stats_grid)
        layout.addWidget(stats_frame)
        
        layout.addStretch()
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        view_btn = QPushButton("🌐 Ver en Modrinth")
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.clicked.connect(self.open_modrinth)
        buttons_layout.addWidget(view_btn)
        
        close_btn = QPushButton("Cerrar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C41;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #55555A;
            }
        """)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_icon(self):
        icon_url = self.content_data.get('icon_url')
        
        if icon_url:
            self.image_loader = ImageLoader(icon_url)
            self.image_loader.image_loaded.connect(self.on_icon_loaded)
            self.image_loader.start()
        else:
            self.show_placeholder()
    
    def on_icon_loaded(self, pixmap):
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            self.show_placeholder()
    
    def show_placeholder(self):
        pixmap = QPixmap(100, 100)
        pixmap.fill(QColor("#2D2D30"))
        self.icon_label.setPixmap(pixmap)
    
    def open_modrinth(self):
        slug = self.content_data.get('slug', '')
        type_path = {"mod": "mod", "shader": "shader", "resourcepack": "resourcepack"}
        if slug:
            QDesktopServices.openUrl(QUrl(f"https://modrinth.com/{type_path.get(self.content_type, 'mod')}/{slug}"))

# ==================== VENTANA PRINCIPAL DE CONTENIDO ====================

class ModsWindow(QWidget):
    """Ventana principal con navegación entre Mods, Shaders y Texturas"""
    def __init__(self, initial_data=None, parent=None, launcher=None):
        super().__init__(parent)
        self.launcher = launcher
        self.content_data = initial_data or []
        self.current_page = 0
        self.page_size = 10
        self.search_query = ""
        self.content_cards = []
        self.content_loader = None
        self.current_content_type = "mod"
        self.current_mode = "explore"  # Nuevo: explore, manage, modpacks
        
        # Importar managers
        try:
            from managers.mod_manager import ModManager
            from managers.modpack_manager import ModpackManager
            from utils.resource_manager import get_minecraft_dir
            
            minecraft_dir = get_minecraft_dir()
            self.mod_manager = ModManager(minecraft_dir)
            self.modpack_manager = ModpackManager(minecraft_dir)
        except Exception as e:
            print(f"Error inicializando managers: {e}")
            self.mod_manager = None
            self.modpack_manager = None
        
        if parent:
            self.setGeometry(0, 0, parent.width(), parent.height())
        
        self.setup_ui()
        if initial_data:
            self.display_content()
        else:
            self.load_content()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: white;
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)
        
        # Definir estilos
        self.button_style_inactive = """
            QPushButton {
                background-color: #2D2D30;
                color: #AAAAAA;
                border: 1px solid #3C3C41;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #3C3C41;
                color: white;
                border: 1px solid #4CAF50;
            }
        """
        
        self.button_style_active = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #4CAF50;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }
        """
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        self.create_navigation_buttons(main_layout)
        self.create_header(main_layout)
        self.create_content_area(main_layout)
        self.create_footer(main_layout)
    
    def create_navigation_buttons(self, parent_layout):
        nav_frame = QFrame()
        nav_frame.setFixedHeight(60)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 8px;
            }
        """)
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(15, 10, 15, 10)
        nav_layout.setSpacing(10)
        
        button_style_inactive = self.button_style_inactive
        button_style_active = self.button_style_active
        
        self.explore_btn = QPushButton("🔍 Explorar")
        self.explore_btn.setFixedSize(150, 40)
        self.explore_btn.setStyleSheet(button_style_active)
        self.explore_btn.setCursor(Qt.PointingHandCursor)
        self.explore_btn.clicked.connect(lambda: self.switch_mode("explore"))
        nav_layout.addWidget(self.explore_btn)
        
        self.manage_btn = QPushButton("⚙️ Administrar Mods")
        self.manage_btn.setFixedSize(180, 40)
        self.manage_btn.setStyleSheet(button_style_inactive)
        self.manage_btn.setCursor(Qt.PointingHandCursor)
        self.manage_btn.clicked.connect(lambda: self.switch_mode("manage"))
        nav_layout.addWidget(self.manage_btn)
        
        self.modpacks_btn = QPushButton("📁 Modpacks")
        self.modpacks_btn.setFixedSize(150, 40)
        self.modpacks_btn.setStyleSheet(button_style_inactive)
        self.modpacks_btn.setCursor(Qt.PointingHandCursor)
        self.modpacks_btn.clicked.connect(lambda: self.switch_mode("modpacks"))
        nav_layout.addWidget(self.modpacks_btn)
        
        nav_layout.addStretch()
        
        parent_layout.addWidget(nav_frame)
        
        # Navegación de tipos de contenido (solo visible en modo explore)
        self.content_type_nav = QFrame()
        self.content_type_nav.setFixedHeight(50)
        self.content_type_nav.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border-radius: 6px;
                margin-top: 10px;
            }
        """)
        content_nav_layout = QHBoxLayout(self.content_type_nav)
        content_nav_layout.setContentsMargins(10, 5, 10, 5)
        content_nav_layout.setSpacing(5)
        
        self.mods_btn = QPushButton("📦 Mods")
        self.mods_btn.setFixedSize(120, 35)
        self.mods_btn.setStyleSheet(button_style_active)
        self.mods_btn.setCursor(Qt.PointingHandCursor)
        self.mods_btn.clicked.connect(lambda: self.switch_content_type("mod"))
        content_nav_layout.addWidget(self.mods_btn)
        
        self.shaders_btn = QPushButton("✨ Shaders")
        self.shaders_btn.setFixedSize(120, 35)
        self.shaders_btn.setStyleSheet(button_style_inactive)
        self.shaders_btn.setCursor(Qt.PointingHandCursor)
        self.shaders_btn.clicked.connect(lambda: self.switch_content_type("shader"))
        content_nav_layout.addWidget(self.shaders_btn)
        
        self.textures_btn = QPushButton("🎨 Texturas")
        self.textures_btn.setFixedSize(120, 35)
        self.textures_btn.setStyleSheet(button_style_inactive)
        self.textures_btn.setCursor(Qt.PointingHandCursor)
        self.textures_btn.clicked.connect(lambda: self.switch_content_type("resourcepack"))
        content_nav_layout.addWidget(self.textures_btn)
        
        content_nav_layout.addStretch()
        parent_layout.addWidget(self.content_type_nav)
        
        self.button_style_inactive = button_style_inactive
        self.button_style_active = button_style_active
    
    def switch_mode(self, mode):
        if self.current_mode == mode:
            return
        
        self.current_mode = mode
        self.current_page = 0
        self.search_query = ""
        self.search_input.clear()
        
        # Actualizar botones de navegación
        self.explore_btn.setStyleSheet(self.button_style_active if mode == "explore" else self.button_style_inactive)
        self.manage_btn.setStyleSheet(self.button_style_active if mode == "manage" else self.button_style_inactive)
        self.modpacks_btn.setStyleSheet(self.button_style_active if mode == "modpacks" else self.button_style_inactive)
        
        # Limpiar contenido actual
        self.clear_content_cards()
        
        if mode == "explore":
            # Modo explorar: mostrar navegación de tipos de contenido
            if hasattr(self, 'content_type_nav'):
                self.content_type_nav.show()
            self.header_title.setText("📦 Explorar Mods de Minecraft")
            self.search_input.setPlaceholderText("🔍 Buscar mods...")
            self.current_content_type = "mod"
            self.load_content()
        elif mode == "manage":
            # Modo administrar: mostrar mods instalados
            if hasattr(self, 'content_type_nav'):
                self.content_type_nav.hide()
            self.header_title.setText("⚙️ Administrar Mods Instalados")
            self.search_input.setPlaceholderText("🔍 Buscar mods instalados...")
            self.show_mod_management()
        elif mode == "modpacks":
            # Modo modpacks: mostrar gestión de modpacks
            if hasattr(self, 'content_type_nav'):
                self.content_type_nav.hide()
            self.header_title.setText("📁 Gestor de Modpacks")
            self.search_input.setPlaceholderText("🔍 Buscar modpacks...")
            self.show_modpack_management()
    
    def create_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setFixedHeight(70)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 8px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        self.header_title = QLabel("📦 Explorar Mods de Minecraft")
        self.header_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setFixedSize(300, 35)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E1E;
                color: white;
                border: 1px solid #3C3C41;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        self.search_input.setPlaceholderText("🔍 Buscar mods...")
        self.search_input.returnPressed.connect(self.search_content)
        header_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Buscar")
        search_btn.setFixedSize(80, 35)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3d8c40;
            }
            QPushButton:pressed {
                background-color: #2d7030;
            }
        """)
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.clicked.connect(self.search_content)
        header_layout.addWidget(search_btn)
        
        parent_layout.addWidget(header_frame)
    
    def create_content_area(self, parent_layout):
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #252526;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #3C3C41;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4CAF50;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget {
                background-color: #252526;
                border-radius: 8px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(8)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.content_widget)
        parent_layout.addWidget(self.scroll_area)
    
    def create_footer(self, parent_layout):
        footer_frame = QFrame()
        footer_frame.setFixedHeight(50)
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 8px;
            }
        """)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(15, 0, 15, 0)
        
        self.prev_button = QPushButton("⬅ Anterior")
        self.prev_button.setFixedSize(120, 35)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #3C3C41;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #55555A;
            }
            QPushButton:disabled {
                background-color: #2A2A2E;
                color: #666666;
            }
        """)
        self.prev_button.setCursor(Qt.PointingHandCursor)
        self.prev_button.clicked.connect(self.previous_page)
        self.prev_button.setEnabled(False)
        footer_layout.addWidget(self.prev_button)
        
        footer_layout.addStretch()
        
        self.page_label = QLabel("Página 1")
        self.page_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        self.page_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(self.page_label)
        
        footer_layout.addStretch()
        
        self.next_button = QPushButton("Siguiente ➡")
        self.next_button.setFixedSize(120, 35)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #3C3C41;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #55555A;
            }
            QPushButton:disabled {
                background-color: #2A2A2E;
                color: #666666;
            }
        """)
        self.next_button.setCursor(Qt.PointingHandCursor)
        self.next_button.clicked.connect(self.next_page)
        footer_layout.addWidget(self.next_button)
        
        parent_layout.addWidget(footer_frame)
    
    def search_content(self):
        query = self.search_input.text().strip()
        self.search_query = query
        self.current_page = 0
        self.load_content()
    
    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_content()
    
    def next_page(self):
        self.current_page += 1
        self.load_content()
    
    def load_content(self):
        if self.content_loader and self.content_loader.isRunning():
            return
        
        self.clear_content_cards()
        self.show_loading_indicator()
        
        self.content_loader = ContentLoader(
            self.current_content_type, 
            self.current_page, 
            self.page_size, 
            self.search_query
        )
        self.content_loader.content_loaded.connect(self.on_content_loaded)
        self.content_loader.error_occurred.connect(self.on_load_error)
        self.content_loader.start()
    
    def show_loading_indicator(self):
        loading_label = QLabel("🔄 Cargando...")
        loading_label.setObjectName("loading_label")
        loading_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 16px;
                font-weight: bold;
                padding: 80px;
                background: transparent;
            }
        """)
        loading_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(loading_label)
    
    def on_content_loaded(self, content_data):
        self.content_data = content_data
        self.display_content()

    def display_content(self):
        self.clear_content_cards()
        if not self.content_data:
            no_content_label = QLabel("🔭 No se encontró contenido para tu búsqueda.")
            no_content_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 16px;
                    padding: 80px;
                    background: transparent;
                }
            """)
            no_content_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(no_content_label)
        else:
            self.content_cards.clear()
            for content_item in self.content_data:
                content_card = ContentCard(content_item, self.current_content_type, self)
                self.content_cards.append(content_card)
                self.content_layout.addWidget(content_card)
            
            self.content_layout.addStretch()
        
        self.scroll_area.verticalScrollBar().setValue(0)
        self.update_pagination()
    
    def on_load_error(self, error_message):
        self.clear_content_cards()
        
        error_label = QLabel(f"❌ {error_message}\n\nVerifica tu conexión a internet")
        error_label.setStyleSheet("""
            QLabel {
                color: #FF6B6B;
                font-size: 16px;
                padding: 80px;
                background: transparent;
            }
        """)
        error_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(error_label)
        
        self.update_pagination()
    
    def clear_content_cards(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                if isinstance(widget, ContentCard) and hasattr(widget, 'stop_threads'):
                    widget.stop_threads()
                widget.setParent(None)
                widget.deleteLater()
        self.content_cards.clear()

    def update_pagination(self):
        self.page_label.setText(f"Página {self.current_page + 1}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(len(self.content_data) >= self.page_size)
    
    def show_mod_management(self):
        """Mostrar interfaz de administración de mods"""
        self.clear_content_cards()
        
        if not self.mod_manager:
            error_label = QLabel("❌ Error: No se pudo inicializar el administrador de mods")
            error_label.setStyleSheet("""
                QLabel {
                    color: #FF6B6B;
                    font-size: 16px;
                    padding: 80px;
                    background: transparent;
                }
            """)
            error_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(error_label)
            return
        
        # Escanear mods instalados
        installed_mods = self.mod_manager.scan_installed_mods()
        
        if not installed_mods:
            no_mods_label = QLabel("📦 No hay mods instalados\n\nUsa la pestaña 'Explorar' para descargar mods")
            no_mods_label.setStyleSheet("""
                QLabel {
                    color: #AAAAAA;
                    font-size: 16px;
                    padding: 80px;
                    background: transparent;
                }
            """)
            no_mods_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(no_mods_label)
        else:
            # Mostrar lista de mods
            for mod_info in installed_mods:
                mod_card = ModManagementCard(mod_info, self.mod_manager, self)
                self.content_layout.addWidget(mod_card)
        
        self.content_layout.addStretch()
    
    def show_modpack_management(self):
        """Mostrar interfaz de gestión de modpacks"""
        self.clear_content_cards()
        
        if not self.modpack_manager:
            error_label = QLabel("❌ Error: No se pudo inicializar el gestor de modpacks")
            error_label.setStyleSheet("""
                QLabel {
                    color: #FF6B6B;
                    font-size: 16px;
                    padding: 80px;
                    background: transparent;
                }
            """)
            error_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(error_label)
            return
        
        # Escanear modpacks
        modpacks = self.modpack_manager.scan_modpacks()
        
        # Botones de acción
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 8px;
                margin-bottom: 15px;
            }
        """)
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(15, 10, 15, 10)
        
        create_btn = QPushButton("➕ Crear Modpack")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        create_btn.clicked.connect(self.create_modpack)
        actions_layout.addWidget(create_btn)
        
        import_btn = QPushButton("📥 Importar Modpack")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        import_btn.clicked.connect(self.import_modpack)
        actions_layout.addWidget(import_btn)
        
        actions_layout.addStretch()
        self.content_layout.addWidget(actions_frame)
        
        if not modpacks:
            no_packs_label = QLabel("📁 No hay modpacks\n\nCrea un modpack desde tus mods instalados")
            no_packs_label.setStyleSheet("""
                QLabel {
                    color: #AAAAAA;
                    font-size: 16px;
                    padding: 80px;
                    background: transparent;
                }
            """)
            no_packs_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(no_packs_label)
        else:
            # Mostrar lista de modpacks
            for modpack_info in modpacks:
                pack_card = ModpackCard(modpack_info, self.modpack_manager, self)
                self.content_layout.addWidget(pack_card)
        
        self.content_layout.addStretch()
    
    def create_modpack(self):
        """Crear un nuevo modpack"""
        if not self.modpack_manager:
            QMessageBox.warning(self, "Error", "No se pudo acceder al gestor de modpacks")
            return
        
        # Obtener directorio de mods
        from utils.resource_manager import get_minecraft_dir
        from pathlib import Path
        minecraft_dir = get_minecraft_dir()
        mods_dir = Path(minecraft_dir) / "mods"
        
        if not mods_dir.exists() or not list(mods_dir.glob("*.jar")):
            QMessageBox.warning(self, "Error", "No hay mods instalados para crear un modpack")
            return
        
        # Diálogo para crear modpack
        dialog = CreateModpackDialog(self.modpack_manager, str(mods_dir), self)
        if dialog.exec_() == QDialog.Accepted:
            self.show_modpack_management()  # Refrescar vista
    
    def import_modpack(self):
        """Importar un modpack desde archivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de modpack", "", "Archivos ZIP (*.zip)"
        )
        
        if file_path and self.modpack_manager:
            pack_id = self.modpack_manager.import_modpack(file_path)
            if pack_id:
                QMessageBox.information(self, "Éxito", "Modpack importado correctamente")
                self.show_modpack_management()  # Refrescar vista
            else:
                QMessageBox.warning(self, "Error", "No se pudo importar el modpack")


# ==================== TARJETA DE GESTIÓN DE MOD ====================

class ModManagementCard(QFrame):
    """Tarjeta para gestionar un mod instalado"""
    def __init__(self, mod_info, mod_manager, parent=None):
        super().__init__(parent)
        self.mod_info = mod_info
        self.mod_manager = mod_manager
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border-radius: 8px;
                border: 1px solid #3C3C41;
            }
            QFrame:hover {
                background-color: #333337;
                border: 1px solid #4CAF50;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Información del mod
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title_label = QLabel(f"{self.mod_info.name}")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(title_label)
        
        version_label = QLabel(f"Versión: {self.mod_info.version}")
        version_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(version_label)
        
        status_text = "✅ Habilitado" if self.mod_info.enabled else "❌ Deshabilitado"
        status_label = QLabel(status_text)
        status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50 if self.mod_info.enabled else #FF6B6B;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(status_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout, stretch=1)
        
        # Botones de acción
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        toggle_btn = QPushButton("🔄 Habilitar" if not self.mod_info.enabled else "🔄 Deshabilitar")
        toggle_btn.setFixedSize(120, 32)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        toggle_btn.clicked.connect(self.toggle_mod)
        buttons_layout.addWidget(toggle_btn)
        
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.setFixedSize(120, 32)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_btn.clicked.connect(self.delete_mod)
        buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    
    def toggle_mod(self):
        """Habilitar/deshabilitar mod"""
        if self.mod_manager.toggle_mod(self.mod_info.name):
            # Refrescar la vista
            parent_window = self.parent()
            while parent_window and not isinstance(parent_window, ModsWindow):
                parent_window = parent_window.parent()
            if parent_window:
                parent_window.show_mod_management()
        else:
            QMessageBox.warning(self, "Error", "No se pudo cambiar el estado del mod")
    
    def delete_mod(self):
        """Eliminar mod"""
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar '{self.mod_info.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.mod_manager.uninstall_mod(self.mod_info.name):
                # Refrescar la vista
                parent_window = self.parent()
                while parent_window and not isinstance(parent_window, ModsWindow):
                    parent_window = parent_window.parent()
                if parent_window:
                    parent_window.show_mod_management()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el mod")


# ==================== TARJETA DE MODPACK ====================

class ModpackCard(QFrame):
    """Tarjeta para gestionar un modpack"""
    def __init__(self, modpack_info, modpack_manager, parent=None):
        super().__init__(parent)
        self.modpack_info = modpack_info
        self.modpack_manager = modpack_manager
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border-radius: 8px;
                border: 1px solid #3C3C41;
            }
            QFrame:hover {
                background-color: #333337;
                border: 1px solid #4CAF50;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Información del modpack
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title_label = QLabel(f"{self.modpack_info.name}")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(title_label)
        
        version_label = QLabel(f"Versión: {self.modpack_info.version}")
        version_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(version_label)
        
        mc_label = QLabel(f"Minecraft: {self.modpack_info.minecraft_version}")
        mc_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(mc_label)
        
        mods_count = len(self.modpack_info.mods)
        mods_label = QLabel(f"Mods: {mods_count}")
        mods_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
            }
        """)
        info_layout.addWidget(mods_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout, stretch=1)
        
        # Botones de acción
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        install_btn = QPushButton("📦 Instalar")
        install_btn.setFixedSize(100, 32)
        install_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        install_btn.clicked.connect(self.install_modpack)
        buttons_layout.addWidget(install_btn)
        
        export_btn = QPushButton("📤 Exportar")
        export_btn.setFixedSize(100, 32)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        export_btn.clicked.connect(self.export_modpack)
        buttons_layout.addWidget(export_btn)
        
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.setFixedSize(100, 32)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_btn.clicked.connect(self.delete_modpack)
        buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    
    def install_modpack(self):
        """Instalar modpack"""
        from utils.resource_manager import get_minecraft_dir
        from pathlib import Path
        minecraft_dir = get_minecraft_dir()
        mods_dir = Path(minecraft_dir) / "mods"
        
        reply = QMessageBox.question(
            self, "Confirmar instalación",
            f"¿Instalar '{self.modpack_info.name}'? Esto reemplazará los mods actuales.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.modpack_manager.install_modpack(self.modpack_info.name, str(mods_dir)):
                QMessageBox.information(self, "Éxito", "Modpack instalado correctamente")
            else:
                QMessageBox.warning(self, "Error", "No se pudo instalar el modpack")
    
    def export_modpack(self):
        """Exportar modpack"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar modpack", f"{self.modpack_info.name}.zip", "Archivos ZIP (*.zip)"
        )
        
        if file_path:
            if self.modpack_manager.export_modpack(self.modpack_info.name, file_path):
                QMessageBox.information(self, "Éxito", "Modpack exportado correctamente")
            else:
                QMessageBox.warning(self, "Error", "No se pudo exportar el modpack")
    
    def delete_modpack(self):
        """Eliminar modpack"""
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar '{self.modpack_info.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.modpack_manager.delete_modpack(self.modpack_info.name):
                # Refrescar la vista
                parent_window = self.parent()
                while parent_window and not isinstance(parent_window, ModsWindow):
                    parent_window = parent_window.parent()
                if parent_window:
                    parent_window.show_modpack_management()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el modpack")


# ==================== DIÁLOGO PARA CREAR MODPACK ====================

class CreateModpackDialog(QDialog):
    """Diálogo para crear un nuevo modpack"""
    def __init__(self, modpack_manager, mods_dir, parent=None):
        super().__init__(parent)
        self.modpack_manager = modpack_manager
        self.mods_dir = mods_dir
        self.setWindowTitle("Crear Modpack")
        self.setFixedSize(400, 300)
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Nombre
        name_label = QLabel("Nombre del modpack:")
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Mi Modpack")
        layout.addWidget(self.name_input)
        
        # Versión de Minecraft
        mc_label = QLabel("Versión de Minecraft:")
        mc_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(mc_label)
        
        self.mc_input = QLineEdit()
        self.mc_input.setPlaceholderText("1.20.1")
        layout.addWidget(self.mc_input)
        
        # Modloader
        loader_label = QLabel("Modloader:")
        loader_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(loader_label)
        
        self.loader_combo = QComboBox()
        self.loader_combo.addItem("Forge")
        self.loader_combo.addItem("Fabric")
        self.loader_combo.addItem("NeoForge")
        layout.addWidget(self.loader_combo)
        
        # Descripción
        desc_label = QLabel("Descripción (opcional):")
        desc_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        layout.addWidget(self.desc_input)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Crear")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        create_btn.clicked.connect(self.create_modpack)
        buttons_layout.addWidget(create_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def create_modpack(self):
        """Crear el modpack"""
        name = self.name_input.text().strip()
        mc_version = self.mc_input.text().strip()
        modloader = self.loader_combo.currentText().lower()
        description = self.desc_input.toPlainText().strip()
        
        if not name or not mc_version:
            QMessageBox.warning(self, "Error", "Nombre y versión de Minecraft son obligatorios")
            return
        
        # Crear modpack
        pack_id = self.modpack_manager.create_modpack(
            name=name,
            minecraft_version=mc_version,
            modloader=modloader,
            modloader_version="Desconocida",  # Podría mejorarse
            mods_dir=self.mods_dir,
            description=description,
            author="Usuario"  # Podría obtenerse del perfil
        )
        
        if pack_id:
            QMessageBox.information(self, "Éxito", "Modpack creado correctamente")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "No se pudo crear el modpack")


# ==================== PRUEBA INDEPENDIENTE ====================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = QMainWindow()
    window.setWindowTitle("ModerLauncher - Explorar Contenido")
    window.setGeometry(100, 100, 1120, 668)
    window.setStyleSheet("background-color: #1E1E1E;")
    
    mods_widget = ModsWindow(parent=window)
    window.setCentralWidget(mods_widget)
    
    window.show()
    sys.exit(app.exec_())