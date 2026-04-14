import sys
import os
import json
import uuid
import shutil
import subprocess
from threading import Thread
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import minecraft_launcher_lib
from pygame import mixer
from utils.resource_manager import get_local_data_dir, get_minecraft_dir


# ==================== VERSION MANAGER ====================

class VersionManager:
    def __init__(self):
        self.minecraft_directory = get_local_data_dir('moderlauncher')
        self.installed_versions = self.load_installed_versions()
        self.cancelled = False
        
        # Crear directorios iniciales
        self.create_initial_directories()
    
    def create_initial_directories(self):
        """Crear directorios necesarios"""
        directories = [
            self.minecraft_directory,
            os.path.join(self.minecraft_directory, 'versions'),
            os.path.join(self.minecraft_directory, 'assets'),
            os.path.join(self.minecraft_directory, 'libraries'),
            os.path.join(self.minecraft_directory, 'natives'),
            os.path.join(self.minecraft_directory, 'runtime')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def load_installed_versions(self):
        """Cargar versiones instaladas"""
        versions_dir = os.path.join(self.minecraft_directory, 'versions')
        installed = {}
        
        if os.path.exists(versions_dir):
            for version in os.listdir(versions_dir):
                version_dir = os.path.join(versions_dir, version)
                if os.path.isdir(version_dir):
                    jar_path = os.path.join(version_dir, f"{version}.jar")
                    json_path = os.path.join(version_dir, f"{version}.json") # Corregido
                    if os.path.exists(jar_path) and os.path.exists(json_path): # Corregido
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                version_info = json.load(f)
                            installed[version] = {
                                "id": version_info.get("id", version),
                                "type": version_info.get("type", "release"),
                                "releaseTime": version_info.get("releaseTime", ""),
                                "installed": True
                            }
                        except Exception as e:
                            print(f"Error leyendo JSON para {version}: {e}")
        return installed
    
    def is_version_installed(self, version):
        """Verificar si una versión está instalada"""
        return version in self.installed_versions
    
    def remove_version(self, version):
        """Eliminar una versión"""
        if version in self.installed_versions:
            version_path = os.path.join(self.minecraft_directory, "versions", version)
            if os.path.exists(version_path):
                shutil.rmtree(version_path)
            del self.installed_versions[version]
    
    def refresh_installed_versions(self):
        """Actualizar lista de versiones instaladas"""
        self.installed_versions = self.load_installed_versions()
        return self.installed_versions
    
    def get_version_type(self, version):
        """Determinar tipo de versión"""
        version_dir = os.path.join(self.minecraft_directory, "versions", version)
        if os.path.exists(os.path.join(version_dir, f"{version}-forge.jar")):
            return "forge"
        elif os.path.exists(os.path.join(version_dir, f"{version}-fabric.jar")):
            return "fabric"
        return "vanilla"
    
    def get_installed_version(self):
        """Retornar la última versión instalada"""
        installed = [v for v in self.installed_versions.keys()]
        return installed[-1] if installed else None


# ==================== CARGADOR DE VERSIONES ====================

class VersionListLoader(QThread):
    """Hilo para cargar lista de versiones de Minecraft sin bloquear la UI"""
    versions_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._is_cancelled = False
    
    def cancel(self):
        """Cancelar carga"""
        self._is_cancelled = True
    
    def run(self):
        try:
            if not self._is_cancelled:
                print("⏳ [GameWindow] Cargando lista de versiones de Minecraft...")
                versions = minecraft_launcher_lib.utils.get_version_list()
                
                if not self._is_cancelled:
                    print(f"✅ [GameWindow] {len(versions)} versiones cargadas")
                    self.versions_loaded.emit(versions)
                else:
                    print("❌ [GameWindow] Carga cancelada")
        except Exception as e:
            print(f"❌ [GameWindow] Error cargando versiones: {e}")
            if not self._is_cancelled:
                self.error_occurred.emit(f"Error de red: {str(e)}")


# ==================== WORKER DE DESCARGA ====================

class DownloadWorker(QThread):
    """Worker para descargar versiones en segundo plano"""
    progress_update = pyqtSignal(int, str, dict)
    download_complete = pyqtSignal(str)
    download_error = pyqtSignal(str)
    
    def __init__(self, version, minecraft_dir):
        super().__init__()
        self.version = version
        self.minecraft_dir = minecraft_dir
        self.current_max = 0
        self.current_downloaded_bytes = 0 # Para un seguimiento más detallado
        self.cancelled = False # Flag to allow external cancellation
        
    def run(self):
        try:
            def set_status(text):
                self.progress_update.emit(0, text, {})
            
            def set_progress(value):
                if self.cancelled:
                    print(f"[DownloadWorker] Progreso ignorado, descarga cancelada para {self.version}.")
                    return
                
                self.current_downloaded_bytes = value
                if self.current_max > 0:
                    percentage = int((value / self.current_max) * 100)
                    self.progress_update.emit(percentage, "Descargando...", {
                        "percentage": percentage,
                        "current": value,
                        "total": self.current_max,
                        "version": self.version # Añadir versión para contexto
                    })
                else:
                    # Si current_max es 0, emitir progreso con 0%
                    self.progress_update.emit(0, "Descargando...", {"current": value, "total": self.current_max, "version": self.version})
            
            def set_max(maximum):
                self.current_max = maximum
                print(f"[DownloadWorker] Max progress set to: {maximum} bytes para {self.version}")

            print(f"[DownloadWorker] Starting install for version: {self.version} in {self.minecraft_dir}") # Add logging
            
            if self.cancelled: # Check for cancellation before starting
                raise Exception("Descarga cancelada")
            minecraft_launcher_lib.install.install_minecraft_version(
                self.version,
                # Asegúrate de que self.minecraft_dir sea la ruta correcta (.moderlauncher)
                self.minecraft_dir,
                callback={
                    "setStatus": set_status,
                    "setProgress": set_progress,
                    "setMax": set_max
                }
            )

            if self.cancelled: # Check for cancellation after install (if it was partial)
                raise Exception("Descarga cancelada")
            
            # --- NUEVA VERIFICACIÓN DE ARCHIVOS CRÍTICOS ---
            version_jar_path = os.path.join(self.minecraft_dir, "versions", self.version, f"{self.version}.jar")
            version_json_path = os.path.join(self.minecraft_dir, "versions", self.version, f"{self.version}.json")

            if not os.path.exists(version_jar_path) or not os.path.exists(version_json_path):
                print(f"[DownloadWorker] ERROR: Archivos JAR o JSON no encontrados después de la instalación para {self.version}")
                raise Exception(f"La instalación de {self.version} parece incompleta. Archivos principales no encontrados.")
            # --- FIN NUEVA VERIFICACIÓN ---

            self.download_complete.emit(self.version)
            print(f"[DownloadWorker] Instalación completa y verificada para {self.version}")
        except Exception as e:
            self.download_error.emit(str(e))


# ==================== WORKER PARA FABRIC ====================

class FabricInstallWorker(QThread):
    """Worker para instalar Fabric"""
    install_complete = pyqtSignal(str)
    install_error = pyqtSignal(str)
    
    def __init__(self, mc_version, fabric_version, minecraft_dir):
        super().__init__()
        self.mc_version = mc_version
        self.fabric_version = fabric_version
        self.minecraft_dir = minecraft_dir
    
    def run(self):
        try:
            minecraft_launcher_lib.fabric.install_fabric(
                self.mc_version,
                self.minecraft_dir,
                loader_version=self.fabric_version
            )
            self.install_complete.emit(f"fabric-loader-{self.fabric_version}-{self.mc_version}")
        except Exception as e:
            self.install_error.emit(str(e))


# ==================== WORKER PARA FORGE ====================

class ForgeInstallWorker(QThread):
    """Worker para instalar Forge"""
    install_complete = pyqtSignal(str)
    install_error = pyqtSignal(str)
    
    def __init__(self, mc_version, forge_version, minecraft_dir):
        super().__init__()
        self.mc_version = mc_version
        self.forge_version = forge_version
        self.minecraft_dir = minecraft_dir
    
    def run(self):
        try:
            minecraft_launcher_lib.forge.install_forge_version(
                self.forge_version,
                self.minecraft_dir
            )
            self.install_complete.emit(f"{self.mc_version}-forge-{self.forge_version}")
        except Exception as e:
            self.install_error.emit(str(e))


# ==================== TARJETA DE VERSIÓN ====================

class VersionCard(QFrame):
    """Tarjeta individual para cada versión"""
    download_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    
    def __init__(self, version_data, is_installed=False, parent=None):
        super().__init__(parent)
        self.version_data = version_data
        self.version_id = version_data.get('id', 'Unknown')
        self.version_type = version_data.get('type', 'release')
        self.is_installed = is_installed
        
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedSize(280, 140)
        self.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-radius: 10px;
                border: 1px solid #3C3C41;
            }
            QFrame:hover {
                border-color: #4CAF50;
                background-color: #2A2A2A;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Header con versión y badge
        header_layout = QHBoxLayout()
        
        # Versión
        version_label = QLabel(f"Minecraft {self.version_id}")
        version_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        version_label.setStyleSheet("color: white; background: transparent; border: none;")
        header_layout.addWidget(version_label)
        
        header_layout.addStretch()
        
        # Badge de tipo
        badge_colors = {
            "release": "#4CAF50",
            "snapshot": "#FF9800",
            "old_beta": "#2196F3",
            "old_alpha": "#9C27B0"
        }
        
        badge_text = {
            "release": "RELEASE",
            "snapshot": "SNAPSHOT",
            "old_beta": "BETA",
            "old_alpha": "ALPHA"
        }
        
        badge_color = badge_colors.get(self.version_type, "#666666")
        if self.version_type == "release":
            bg = "#000000"
            fg = "#FFFFFF"
        else:
            bg = badge_color
            fg = "white"

        badge_label = QLabel(badge_text.get(self.version_type, "OTHER"))
        badge_label.setFixedSize(75, 20)
        badge_label.setAlignment(Qt.AlignCenter)
        badge_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 10px;
                font-size: 9px;
                font-weight: bold;
                border: none;
            }}
        """)
        header_layout.addWidget(badge_label)
        
        layout.addLayout(header_layout)
        
        # Fecha de lanzamiento
        release_time = self.version_data.get('releaseTime', '')
        if release_time:
            try:
                if isinstance(release_time, datetime):
                    date_str = release_time.strftime('%Y-%m-%d')
                elif isinstance(release_time, str):
                    date_str = release_time.split('T')[0]
                else:
                    date_str = str(release_time)[:10]
                
                date_label = QLabel(f"📅 {date_str}")
                date_label.setStyleSheet("color: #888888; font-size: 10px; background: transparent; border: none;")
                layout.addWidget(date_label)
            except:
                pass
        
        layout.addStretch()
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        if self.is_installed:
            status = QLabel("✓ Instalado")
            status.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                }
            """)
            button_layout.addWidget(status)
            
            button_layout.addStretch()
            
            delete_btn = QPushButton("Eliminar")
            delete_btn.setFixedSize(90, 32)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
                QPushButton:pressed {
                    background-color: #B71C1C;
                }
            """)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.version_id))
            button_layout.addWidget(delete_btn)
        else:
            button_layout.addStretch()
            
            download_btn = QPushButton("Descargar")
            download_btn.setFixedSize(100, 32)
            download_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3d8c40;
                }
                QPushButton:pressed {
                    background-color: #2d7030;
                }
            """)
            download_btn.setCursor(Qt.PointingHandCursor)
            download_btn.clicked.connect(lambda: self.download_clicked.emit(self.version_id))
            button_layout.addWidget(download_btn)
        
        layout.addLayout(button_layout)


