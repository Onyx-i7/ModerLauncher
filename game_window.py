import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import minecraft_launcher_lib
import threading
import os
import json
import shutil
import getpass
from pygame import mixer
import time

class VersionManager:
    def __init__(self, root=None):
        self.root = root  # Hacer root opcional
        self.minecraft_directory = os.path.join(os.getenv('APPDATA'), '.minecraft')
        self.installed_versions = self.load_installed_versions()
        self.current_max = 0
        self.cancelled = False
        self.download_steps = ['Analizando', 'Assets', 'Libraries', 'Cliente', 'Index']
        self.current_step = 0

    def create_initial_directories(self):
        """Crea los directorios necesarios de minecraft"""
        directories = [
            self.minecraft_directory,
            os.path.join(self.minecraft_directory, 'versions'),
            os.path.join(self.minecraft_directory, 'assets'),
            os.path.join(self.minecraft_directory, 'libraries'),
            os.path.join(self.minecraft_directory, 'natives'),
            os.path.join(self.minecraft_directory, 'runtime')
        ]

        for directory in directories:
            try:
                if not os.path.exists(directory):
                    print(f"Creando directorio: {directory}")
                    os.makedirs(directory)
            except Exception as e:
                print(f"Error con el directorio {directory}: {e}")

    def load_installed_versions(self):
        """Cargar versiones instaladas directamente del directorio versions"""
        versions_dir = os.path.join(self.minecraft_directory, 'versions')
        installed = {}
        
        if os.path.exists(versions_dir):
            for version in os.listdir(versions_dir):
                version_dir = os.path.join(versions_dir, version)
                if os.path.isdir(version_dir):
                    jar_path = os.path.join(version_dir, f"{version}.jar")
                    json_path = os.path.join(version_dir, f"{version}.json")
                    if os.path.exists(jar_path) and os.path.exists(json_path):
                        installed[version] = {
                            "installed": True,
                            "path": version_dir
                        }
        return installed

    def save_installed_versions(self):
        # No necesitamos guardar nada, las versiones se detectan automáticamente
        pass

    def is_version_installed(self, version):
        return version in self.installed_versions and self.installed_versions[version]["installed"]

    def download_version(self, version, callback):
        try:
            self.create_initial_directories()
            
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # Calcular tamaño total basado en la versión
            if version.startswith("1."):
                major, minor = map(int, version.split('.')[:2])
                if major == 1 and minor >= 17:
                    total_size = 450  # MB
                    total_files = 15
                else:
                    total_size = 250  # MB
                    total_files = 10
            else:
                total_size = 300  # MB
                total_files = 12

            # Variable para rastrear el archivo actual
            self.current_file = 1
            self.current_step = ""
            download_steps = ['assets', 'libraries', 'client', 'index']
            total_steps = len(download_steps)
                    
            def set_status(text):
                try:
                    # Detectar el paso actual
                    for i, step in enumerate(self.download_steps):
                        if step.lower() in text.lower():
                            self.current_step = i + 1
                            break
                    
                    # Enviar información actualizada del progreso
                    callback("progress", text, {
                        "current_step": self.current_step,
                        "total_steps": len(self.download_steps)
                    })
                except Exception as e:
                    print(f"Error en set_status: {e}")
            
            def set_progress(value):
                if self.current_max > 0:
                    percentage = int((value / self.current_max) * 100)
                    current_mb = int(total_size * percentage / 100)
                    speed = f"{(current_mb/10):.1f}"  # Simular velocidad
                    
                    # Actualizar progreso con toda la información
                    callback("progress", f"Descargando... {percentage}%", {
                        "percentage": percentage,
                        "current_size": current_mb,
                        "total_size": total_size,
                        "speed": speed,
                        "current_file": self.current_file,
                        "total_files": total_files
                    })
                else:
                    callback("progress", "Descargando...")

            def set_max(maximum):
                self.current_max = maximum

            callback("analyzing", "Analizando archivos necesarios...")
            
            minecraft_launcher_lib.install.install_minecraft_version(
                version,
                self.minecraft_directory,
                callback={
                    "setStatus": set_status,
                    "setProgress": set_progress,
                    "setMax": set_max
                }
            )

            # Verificar instalación
            version_path = os.path.join(self.minecraft_directory, "versions", version)
            if os.path.exists(version_path):
                self.installed_versions[version] = {
                    "installed": True,
                    "path": version_path
                }
                self.save_installed_versions()
                callback("success", "¡Instalación completada!")
                
                if self.root:
                    self.root.after(100, lambda: self.show_download_message(version))

        except Exception as e:
            print(f"Error detallado: {str(e)}")
            callback("error", f"Error: {str(e)}")

    def show_download_message(self, version):
        """Muestra el mensaje de descarga completada"""
        from mensajeDoloand import MensajeDescarga
        MensajeDescarga(self.root, version)

    def remove_version(self, version):
        if version in self.installed_versions:
            version_path = os.path.join(self.minecraft_directory, "versions", version)
            if os.path.exists(version_path):
                shutil.rmtree(version_path)
            del self.installed_versions[version]
            self.save_installed_versions()

    def get_installed_version(self):
        # Retornar la última versión instalada
        installed = [v for v, data in self.installed_versions.items() if data.get("installed")]
        return installed[-1] if installed else None

    def launch_game(self, version, ram="2", java_path=None, options=None):
        try:
            if not options:
                options = {
                    'username': "Player",
                    'uuid': '',
                    'token': '',
                    'executablePath': java_path if java_path else "java",
                    "jvmArguments": [f"-Xmx{ram}G", f"-Xms{ram}G"],
                    "launcherVersion": "1.0.4",
                }

            # Asegurarse de que las opciones contengan los campos necesarios
            required_fields = ['username', 'uuid', 'token']
            for field in required_fields:
                if field not in options:
                    options[field] = ''

            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                version,
                self.minecraft_directory,
                options
            )
            
            import subprocess
            subprocess.Popen(minecraft_command)
            return True, "Juego iniciado correctamente"
        except Exception as e:
            return False, f"Error al iniciar: {str(e)}"

    def get_version_type(self, version):
        version_dir = os.path.join(self.minecraft_directory, "versions", version)
        if os.path.exists(os.path.join(version_dir, f"{version}-forge.jar")):
            return "forge"
        elif os.path.exists(os.path.join(version_dir, f"{version}-fabric.jar")):
            return "fabric"
        return "vanilla"

    def refresh_installed_versions(self):
        """Actualiza la lista de versiones instaladas"""
        self.installed_versions = self.load_installed_versions()
        return self.installed_versions

