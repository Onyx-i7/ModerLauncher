"""
Gestor de Modpacks - Maneja la creación, importación y gestión de modpacks
"""
import os
import json
import shutil
import zipfile
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


class ModpackInfo:
    """Información de un modpack"""
    def __init__(self, name: str, version: str, minecraft_version: str,
                 modloader: str, modloader_version: str, description: str = "",
                 author: str = "", created_date: str = None, mods: List[Dict] = None):
        self.name = name
        self.version = version
        self.minecraft_version = minecraft_version
        self.modloader = modloader
        self.modloader_version = modloader_version
        self.description = description
        self.author = author
        self.created_date = created_date or datetime.now().isoformat()
        self.mods = mods or []

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'minecraft_version': self.minecraft_version,
            'modloader': self.modloader,
            'modloader_version': self.modloader_version,
            'description': self.description,
            'author': self.author,
            'created_date': self.created_date,
            'mods': self.mods
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ModpackInfo':
        return cls(
            name=data.get('name', ''),
            version=data.get('version', ''),
            minecraft_version=data.get('minecraft_version', ''),
            modloader=data.get('modloader', ''),
            modloader_version=data.get('modloader_version', ''),
            description=data.get('description', ''),
            author=data.get('author', ''),
            created_date=data.get('created_date'),
            mods=data.get('mods', [])
        )