# ==================== DIÁLOGO DE DESCARGA ====================

class DownloadDialog(QDialog):
    """Diálogo de progreso de descarga"""
    download_finished = pyqtSignal(bool, str) # True for success, False for error, and message

    def __init__(self, version, parent=None):
        super().__init__(parent)
        self.version = version
        self.setup_ui()
        self.result_success = False
        self.result_message = ""
    
    def setup_ui(self):
        self.setWindowTitle("Descargando Minecraft")
        self.setFixedSize(450, 220)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                border: 2px solid #3C3C41;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title = QLabel(f"Descargando Minecraft {self.version}")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2A2A2A;
                border: none;
                border-radius: 12px;
                text-align: center;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 12px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.percent_label = QLabel("0%")
        self.percent_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.percent_label.setStyleSheet("color: #4CAF50; background: transparent;")
        self.percent_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.percent_label)
        
        self.status_label = QLabel("Iniciando descarga...")
        self.status_label.setStyleSheet("color: #AAAAAA; font-size: 11px; background: transparent;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def update_progress(self, percentage, status, extra):
        """Actualizar progreso"""
        self.progress_bar.setValue(percentage)
        self.percent_label.setText(f"{percentage}%")
        self.status_label.setText(status)


# ==================== DIÁLOGO DE VERSIÓN CUSTOM ====================

class CustomVersionDialog(QDialog):
    """Diálogo para crear versión personalizada"""
    version_created = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.minecraft_dir = get_minecraft_dir()
        self.setup_ui()
    
    def setup_ui(self):
        self.setMinimumSize(500, 520)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                border: 2px solid #3C3C41;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        title = QLabel("Crear Versión Personalizada")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        name_label = QLabel("Nombre de la Versión")
        name_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Mi Modpack Personalizado")
        self.name_input.setFixedHeight(45)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #3C3C41;
                color: white;
                border: 2px solid #3C3C41;
                border-radius: 10px;
                padding: 0 18px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: #424245;
            }
        """)
        layout.addWidget(self.name_input)
        
        layout.addSpacing(10)
        
        mc_label = QLabel("Versión de Minecraft")
        mc_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(mc_label)
        
        self.mc_combo = QComboBox()
        self.mc_combo.setFixedHeight(45)
        self.mc_combo.setStyleSheet("""
            QComboBox {
                background-color: #3C3C41;
                color: white;
                border: 2px solid #3C3C41;
                border-radius: 10px;
                padding: 0 18px;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #4CAF50;
                background-color: #424245;
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #E0E0E0;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #3C3C41;
                color: white;
                selection-background-color: #4CAF50;
                border: 2px solid #3C3C41;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        self.load_minecraft_versions()
        layout.addWidget(self.mc_combo)
        
        layout.addSpacing(10)
        
        loader_label = QLabel("Mod Loader")
        loader_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(loader_label)
        
        loader_layout = QHBoxLayout()
        loader_layout.setSpacing(15)
        
        self.fabric_radio = QRadioButton("Fabric")
        self.fabric_radio.setStyleSheet("""
            QRadioButton {
                color: white;
                font-size: 14px;
                background: transparent;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid #3C3C41;
                background-color: #2D2D30;
            }
            QRadioButton::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QRadioButton::indicator:hover {
                border-color: #4CAF50;
            }
        """)
        self.fabric_radio.setChecked(False)
        loader_layout.addWidget(self.fabric_radio)
        
        self.forge_radio = QRadioButton("Forge")
        self.forge_radio.setStyleSheet(self.fabric_radio.styleSheet())
        self.forge_radio.setChecked(True)
        loader_layout.addWidget(self.forge_radio)
        
        loader_layout.addStretch()
        layout.addLayout(loader_layout)
        
        layout.addSpacing(10)
        
        loader_ver_label = QLabel("Versión del Loader")
        loader_ver_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(loader_ver_label)
        
        self.loader_combo = QComboBox()
        self.loader_combo.setFixedHeight(45)
        self.loader_combo.setStyleSheet(self.mc_combo.styleSheet())
        layout.addWidget(self.loader_combo)
        
        self.fabric_radio.toggled.connect(self.on_loader_changed)
        self.forge_radio.toggled.connect(self.on_loader_changed)
        self.mc_combo.currentTextChanged.connect(self.on_mc_version_changed)
        
        self.on_loader_changed()
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(50)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C41;
                color: #E0E0E0;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4A4A4F;
            }
            QPushButton:pressed {
                background-color: #55555A;
            }
        """)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Crear Versión")
        create_btn.setFixedHeight(50)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #3D8B40;
            }
        """)
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.clicked.connect(self.create_version)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def load_minecraft_versions(self):
        """Cargar versiones de Minecraft"""
        try:
            versions = minecraft_launcher_lib.utils.get_version_list()
            release_versions = [v['id'] for v in versions if v['type'] == 'release']
            self.mc_combo.addItems(release_versions[:20])
        except:
            self.mc_combo.addItems(["1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"])
    
    def on_loader_changed(self):
        """Cambiar loader"""
        self.loader_combo.clear()
        mc_version = self.mc_combo.currentText()
        
        if self.fabric_radio.isChecked():
            self.load_fabric_versions(mc_version)
        else:
            self.load_forge_versions(mc_version)
    
    def on_mc_version_changed(self):
        """Cambiar versión de Minecraft"""
        self.on_loader_changed()
    
    def load_fabric_versions(self, mc_version):
        """Cargar versiones de Fabric"""
        try:
            loaders = minecraft_launcher_lib.fabric.get_all_loader_versions()
            self.loader_combo.addItems([l['version'] for l in loaders[:10]])
        except:
            self.loader_combo.addItem("0.14.21")
    
    def load_forge_versions(self, mc_version):
        """Cargar versiones de Forge"""
        try:
            forge_versions = minecraft_launcher_lib.forge.find_forge_version(mc_version)
            if forge_versions:
                self.loader_combo.addItems(forge_versions[:10])
            else:
                self.loader_combo.addItem("Forge no disponible")
        except:
            self.loader_combo.addItem("47.1.0")
    
    def create_version(self):
        """Crear versión personalizada"""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Ingresa un nombre para la versión")
            return
        
        mc_version = self.mc_combo.currentText()
        loader_version = self.loader_combo.currentText()
        
        progress = QProgressDialog("Creando versión personalizada...", None, 0, 0, self)
        progress.setWindowTitle("Instalando")
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()
        
        def on_complete(version_id):
            progress.close()
            QMessageBox.information(self, "Éxito", f"Versión '{name}' creada correctamente")
            self.version_created.emit(version_id)
            self.accept()
        
        def on_error(error):
            progress.close()
            QMessageBox.critical(self, "Error", f"Error al crear versión:\n{error}")
        
        if self.fabric_radio.isChecked():
            worker = FabricInstallWorker(mc_version, loader_version, self.minecraft_dir)
        else:
            worker = ForgeInstallWorker(mc_version, loader_version, self.minecraft_dir)
        
        worker.install_complete.connect(on_complete)
        worker.install_error.connect(on_error)
        worker.start()


