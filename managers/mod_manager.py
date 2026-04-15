"""
Gestor de Mods - Maneja la instalación, desinstalación y gestión de mods
"""
import os
import json
import shutil
from typing import List, Dict, Optional
from pathlib import Path


class ModInfo:
    """Información de un mod instalado"""
    def __init__(self, name: str, version: str, file_path: str, enabled: bool = True,
                 modrinth_id: str = None, description: str = ""):
        self.name = name
        self.version = version
        self.file_path = file_path
        self.enabled = enabled
        self.modrinth_id = modrinth_id
        self.description = description

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'file_path': self.file_path,
            'enabled': self.enabled,
            'modrinth_id': self.modrinth_id,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ModInfo':
        return cls(
            name=data.get('name', ''),
            version=data.get('version', ''),
            file_path=data.get('file_path', ''),
            enabled=data.get('enabled', True),
            modrinth_id=data.get('modrinth_id'),
            description=data.get('description', '')
        )


class ModManager:
    """Gestor principal de mods"""

    def __init__(self, minecraft_dir: str, profile_name: str = "default"):
        self.minecraft_dir = Path(minecraft_dir)
        self.profile_name = profile_name
        self.mods_dir = self.minecraft_dir / "mods"
        self.disabled_mods_dir = self.mods_dir / ".disabled"
        self.config_file = self.mods_dir / "mod_manager_config.json"

        # Crear directorios si no existen
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        self.disabled_mods_dir.mkdir(parents=True, exist_ok=True)

        # Cargar configuración
        self.installed_mods: Dict[str, ModInfo] = {}
        self.load_config()

    def load_config(self):
        """Cargar configuración de mods instalados"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for mod_id, mod_data in data.get('installed_mods', {}).items():
                        self.installed_mods[mod_id] = ModInfo.from_dict(mod_data)
            except Exception as e:
                print(f"Error cargando configuración de mods: {e}")

    def save_config(self):
        """Guardar configuración de mods"""
        data = {
            'installed_mods': {
                mod_id: mod.to_dict() for mod_id, mod in self.installed_mods.items()
            }
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración de mods: {e}")

    def scan_installed_mods(self) -> List[ModInfo]:
        """Escanear mods instalados en el directorio"""
        installed = []

        # Escanear mods habilitados
        if self.mods_dir.exists():
            for file_path in self.mods_dir.glob("*.jar"):
                if file_path.name.startswith('.'):
                    continue  # Ignorar archivos ocultos

                mod_name = file_path.stem
                mod_info = self.installed_mods.get(mod_name)
                if mod_info:
                    # Actualizar ruta si cambió
                    mod_info.file_path = str(file_path)
                    installed.append(mod_info)
                else:
                    # Crear entrada básica
                    mod_info = ModInfo(
                        name=mod_name,
                        version="Desconocida",
                        file_path=str(file_path),
                        enabled=True
                    )
                    self.installed_mods[mod_name] = mod_info
                    installed.append(mod_info)

        # Escanear mods deshabilitados
        if self.disabled_mods_dir.exists():
            for file_path in self.disabled_mods_dir.glob("*.jar"):
                mod_name = file_path.stem
                mod_info = self.installed_mods.get(mod_name)
                if mod_info:
                    mod_info.file_path = str(file_path)
                    mod_info.enabled = False
                    installed.append(mod_info)
                else:
                    mod_info = ModInfo(
                        name=mod_name,
                        version="Desconocida",
                        file_path=str(file_path),
                        enabled=False
                    )
                    self.installed_mods[mod_name] = mod_info
                    installed.append(mod_info)

        self.save_config()
        return installed

    def install_mod(self, mod_file_path: str, mod_info: Optional[ModInfo] = None) -> bool:
        """Instalar un mod desde un archivo"""
        try:
            mod_path = Path(mod_file_path)
            if not mod_path.exists():
                return False

            # Determinar nombre del mod
            mod_name = mod_info.name if mod_info else mod_path.stem

            # Copiar al directorio de mods
            target_path = self.mods_dir / f"{mod_name}.jar"
            counter = 1
            while target_path.exists():
                target_path = self.mods_dir / f"{mod_name}_{counter}.jar"
                counter += 1

            shutil.copy2(mod_path, target_path)

            # Crear información del mod
            if not mod_info:
                mod_info = ModInfo(
                    name=mod_name,
                    version="Desconocida",
                    file_path=str(target_path),
                    enabled=True
                )

            mod_info.file_path = str(target_path)
            self.installed_mods[mod_name] = mod_info
            self.save_config()

            return True
        except Exception as e:
            print(f"Error instalando mod: {e}")
            return False

    def uninstall_mod(self, mod_name: str) -> bool:
        """Desinstalar un mod"""
        try:
            if mod_name not in self.installed_mods:
                return False

            mod_info = self.installed_mods[mod_name]
            mod_path = Path(mod_info.file_path)

            # Eliminar archivo
            if mod_path.exists():
                mod_path.unlink()

            # Remover de la configuración
            del self.installed_mods[mod_name]
            self.save_config()

            return True
        except Exception as e:
            print(f"Error desinstalando mod: {e}")
            return False

    def toggle_mod(self, mod_name: str) -> bool:
        """Habilitar/deshabilitar un mod"""
        try:
            if mod_name not in self.installed_mods:
                return False

            mod_info = self.installed_mods[mod_name]
            mod_path = Path(mod_info.file_path)

            if mod_info.enabled:
                # Deshabilitar: mover a .disabled
                disabled_path = self.disabled_mods_dir / mod_path.name
                if mod_path.exists():
                    shutil.move(mod_path, disabled_path)
                    mod_info.file_path = str(disabled_path)
                mod_info.enabled = False
            else:
                # Habilitar: mover de vuelta a mods
                enabled_path = self.mods_dir / mod_path.name
                if mod_path.exists():
                    shutil.move(mod_path, enabled_path)
                    mod_info.file_path = str(enabled_path)
                mod_info.enabled = True

            self.save_config()
            return True
        except Exception as e:
            print(f"Error cambiando estado del mod: {e}")
            return False

    def get_mod_info(self, mod_name: str) -> Optional[ModInfo]:
        """Obtener información de un mod"""
        return self.installed_mods.get(mod_name)

    def get_all_mods(self) -> List[ModInfo]:
        """Obtener todos los mods instalados"""
        return list(self.installed_mods.values())