class ModpackManager:
    """Gestor principal de modpacks"""

    def __init__(self, minecraft_dir: str):
        self.minecraft_dir = Path(minecraft_dir)
        self.modpacks_dir = self.minecraft_dir.parent / "modpacks"
        self.config_file = self.modpacks_dir / "modpacks_config.json"

        # Crear directorios
        self.modpacks_dir.mkdir(parents=True, exist_ok=True)

        # Cargar configuración
        self.installed_modpacks: Dict[str, ModpackInfo] = {}
        self.load_config()

    def load_config(self):
        """Cargar configuración de modpacks"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pack_id, pack_data in data.get('installed_modpacks', {}).items():
                        self.installed_modpacks[pack_id] = ModpackInfo.from_dict(pack_data)
            except Exception as e:
                print(f"Error cargando configuración de modpacks: {e}")

    def save_config(self):
        """Guardar configuración de modpacks"""
        data = {
            'installed_modpacks': {
                pack_id: pack.to_dict() for pack_id, pack in self.installed_modpacks.items()
            }
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración de modpacks: {e}")

    def create_modpack(self, name: str, minecraft_version: str, modloader: str,
                      modloader_version: str, mods_dir: str, description: str = "",
                      author: str = "") -> Optional[str]:
        """Crear un nuevo modpack desde mods instalados"""
        try:
            # Generar ID único
            pack_id = f"{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"

            # Directorio del modpack
            pack_dir = self.modpacks_dir / pack_id
            pack_dir.mkdir(exist_ok=True)

            # Copiar mods
            mods_source = Path(mods_dir)
            mods_target = pack_dir / "mods"
            mods_target.mkdir(exist_ok=True)

            mods_list = []
            if mods_source.exists():
                for mod_file in mods_source.glob("*.jar"):
                    if not mod_file.name.startswith('.'):
                        shutil.copy2(mod_file, mods_target / mod_file.name)
                        mods_list.append({
                            'name': mod_file.stem,
                            'file': mod_file.name,
                            'enabled': True
                        })

            # Crear manifest
            manifest = {
                'name': name,
                'version': '1.0.0',
                'minecraft_version': minecraft_version,
                'modloader': modloader,
                'modloader_version': modloader_version,
                'description': description,
                'author': author,
                'created_date': datetime.now().isoformat(),
                'mods': mods_list
            }

            with open(pack_dir / 'manifest.json', 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            # Crear objeto ModpackInfo
            modpack_info = ModpackInfo(
                name=name,
                version='1.0.0',
                minecraft_version=minecraft_version,
                modloader=modloader,
                modloader_version=modloader_version,
                description=description,
                author=author,
                mods=mods_list
            )

            self.installed_modpacks[pack_id] = modpack_info
            self.save_config()

            return pack_id
        except Exception as e:
            print(f"Error creando modpack: {e}")
            return None

    def import_modpack(self, zip_path: str) -> Optional[str]:
        """Importar un modpack desde un archivo ZIP"""
        try:
            zip_path = Path(zip_path)
            if not zip_path.exists():
                return None

            # Generar ID único
            pack_id = f"imported_{int(datetime.now().timestamp())}"

            # Extraer ZIP
            pack_dir = self.modpacks_dir / pack_id
            pack_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(pack_dir)

            # Leer manifest
            manifest_path = pack_dir / 'manifest.json'
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)

                modpack_info = ModpackInfo.from_dict(manifest)
                self.installed_modpacks[pack_id] = modpack_info
                self.save_config()

                return pack_id
            else:
                # Crear manifest básico si no existe
                modpack_info = ModpackInfo(
                    name=zip_path.stem,
                    version='1.0.0',
                    minecraft_version='Desconocida',
                    modloader='Desconocido',
                    modloader_version='Desconocida',
                    description='Modpack importado'
                )
                self.installed_modpacks[pack_id] = modpack_info
                self.save_config()

                return pack_id
        except Exception as e:
            print(f"Error importando modpack: {e}")
            return None

    def export_modpack(self, pack_id: str, export_path: str) -> bool:
        """Exportar un modpack a un archivo ZIP"""
        try:
            if pack_id not in self.installed_modpacks:
                return False

            pack_dir = self.modpacks_dir / pack_id
            if not pack_dir.exists():
                return False

            export_path = Path(export_path)
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for file_path in pack_dir.rglob('*'):
                    if file_path.is_file():
                        zip_ref.write(file_path, file_path.relative_to(pack_dir))

            return True
        except Exception as e:
            print(f"Error exportando modpack: {e}")
            return False

    def install_modpack(self, pack_id: str, target_mods_dir: str) -> bool:
        """Instalar un modpack en el directorio de mods"""
        try:
            if pack_id not in self.installed_modpacks:
                return False

            pack_dir = self.modpacks_dir / pack_id
            if not pack_dir.exists():
                return False

            # Limpiar directorio de mods actual
            target_dir = Path(target_mods_dir)
            if target_dir.exists():
                for file in target_dir.glob("*.jar"):
                    file.unlink()

            # Copiar mods del modpack
            mods_source = pack_dir / "mods"
            if mods_source.exists():
                for mod_file in mods_source.glob("*.jar"):
                    shutil.copy2(mod_file, target_dir / mod_file.name)

            return True
        except Exception as e:
            print(f"Error instalando modpack: {e}")
            return False

    def delete_modpack(self, pack_id: str) -> bool:
        """Eliminar un modpack"""
        try:
            if pack_id not in self.installed_modpacks:
                return False

            pack_dir = self.modpacks_dir / pack_id
            if pack_dir.exists():
                shutil.rmtree(pack_dir)

            del self.installed_modpacks[pack_id]
            self.save_config()

            return True
        except Exception as e:
            print(f"Error eliminando modpack: {e}")
            return False

    def get_modpack_info(self, pack_id: str) -> Optional[ModpackInfo]:
        """Obtener información de un modpack"""
        return self.installed_modpacks.get(pack_id)

    def get_all_modpacks(self) -> List[ModpackInfo]:
        """Obtener todos los modpacks"""
        return list(self.installed_modpacks.values())

    def scan_modpacks(self) -> List[ModpackInfo]:
        """Escanear modpacks en el directorio"""
        scanned = []

        if self.modpacks_dir.exists():
            for pack_dir in self.modpacks_dir.iterdir():
                if pack_dir.is_dir() and not pack_dir.name.startswith('.'):
                    manifest_path = pack_dir / 'manifest.json'
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                                modpack_info = ModpackInfo.from_dict(manifest)
                                self.installed_modpacks[pack_dir.name] = modpack_info
                                scanned.append(modpack_info)
                        except Exception as e:
                            print(f"Error leyendo manifest de {pack_dir.name}: {e}")

        self.save_config()
        return scanned