# ==================== MENSAJE MODERNO ====================

class ModernDialog(QDialog):
    def __init__(self, title, message, icon_type="info", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setupUi(title, message, icon_type)
        
    def setupUi(self, title, message, icon_type):
        # Contenedor principal con sombra
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Widget contenedor con fondo y bordes redondeados
        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            #container {
                background-color: #252526;
                border: 2px solid #3C3C41;
                border-radius: 15px;
            }
        """)
        
        # Layout del contenedor
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Icono y título
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        if icon_type == "success":
            icon_text = "✅"
        elif icon_type == "error":
            icon_text = "❌"
        elif icon_type == "question":
            icon_text = "❓"
        else:
            icon_text = "ℹ️"
        
        icon_label.setText(icon_text)
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Mensaje
        message_label = QLabel(message)
        message_label.setFont(QFont("Segoe UI", 12))
        message_label.setStyleSheet("color: #CCCCCC; background: transparent;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        layout.addStretch()
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.button_accept = QPushButton("Aceptar")
        self.button_accept.setFixedSize(120, 40)
        self.button_accept.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        if icon_type == "question":
            self.button_cancel = QPushButton("Cancelar")
            self.button_cancel.setFixedSize(120, 40)
            self.button_cancel.setStyleSheet("""
                QPushButton {
                    background-color: #555555;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #666666;
                }
                QPushButton:pressed {
                    background-color: #444444;
                }
            """)
            button_layout.addWidget(self.button_cancel)
            button_layout.addSpacing(10)
            self.button_cancel.clicked.connect(self.reject)
        
        button_layout.addWidget(self.button_accept)
        self.button_accept.clicked.connect(self.accept)
        
        layout.addLayout(button_layout)
        main_layout.addWidget(container)
        
        # Tamaño
        self.setFixedSize(400, 250)
        
        # Centrar en la pantalla - CORREGIDO
        center = QDesktopWidget().availableGeometry().center()
        x = int(center.x() - self.width() * 0.5)  # Convertir a int
        y = int(center.y() - self.height() * 0.5)  # Convertir a int
        self.move(x, y)

# Mover el método download_version y show_error_dialog a la clase GameWindow
class GameWindow(QWidget):
    """Ventana principal de gestión de versiones - AUTÓNOMA como ModsWindow"""
    
    def __init__(self, initial_data=None, parent=None, version_callback=None, refresh_callback=None, launcher=None):
        super().__init__(parent)
        
        # Configuración inicial
        self.version_manager = VersionManager()
        self.version_callback = version_callback
        self.refresh_callback = refresh_callback
        self.launcher = launcher
        self.all_versions = initial_data
        self.version_loader = None
        self.download_workers = []
        
        # Audio
        mixer.init()
        try:
            self.delete_sound = mixer.Sound(os.path.join(os.path.dirname(__file__), 'sonidos', 'basura.mp3'))
            self.delete_sound.set_volume(0.5)
        except:
            self.delete_sound = None
        
        # Ajustar al parent
        if parent:
            self.setGeometry(0, 0, parent.width(), parent.height())
        
        # Configurar UI
        self.setup_ui()
        
        # Cargar datos
        if initial_data:
            print("✅ [GameWindow] Usando datos pre-cargados")
            self.display_versions()
        else:
            print("🔄 [GameWindow] Cargando versiones por sí mismo...")
            self.load_versions()

    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QFrame()
        header.setFixedHeight(90)
        header.setStyleSheet("""
            QFrame {
                background-color: #1A2327;
                border-radius: 10px;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 15, 25, 15)
        
        title = QLabel("🎮 Gestor de Versiones de Minecraft")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botón de versión custom
        custom_btn = QPushButton("+ Crear Personalizada")
        custom_btn.setFixedSize(180, 45)
        custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        custom_btn.setCursor(Qt.PointingHandCursor)
        custom_btn.clicked.connect(self.show_custom_dialog)
        header_layout.addWidget(custom_btn)
        
        layout.addWidget(header)
        
        # Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background-color: #252526;
                border-radius: 8px;
                border: 1px solid #3C3C41;
            }
            QTabBar::tab {
                background-color: #2D2D30;
                color: #AAAAAA;
                padding: 14px 50px;
                min-width: 100px;
                min-height: 40px;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #252526;
                color: white;
                border-bottom: 3px solid #4CAF50;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3C3C41;
            }
        """)
        
        # Scroll area para vanilla
        vanilla_scroll = QScrollArea()
        vanilla_scroll.setWidgetResizable(True)
        vanilla_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2D2D30;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4CAF50;
                border-radius: 6px;
            }
        """)
        
        # Contenedor para versiones vanilla
        vanilla_container = QWidget()
        self.vanilla_layout = QGridLayout(vanilla_container)
        self.vanilla_layout.setSpacing(15)
        self.vanilla_layout.setContentsMargins(10, 10, 10, 10)
        vanilla_scroll.setWidget(vanilla_container)
        
        # Scroll area para instaladas
        installed_scroll = QScrollArea()
        installed_scroll.setWidgetResizable(True)
        installed_scroll.setStyleSheet(vanilla_scroll.styleSheet())
        
        # Contenedor para versiones instaladas
        installed_container = QWidget()
        self.installed_layout = QGridLayout(installed_container)
        self.installed_layout.setSpacing(15)
        self.installed_layout.setContentsMargins(10, 10, 10, 10)
        installed_scroll.setWidget(installed_container)
        
        # Añadir tabs con sus scroll areas
        self.tab_widget.addTab(vanilla_scroll, "VANILLA")
        self.tab_widget.addTab(installed_scroll, "INSTALADAS")
        
        # Conectar cambio de tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)

    def show_custom_dialog(self):
        """Mostrar diálogo de versión personalizada"""
        dialog = CustomVersionDialog(self)
        dialog.version_created.connect(self.on_version_created)
        dialog.exec_()

    def on_version_created(self, version_id):
        """Callback cuando se crea una versión personalizada"""
        self.version_manager.refresh_installed_versions()
        self.populate_installed_tab()
        if self.version_callback:
            self.version_callback(version_id)

    def on_tab_changed(self, index):
        """Callback cuando se cambia de pestaña"""
        if index == 1:  # Pestaña de instaladas
            self.populate_installed_tab()

    def download_version(self, version):
        """Descargar versión"""
        try:
            dialog = DownloadDialog(version, self)
            dialog.show()
            
            def on_progress(percentage, status, extra):
                try:
                    dialog.update_progress(percentage, status, extra)
                except Exception as e:
                    print(f"Error actualizando progreso: {e}")
            
            def on_complete(ver):
                try:
                    dialog.accept()
                    success_dialog = ModernDialog(
                        "Descarga Completada",
                        f"Minecraft {ver} se ha instalado correctamente.",
                        "success",
                        self
                    )
                    success_dialog.exec_()
                    
                    if worker in self.download_workers:
                        self.download_workers.remove(worker)
                    
                    self.version_manager.refresh_installed_versions()
                    self.apply_filters()
                    self.populate_installed_tab()
                    
                    if self.version_callback:
                        self.version_callback(ver)
                        
                except Exception as e:
                    print(f"Error en on_complete: {e}")
                    self.show_error_dialog(f"Error al finalizar la descarga: {e}")
            
            def on_error(error):
                try:
                    dialog.reject()
                    error_dialog = ModernDialog(
                        "Error de Descarga",
                        f"No se pudo descargar la versión:\n{error}",
                        "error",
                        self
                    )
                    error_dialog.exec_()
                    
                    if worker in self.download_workers:
                        self.download_workers.remove(worker)
                        
                except Exception as e:
                    print(f"Error en on_error: {e}")
                    self.show_error_dialog(f"Error al mostrar error de descarga: {e}")
            
            worker = DownloadWorker(version, self.version_manager.minecraft_directory)
            worker.progress_update.connect(on_progress)
            worker.download_complete.connect(on_complete)
            worker.download_error.connect(on_error)
            worker.start()
            
            self.download_workers.append(worker)
            
        except Exception as e:
            print(f"Error iniciando descarga: {e}")
            self.show_error_dialog(f"Error al iniciar la descarga: {e}")

    def show_error_dialog(self, message):
        """Método auxiliar para mostrar errores de forma segura"""
        try:
            error_dialog = ModernDialog(
                "Error",
                message,
                "error",
                self
            )
            error_dialog.exec_()
        except Exception as e:
            print(f"Error mostrando diálogo de error: {e}")
            QMessageBox.critical(self, "Error", message)

    def display_versions(self):
        """Mostrar versiones en la interfaz"""
        self.clear_version_cards()
        self.apply_filters()
    
    def clear_version_cards(self):
        """Limpiar tarjetas de versiones"""
        while self.vanilla_layout.count():
            item = self.vanilla_layout.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
    
    def apply_filters(self):
        """Aplicar filtros a las versiones"""
        # Comprobar si tenemos versiones
        if not self.all_versions:
            return
        
        # Crear área de filtros si no existe
        if not hasattr(self, 'filter_layout'):
            filter_layout = QHBoxLayout()
            
            # Label de filtro
            filter_label = QLabel("Filtrar:")
            filter_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
            filter_layout.addWidget(filter_label)
            
            # Checkbox para releases
            self.filter_release = QCheckBox("Releases")
            self.filter_release.setChecked(True)
            self.filter_release.setStyleSheet("color: white; font-size: 12px;")
            filter_layout.addWidget(self.filter_release)
            
            # Checkbox para snapshots
            self.filter_snapshot = QCheckBox("Snapshots")
            self.filter_snapshot.setStyleSheet("color: white; font-size: 12px;")
            filter_layout.addWidget(self.filter_snapshot)
            
            # Checkbox para versiones antiguas
            self.filter_old = QCheckBox("Versiones Antiguas")
            self.filter_old.setStyleSheet("color: white; font-size: 12px;")
            filter_layout.addWidget(self.filter_old)
            
            filter_layout.addStretch()
            
            # Label contador de versiones
            self.version_count_label = QLabel("Cargando...")
            self.version_count_label.setStyleSheet("color: #888888; font-size: 12px;")
            filter_layout.addWidget(self.version_count_label)
            
            # Añadir layout de filtros
            self.vanilla_layout.addLayout(filter_layout, 0, 0, 1, 3)
            
            # Conectar señales de filtros
            self.filter_release.toggled.connect(self.apply_filters)
            self.filter_snapshot.toggled.connect(self.apply_filters)
            self.filter_old.toggled.connect(self.apply_filters)
        
        # Filtrar versiones
        filtered_versions = []
        for version in self.all_versions:
            version_type = version.get('type', '')
            
            if version_type == 'release' and self.filter_release.isChecked():
                filtered_versions.append(version)
            elif version_type == 'snapshot' and self.filter_snapshot.isChecked():
                filtered_versions.append(version)
            elif version_type in ['old_beta', 'old_alpha'] and self.filter_old.isChecked():
                filtered_versions.append(version)
        
        # Actualizar contador
        self.version_count_label.setText(f"Mostrando {len(filtered_versions)} versiones")
        
        # Crear cards
        row, col = 1, 0  # Empezar en fila 1 por los filtros
        for version_data in filtered_versions:
            version_id = version_data['id']
            is_installed = self.version_manager.is_version_installed(version_id)
            
            card = VersionCard(version_data, is_installed)
            card.download_clicked.connect(self.download_version)
            card.delete_clicked.connect(self.delete_version)
            
            self.vanilla_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
    
    def load_versions(self):
        """Cargar versiones de Minecraft"""
        if self.version_loader and self.version_loader.isRunning():
            print("⚠️ Ya hay una carga en curso")
            return
        
        self.clear_version_cards()
        self.show_loading_indicator()
        
        # Crear y ejecutar el hilo de carga
        self.version_loader = VersionListLoader()
        self.version_loader.versions_loaded.connect(self.on_versions_loaded)
        self.version_loader.error_occurred.connect(self.on_load_error)
        self.version_loader.start()
    
    def show_loading_indicator(self):
        """Mostrar indicador de carga"""
        loading_label = QLabel("🔄 Cargando versiones de Minecraft...")
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
        self.vanilla_layout.addWidget(loading_label, 0, 0, 1, 3)
    
    def on_versions_loaded(self, versions_data):
        """Callback cuando se cargan las versiones"""
        self.all_versions = versions_data
        self.display_versions()
    
    def on_load_error(self, error_message):
        """Callback cuando ocurre un error al cargar"""
        self.clear_version_cards()
        
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
        self.vanilla_layout.addWidget(error_label, 0, 0, 1, 3)

    def delete_version(self, version):
        """Eliminar una versión"""
        try:
            confirm_dialog = ModernDialog(
                "Confirmar Eliminación",
                f"¿Estás seguro de que deseas eliminar Minecraft {version}?",
                "question",
                self
            )
            
            if confirm_dialog.exec_() == QDialog.Accepted:
                self.version_manager.remove_version(version)
                self.version_manager.refresh_installed_versions()
                
                if self.delete_sound:
                    try:
                        self.delete_sound.play()
                    except:
                        pass
                
                success_dialog = ModernDialog(
                    "Versión Eliminada",
                    f"Minecraft {version} se ha eliminado correctamente.",
                    "success",
                    self
                )
                success_dialog.exec_()
                
                self.apply_filters()
                
                if self.refresh_callback:
                    self.refresh_callback()
        
        except Exception as e:
            print(f"Error eliminando versión: {e}")
            self.show_error_dialog(f"Error al eliminar la versión: {e}")
    
    def populate_installed_tab(self):
        """Poblar la pestaña de versiones instaladas"""
        # Clear existing cards
        while self.installed_layout.count():
            item = self.installed_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get installed versions
        installed_versions = self.version_manager.refresh_installed_versions()
        
        if not installed_versions:
            no_versions_label = QLabel("No tienes ninguna versión instalada.")
            no_versions_label.setStyleSheet("color: #888888; font-size: 16px; padding: 80px;")
            no_versions_label.setAlignment(Qt.AlignCenter)
            self.installed_layout.addWidget(no_versions_label, 0, 0, 1, 3)
            return
        
        # Create cards for installed versions
        row, col = 0, 0
        for version_id in sorted(installed_versions.keys(), reverse=True):
            version_data = installed_versions[version_id]
            card = VersionCard(version_data, is_installed=True)
            card.delete_clicked.connect(self.delete_version)
            
            self.installed_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1

# Exportar las clases principales
__all__ = ['GameWindow', 'VersionManager']

# Eliminar el bloque if __name__ == "__main__": ya que no lo necesitamos para importar