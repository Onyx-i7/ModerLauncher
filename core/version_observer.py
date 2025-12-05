"""
Version Observer - Observa cambios en las versiones instaladas de Minecraft
"""
import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


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