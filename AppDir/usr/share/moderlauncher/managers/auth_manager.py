import json
import os
import uuid
import base64
import hashlib
import requests
from cryptography.fernet import Fernet
import certifi
import time
from datetime import datetime, timedelta
from utils.resource_manager import get_local_data_dir

class AuthManager:
    def __init__(self):
        self.base_dir = get_local_data_dir('moderlauncher')
        self.auth_file = os.path.join(self.base_dir, 'launcher_accounts.json')
        self.user_file = os.path.join(self.base_dir, 'launcher_user.json')
        self.user_data_file = os.path.join(self.base_dir, 'user_data.json')
        self.current_account = None
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self.load_accounts()
        self.load_user_data()

    def load_accounts(self):
        try:
            if os.path.exists(self.auth_file):
                with open(self.auth_file, 'r') as f:
                    self.accounts = json.load(f)
            else:
                self.accounts = {"accounts": {}}
                self.save_accounts()
        except Exception as e:
            print(f"Error loading accounts: {e}")
            self.accounts = {"accounts": {}}

    def save_accounts(self):
        try:
            os.makedirs(os.path.dirname(self.auth_file), exist_ok=True)
            with open(self.auth_file, 'w') as f:
                json.dump(self.accounts, f, indent=2)
        except Exception as e:
            print(f"Error saving accounts: {e}")

    def load_user_data(self):
        """Cargar datos de usuario del archivo JSON"""
        try:
            if os.path.exists(self.user_file):
                with open(self.user_file, 'r') as f:
                    self.user_data = json.load(f)
            else:
                self.user_data = {}
                self.save_user_data()
        except Exception as e:
            print(f"Error loading user data: {e}")
            self.user_data = {}

    def save_user_data(self):
        """Guardar datos de usuario en archivo JSON"""
        try:
            os.makedirs(os.path.dirname(self.user_file), exist_ok=True)
            with open(self.user_file, 'w') as f:
                json.dump(self.user_data, f, indent=2)
        except Exception as e:
            print(f"Error saving user data: {e}")

    def save_current_account(self, account_data):
        self.accounts["activeAccount"] = account_data["uuid"]
        self.save_accounts()

    def get_current_account(self):
        """Obtener cuenta actual"""
        try:
            # Primero intentar obtener de la memoria
            if self.current_account:
                return self.current_account
                
            # Luego intentar obtener del archivo de usuario
            if os.path.exists(self.user_data_file):
                with open(self.user_data_file, 'r') as f:
                    self.current_account = json.load(f)
                    return self.current_account
                    
            # Finalmente intentar obtener de las cuentas guardadas
            if self.accounts and self.accounts.get("accounts"):
                account = next(iter(self.accounts["accounts"].values()))
                self.current_account = account
                return account
                
            return None
        except Exception as e:
            print(f"Error en get_current_account: {e}")
            return None

    def authenticate_premium(self, email, password):
        try:
            auth_url = "https://authserver.mojang.com/authenticate"
            payload = {
                "agent": {"name": "Minecraft", "version": 1},
                "username": email,
                "password": password
            }
            response = requests.post(auth_url, json=payload, verify=certifi.where())
            if response.status_code == 200:
                account_data = {
                    "username": email.split("@")[0],
                    "type": "premium",
                    "uuid": str(uuid.uuid4()),
                    "email": email
                }
                self.save_current_account(account_data)
                return account_data
            return None
        except:
            return None

    def create_offline_account(self, username):
        # Generar UUID y token consistentes basados en el nombre de usuario
        player_uuid = str(uuid.uuid3(uuid.NAMESPACE_OID, f"OfflinePlayer:{username}"))
        # Crear un token único y persistente basado en el nombre de usuario
        token = base64.b64encode(
            hashlib.sha256(f"offline:{username}".encode()).digest()
        ).decode('utf-8')

        account_data = {
            "username": username,
            "uuid": player_uuid,
            "accessToken": token,
            "type": "offline",
            "persistentToken": token  # Guardar token persistente
        }

        # Guardar la cuenta
        self.accounts["accounts"][player_uuid] = account_data
        self.accounts["activeAccount"] = player_uuid
        self.save_accounts()
        return account_data

    def create_ely_account(self, username, password):
        """Autentica con Ely.by usando el endpoint correcto de authlib-injector"""
        try:
            # Endpoint correcto para authlib-injector de Ely.by
            url = "https://authserver.ely.by/auth/authenticate"
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ModerLauncher/1.0'
            }
            
            # Payload en formato authlib-injector (compatible con Mojang)
            payload = {
                "agent": {
                    "name": "Minecraft",
                    "version": 1
                },
                "username": username,
                "password": password,
                "clientToken": str(uuid.uuid4()),
                "requestUser": True
            }
            
            print(f"Intentando autenticar con Ely.by: {username}")
            
            # Usar certifi para verificación SSL correcta
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=15,
                verify=certifi.where()
            )

            print(f"Respuesta de Ely.by: Status {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                
                # Validar respuesta
                if "accessToken" not in data or "selectedProfile" not in data:
                    print(f"Respuesta incompleta de Ely.by: {data}")
                    raise Exception("Respuesta incompleta del servidor Ely.by")

                access_token = data["accessToken"]
                selected_profile = data["selectedProfile"]
                player_uuid = selected_profile["id"]
                player_username = selected_profile["name"]

                account_data = {
                    "username": player_username,
                    "uuid": player_uuid,
                    "accessToken": access_token,
                    "clientToken": data.get("clientToken", str(uuid.uuid4())),
                    "type": "ely",
                    "properties": selected_profile.get("properties", [])
                }

                # Guardar la cuenta
                self.accounts["accounts"][player_uuid] = account_data
                self.accounts["activeAccount"] = player_uuid
                self.save_accounts()
                
                # Guardar datos del usuario actual
                self.current_account = account_data
                with open(self.user_data_file, 'w') as f:
                    json.dump(account_data, f, indent=2)
                
                print(f"Autenticación exitosa para {player_username}")
                return account_data
                
            elif response.status_code == 403:
                print(f"Credenciales inválidas para Ely.by: {username}")
                raise Exception("Usuario o contraseña incorrectos")
            elif response.status_code == 400:
                print(f"Solicitud mal formada: {response.text}")
                raise Exception("Error en la solicitud. Verifica tus credenciales")
            else:
                print(f"Error {response.status_code} de Ely.by: {response.text}")
                raise Exception(f"Error del servidor Ely.by (código {response.status_code})")
                
        except requests.exceptions.SSLError as e:
            print(f"Error SSL con Ely.by: {e}")
            raise Exception(f"Error de certificado SSL. Intenta ejecutar: pip install --upgrade certifi")
        except requests.exceptions.Timeout:
            print("Timeout conectando a Ely.by")
            raise Exception("Tiempo de espera agotado. Verifica tu conexión a internet")
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión a Ely.by: {e}")
            raise Exception("No se pudo conectar a Ely.by. Verifica tu conexión a internet")
        except requests.exceptions.RequestException as e:
            print(f"Error de red con Ely.by: {e}")
            raise Exception(f"Error de red: {str(e)}")
        except ValueError as e:
            print(f"Error parseando respuesta JSON: {e}")
            raise Exception("Respuesta inválida del servidor Ely.by")
        except Exception as e:
            if "Usuario o contraseña incorrectos" in str(e) or "Error del servidor" in str(e):
                raise
            print(f"Error inesperado con Ely.by: {e}")
            raise Exception(f"Error inesperado: {str(e)}")

    def save_account(self, account_data):
        encrypted_data = self.cipher_suite.encrypt(json.dumps(account_data).encode())
        self.accounts[account_data["username"]] = encrypted_data.decode()
        self.save_accounts()

    def get_login_data(self):
        """Retorna datos de login en formato compatible con servidores"""
        try:
            current_account = self.get_current_account()
            if current_account:
                # Asegurarse de que todos los campos necesarios existen
                return {
                    "username": current_account.get("username", "Player"),
                    "uuid": current_account.get("uuid", str(uuid.uuid4())),
                    "accessToken": current_account.get("accessToken", 
                                                     current_account.get("token", "0")),
                    "clientToken": current_account.get("clientToken", "0"),
                    "type": current_account.get("type", "offline"),
                    "properties": current_account.get("properties", [])
                }
        except Exception as e:
            print(f"Error en get_login_data: {e}")
        
        # Retornar datos por defecto si algo falla
        return {
            "username": "Player",
            "uuid": str(uuid.uuid4()),
            "accessToken": "0",
            "clientToken": "0",
            "type": "offline",
            "properties": []
        }

    def logout(self):
        """Cerrar sesión y limpiar datos"""
        try:
            # Limpiar datos de la cuenta activa
            self.accounts["accounts"] = {}
            if "activeAccount" in self.accounts:
                del self.accounts["activeAccount"]
            
            # Limpiar datos del usuario
            self.current_account = None
            if os.path.exists(self.user_data_file):
                os.remove(self.user_data_file)
            
            # Guardar cambios
            self.save_accounts()
            return True
        except Exception as e:
            print(f"Error en logout: {e}")
            return False

    def generate_offline_token(self, username):
        """Genera un token único para cuentas offline"""
        timestamp = str(int(time.time()))
        unique_id = str(uuid.uuid4())
        data = f"{username}{timestamp}{unique_id}"
        return base64.b64encode(hashlib.sha256(data.encode()).digest()).decode()

    def authenticate_offline(self, username, uuid_str):
        """Autenticar usuario offline y guardar sus datos"""
        try:
            account_data = {
                "username": username,
                "uuid": uuid_str,
                "type": "offline"
            }
            
            # Guardar datos de la cuenta
            self.current_account = account_data
            self.accounts["accounts"] = {uuid_str: account_data}
            self.save_accounts()
            
            # Guardar datos del usuario
            with open(self.user_data_file, 'w') as f:
                json.dump(account_data, f, indent=2)
                
            return account_data
        except Exception as e:
            print(f"Error en authenticate_offline: {e}")
            return None

    def generate_server_compatible_token(self, username):
        """Genera un token compatible con el formato esperado por servidores"""
        # Crear un token que simule el formato de Mojang
        timestamp = int(time.time())
        base_data = f"{username}:{timestamp}:{uuid.uuid4()}"
        token_hash = hashlib.sha256(base_data.encode()).hexdigest()
        return f"token:{token_hash}"

    def validate_offline_session(self, account):
        """Valida si la sesión offline sigue siendo válida"""
        try:
            if not account or account.get("type") != "offline":
                return False
                
            expires_at = datetime.fromisoformat(account["expires_at"])
            if datetime.now() > expires_at:
                return False
                
            return True
        except Exception as e:
            print(f"Error validando sesión offline: {e}")
            return False