class CustomProgressBar(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#252525", highlightthickness=0, height=60)  # Aumentado height
        self.create_status_display()

    def create_status_display(self):
        # Crear marco para el contenedor de información
        self.info_frame = tk.Frame(self, bg="#1a1a1a", width=230, height=50)
        self.info_frame.pack(pady=5)
        self.info_frame.pack_propagate(False)

        # Porcentaje grande en el centro
        self.percent_label = tk.Label(
            self.info_frame,
            text="0%",
            font=("Segoe UI", 18, "bold"),
            bg="#1a1a1a",
            fg="#4CAF50"
        )
        self.percent_label.pack(pady=(5,0))

        # Velocidad y tamaño debajo
        self.details_label = tk.Label(
            self.info_frame,
            text="Esperando...",
            font=("Segoe UI", 8),
            bg="#1a1a1a",
            fg="#888888"
        )
        self.details_label.pack()

    def update_progress(self, percentage, speed="0 MB/s", current_size="0 MB", total_size="0 MB"):
        # Actualizar porcentaje
        self.percent_label.config(text=f"{percentage}%")
        
        # Actualizar detalles de la descarga
        details = f"{speed} • {current_size}/{total_size}"
        self.details_label.config(text=details)

        # Cambiar color según el progreso
        if percentage == 100:
            self.percent_label.config(fg="#4CAF50")  # Verde al completar
        elif percentage > 0:
            self.percent_label.config(fg="#2196F3")  # Azul durante la descarga

class CustomMessageWindow:
    def __init__(self, parent, title, message):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        
        # Configurar ventana
        window_width = 300
        window_height = 150
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configuración de la ventana
        self.window.configure(bg="#161616")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        # Frame principal con borde
        main_frame = tk.Frame(
            self.window,
            bg="#161616",
            highlightbackground="#333333",
            highlightthickness=2
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Mensaje
        message_label = tk.Label(
            main_frame,
            text=message,
            bg="#161616",
            fg="white",
            font=("Segoe UI", 10),
            wraplength=250,
            justify="center"
        )
        message_label.pack(pady=(30, 20))
        
        # Botón Aceptar
        accept_button = tk.Button(
            main_frame,
            text="Aceptar",
            command=self.window.destroy,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            width=10,
            bd=0,
            relief="flat"
        )
        accept_button.pack(pady=(0, 20))
        
        # Efectos hover para el botón
        def on_enter(e):
            e.widget.configure(bg="#3d8c40")
        
        def on_leave(e):
            e.widget.configure(bg="#4CAF50")
        
        accept_button.bind("<Enter>", on_enter)
        accept_button.bind("<Leave>", on_leave)
        
        # Hacer la ventana movible
        def start_move(event):
            self.window.x = event.x
            self.window.y = event.y

        def stop_move(event):
            self.window.x = None
            self.window.y = None

        def do_move(event):
            deltax = event.x - self.window.x
            deltay = event.y - self.window.y
            x = self.window.winfo_x() + deltax
            y = self.window.winfo_y() + deltay
            self.window.geometry(f"+{x}+{y}")

        main_frame.bind("<Button-1>", start_move)
        main_frame.bind("<ButtonRelease-1>", stop_move)
        main_frame.bind("<B1-Motion>", do_move)

class ConfirmDeleteWindow:
    def __init__(self, parent, version, on_confirm):
        self.window = tk.Toplevel(parent)
        self.window.title("Confirmar eliminación")
        
        # Configurar ventana
        window_width = 300
        window_height = 150
        x = (self.window.winfo_screenwidth() - window_width) // 2
        y = (self.window.winfo_screenheight() - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.window.configure(bg="#161616")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        # Frame principal con borde
        main_frame = tk.Frame(
            self.window, 
            bg="#161616",
            highlightbackground="#333333",
            highlightthickness=2
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Mensaje
        message_label = tk.Label(
            main_frame,
            text=f"¿Estás seguro que deseas eliminar\nMinecraft {version}?",
            bg="#161616",
            fg="white",
            font=("Segoe UI", 10),
            justify="center"
        )
        message_label.pack(pady=(30, 20))
        
        # Frame para botones
        buttons_frame = tk.Frame(main_frame, bg="#161616")
        buttons_frame.pack(pady=(0, 20))
        
        # Botón Eliminar
        delete_button = tk.Button(
            buttons_frame,
            text="Eliminar",
            command=lambda: [on_confirm(), self.window.destroy()],
            bg="#ff4444",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            width=10,
            bd=0
        )
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # Botón Cancelar
        cancel_button = tk.Button(
            buttons_frame,
            text="Cancelar",
            command=self.window.destroy,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            width=10,
            bd=0
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Efectos hover para los botones
        def on_enter(e):
            if e.widget == delete_button:
                e.widget.configure(bg="#cc3333")
            else:
                e.widget.configure(bg="#3d8c40")
        
        def on_leave(e):
            if e.widget == delete_button:
                e.widget.configure(bg="#ff4444")
            else:
                e.widget.configure(bg="#4CAF50")
        
        delete_button.bind("<Enter>", on_enter)
        delete_button.bind("<Leave>", on_leave)
        cancel_button.bind("<Enter>", on_enter)
        cancel_button.bind("<Leave>", on_leave)

class GameWindow:
    def __init__(self, parent_frame, version_callback=None, refresh_callback=None):
        self.frame = parent_frame
        self.frame.configure(bg="#1E1E1E")
        # Modificar esta línea para pasar la referencia de la ventana
        self.version_manager = VersionManager(parent_frame.winfo_toplevel())
        self.version_callback = version_callback  # Guardar callback
        self.refresh_callback = refresh_callback  # Guardar callback
        
        # Lista completa de versiones
        self.minecraft_versions = [
            "1.0", "1.1", "1.2.1", "1.2.2", "1.3.1", "1.4.2", "1.4.6", "1.4.7",
            "1.5.1", "1.5.2", "1.6.1", "1.6.2", "1.6.4", "1.7.2", "1.7.4", "1.7.5",
            "1.7.9", "1.7.10", "1.8", "1.8.1", "1.8.2", "1.8.3", "1.8.4", "1.8.5",
            "1.8.6", "1.8.7", "1.8.8", "1.8.9", "1.9", "1.9.1", "1.9.2", "1.9.4",
            "1.10", "1.10.2", "1.11", "1.11.1", "1.11.2", "1.12", "1.12.1", "1.12.2",
            "1.13", "1.13.1", "1.13.2", "1.14", "1.14.1", "1.14.2", "1.14.3", "1.14.4",
            "1.15", "1.15.1", "1.15.2", "1.16", "1.16.1", "1.16.2", "1.16.3", "1.16.4",
            "1.16.5", "1.17", "1.17.1", "1.18", "1.18.1", "1.18.2", "1.19", "1.19.1",
            "1.19.2", "1.19.3", "1.20", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
            "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4", "1.21.5"
        ]
        
        self.create_ui()
        
        # Agregar timer para actualización automática
        self.check_for_updates()

        # Inicializar mixer de pygame para los sonidos
        mixer.init()
        
        # Cargar el sonido de eliminación
        self.delete_sound_path = os.path.join(os.path.dirname(__file__), 'sonidos', 'basura.mp3')
        try:
            self.delete_sound = mixer.Sound(self.delete_sound_path)
            self.delete_sound.set_volume(0.5)  # Ajustar volumen al 50%
        except:
            print("No se pudo cargar el sonido de eliminación")
            self.delete_sound = None

    def create_ui(self):
        # Banner superior
        banner_frame = tk.Frame(self.frame, bg="#1A2327", height=100)
        banner_frame.pack(fill=tk.X, padx=20, pady=(20,10))
        
        # Contenedor para título
        title_container = tk.Frame(banner_frame, bg="#1A2327")
        title_container.place(x=30, y=30)

        title_label = tk.Label(
            title_container, 
            text="Minecraft Java Versions", 
            font=("Segoe UI", 24, "bold"), 
            bg="#1A2327", 
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        # Marco principal con scroll y padding mejorado
        main_frame = tk.Frame(self.frame, bg="#1E1E1E")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Canvas y Scrollbar
        canvas = tk.Canvas(main_frame, bg="#1E1E1E", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1E1E1E")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Grid mejorado con más espacio
        row = 0
        col = 0
        for version in self.minecraft_versions:
            frame = self.create_version_entry(scrollable_frame, version)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            col += 1
            if col >= 4:
                col = 0
                row += 1

        # Configurar grid con pesos iguales
        for i in range(4):
            scrollable_frame.grid_columnconfigure(i, weight=1)

        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True, padx=(0,10))
        scrollbar.pack(side="right", fill="y")

    def create_version_entry(self, parent, version):
        # Frame principal con tamaño fijo y bordes redondeados
        frame = tk.Frame(parent, bg="#252525")
        frame.configure(width=250, height=120)  # Aumentado height
        frame.pack_propagate(False)
        
        # Contenedor principal con mejor organización
        main_container = tk.Frame(frame, bg="#252525", padx=15, pady=10)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Etiqueta de versión con mejor espaciado
        version_label = tk.Label(
            main_container, 
            text=f"Minecraft {version}", 
            font=("Segoe UI", 11, "bold"),
            bg="#252525",
            fg="white",
            anchor="w"
        )
        version_label.pack(side=tk.TOP, fill=tk.X, pady=(0,5))

        # Contenedor para la barra de progreso (ahora antes del bottom_container)
        progress_container = tk.Frame(main_container, bg="#252525")
        progress_container.pack(side=tk.TOP, fill=tk.X, pady=(5,10))  # Aumentado padding
        
        # Crear barra de progreso personalizada
        progress_bar = CustomProgressBar(progress_container, width=250)  # Aumentado width
        frame.progress_bar = progress_bar
        
        # Inicialmente oculta
        frame.progress_bar.pack_forget()

        # Contenedor inferior para botones y estado
        bottom_container = tk.Frame(main_container, bg="#252525")
        bottom_container.pack(side=tk.BOTTOM, fill=tk.X)

        # Status label con ancho fijo
        status_label = tk.Label(
            bottom_container,
            text="",
            font=("Segoe UI", 9),
            bg="#252525",
            fg="#4CAF50",
            width=15,
            anchor="e"
        )
        status_label.pack(side=tk.RIGHT)
        frame.status_label = status_label

        def create_rounded_button(parent, text, command, color="#4CAF50"):
            button_canvas = tk.Canvas(parent, width=100, height=30, 
                                   bg="#252525", highlightthickness=0)
            button_canvas.pack(side=tk.RIGHT, padx=(0,10))

            # Crear rectángulo redondeado
            button_bg = button_canvas.create_rounded_rectangle(0, 0, 100, 30, 
                                                            radius=15, fill=color)
            button_text = button_canvas.create_text(50, 15, text=text,
                                                 font=("Segoe UI", 9, "bold"),
                                                 fill="white")

            def on_enter(e):
                button_canvas.itemconfig(button_bg, fill=self.darken_color(color))

            def on_leave(e):
                button_canvas.itemconfig(button_bg, fill=color)

            def on_click(e):
                command()

            for item in [button_bg, button_text]:
                button_canvas.tag_bind(item, "<Enter>", on_enter)
                button_canvas.tag_bind(item, "<Leave>", on_leave)
                button_canvas.tag_bind(item, "<Button-1>", on_click)

            return button_canvas

        if self.version_manager.is_version_installed(version):
            status_label.config(text="✓ Instalado")
            create_rounded_button(bottom_container, "Eliminar", 
                               lambda v=version, f=frame: self.remove_version(v, f),
                               color="#ff4444")
        else:
            create_rounded_button(bottom_container, "Descargar",
                               lambda v=version, f=frame: self.download_version(v, f))

        return frame

    @staticmethod
    def darken_color(color):
        """Oscurece un color hex"""
        # Convertir color hex a RGB
        rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        # Oscurecer cada componente un 20%
        darkened = tuple(int(c * 8) for c in rgb)
        # Convertir de vuelta a hex
        return '#{:02x}{:02x}{:02x}'.format(*darkened)

    def download_version(self, version, frame):
        # Crear la ventana de progreso
        download_window = DownloadProgressWindow(self.frame, version)
        
        def update_ui(status, message, extra_info=None):
            if download_window.cancelled:
                return
                
            try:
                if status == "analyzing":
                    download_window.percent_label.config(text="Analizando...")
                    
                elif status == "progress":
                    if isinstance(extra_info, dict):
                        download_window.update_progress(
                            extra_info["percentage"],
                            extra_info["current_size"],
                            extra_info["total_size"],
                            extra_info["speed"],
                            extra_info["current_file"],
                            extra_info["total_files"]
                        )
                        
                elif status == "success":
                    download_window.close()
                    frame.status_label.config(text="✓ Instalado", fg="#4CAF50")
                    CustomMessageWindow(
                        self.frame,
                        "✅ Instalación Completada",
                        f"¡Minecraft {version} se ha instalado correctamente!"
                    )
                    
                    if self.version_callback:
                        self.version_callback(version)
                    if self.refresh_callback:
                        self.refresh_callback()
                    self.frame.after_idle(self.refresh_ui)
                    
                elif status == "error":
                    download_window.close()
                    frame.status_label.config(text="✗ Error", fg="#ff4444")
                    
            except Exception as e:
                print(f"Error en update_ui: {e}")

        try:
            thread = threading.Thread(
                target=lambda: self.version_manager.download_version(version, update_ui),
                daemon=True
            )
            thread.start()
        except Exception as e:
            print(f"Error iniciando descarga: {e}")
            update_ui("error", str(e))

    def remove_version(self, version, frame):
        def do_remove():
            self.version_manager.remove_version(version)
            self.refresh_ui()
            
            # Mostrar mensaje de éxito
            CustomMessageWindow(
                self.frame,
                "✅ Versión eliminada",
                f"Minecraft {version} ha sido eliminado correctamente."
            )

            # Reproducir sonido de eliminación
            if hasattr(self, 'delete_sound') and self.delete_sound:
                try:
                    self.delete_sound.play()
                except:
                    print("Error al reproducir sonido de eliminación")

        # Mostrar ventana de confirmación
        ConfirmDeleteWindow(self.frame, version, do_remove)

    def refresh_ui(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.create_ui()
        
    def check_for_updates(self):
        """Verifica periódicamente si hay nuevas versiones instaladas"""
        try:
            old_versions = set(self.version_manager.installed_versions.keys())
            self.version_manager.refresh_installed_versions()
            new_versions = set(self.version_manager.installed_versions.keys())
            
            if old_versions != new_versions:
                # Usar after_idle para actualizar la UI de forma segura
                self.frame.after_idle(self.refresh_ui)
                if self.refresh_callback:
                    self.frame.after_idle(self.refresh_callback)
        except Exception as e:
            print(f"Error checking for updates: {e}")
        finally:
            # Programar próxima verificación
            self.frame.after(5000, self.check_for_updates)

    def update_version_list(self):
        """Actualiza la lista de versiones en la interfaz"""
        try:
            # En lugar de llamar a create_version_list, llamamos a refresh_ui
            self.refresh_ui()
        except Exception as e:
            print(f"Error updating version list: {e}")

    def stop_sound(self):
        """Detiene los sonidos al cerrar la ventana"""
        if hasattr(self, 'delete_sound') and self.delete_sound:
            try:
                mixer.stop()
            except:
                pass

class DownloadProgressWindow:
    def __init__(self, parent, version):
        self.window = tk.Toplevel(parent)
        self.window.title("Descargando Minecraft")
        self.window.configure(bg="#161616")
        self.window.overrideredirect(True)
        self.cancelled = False
        
        # Centrar ventana
        window_width = 400
        window_height = 200
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Frame principal con borde
        self.main_frame = tk.Frame(
            self.window,
            bg="#161616",
            highlightbackground="#333333",
            highlightthickness=2
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Título
        self.title = tk.Label(
            self.main_frame,
            text=f"Descargando Minecraft {version}",
            font=("Segoe UI", 14, "bold"),
            bg="#161616",
            fg="white"
        )
        self.title.pack(pady=10)

        # Estado actual con mejor visibilidad
        self.status_frame = tk.Frame(self.main_frame, bg="#1a1a1a", padx=10, pady=5)
        self.status_frame.pack(fill="x", padx=20)
        
        # Labels para información
        self.step_label = tk.Label(
            self.status_frame,
            text="Archivos: 0/0",
            font=("Segoe UI", 10),
            bg="#1a1a1a",
            fg="white"
        )
        self.step_label.pack(side="left")
        
        self.size_label = tk.Label(
            self.status_frame,
            text="0MB/0MB",
            font=("Segoe UI", 10),
            bg="#1a1a1a",
            fg="white"
        )
        self.size_label.pack(side="right")

        # Barra de progreso
        style = ttk.Style()
        style.configure(
            "Download.Horizontal.TProgressbar",
            troughcolor="#2A2A2A",
            background="#4CAF50",
            thickness=20
        )
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            style="Download.Horizontal.TProgressbar",
            variable=self.progress_var,
            mode="determinate",
            length=360
        )
        self.progress_bar.pack(padx=20, pady=15)

        # Porcentaje grande
        self.percent_label = tk.Label(
            self.main_frame,
            text="0%",
            font=("Segoe UI", 24, "bold"),
            bg="#161616",
            fg="#4CAF50"
        )
        self.percent_label.pack(pady=5)

        # Velocidad
        self.speed_label = tk.Label(
            self.main_frame,
            text="0 MB/s",
            font=("Segoe UI", 10),
            bg="#161616",
            fg="white"
        )
        self.speed_label.pack(pady=5)

        # Hacer la ventana movible
        self.title.bind("<Button-1>", self.start_move)
        self.title.bind("<ButtonRelease-1>", self.stop_move)
        self.title.bind("<B1-Motion>", self.do_move)

    def update_progress(self, percentage, current_mb, total_mb, speed, current_file=None, total_files=None):
        if self.cancelled:
            return False
            
        try:
            self.window.after(0, lambda: self._safe_update(
                percentage, current_mb, total_mb, speed, current_file, total_files
            ))
            return True
        except:
            return False

    def _safe_update(self, percentage, current_mb, total_mb, speed, current_file, total_files):
        try:
            if self.cancelled or not self.window.winfo_exists():
                return

            self.progress_var.set(percentage)
            self.percent_label.config(text=f"{percentage}%")
            
            if current_file is not None and total_files is not None:
                self.step_label.config(text=f"Archivos: {current_file}/{total_files}")
            
            if total_mb >= 1024:
                size_text = f"{current_mb/1024:.1f}GB/{total_mb/1024:.1f}GB"
            else:
                size_text = f"{current_mb}MB/{total_mb}MB"
            self.size_label.config(text=size_text)
            
            self.speed_label.config(text=f"{speed}MB/s")
            self.window.update_idletasks()
            
        except Exception as e:
            print(f"Error en actualización: {e}")
            self.cancelled = True

    def start_move(self, event):
        self.window.x = event.x
        self.window.y = event.y

    def stop_move(self, event):
        self.window.x = None
        self.window.y = None

    def do_move(self, event):
        deltax = event.x - self.window.x
        deltay = event.y - self.window.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

    def close(self):
        self.window.destroy()

# ...rest of existing code...
