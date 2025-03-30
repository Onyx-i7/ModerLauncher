import tkinter as tk
from tkinter import ttk, filedialog
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QProgressBar, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPixmap
import sys
import os
import importlib.util

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_image(path):
    return resource_path(os.path.join('assets', path))

def load_sound(path):
    return resource_path(os.path.join('sonidos', path))

class SplashScreen(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle('Cargando')
        self.setFixedSize(300, 300)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.counter = 0
        
        self.container = QWidget(self)
        self.container.setFixedSize(300, 300)
        self.container.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 20px;
            }
        """)

        self.layout_setup()
        self.timer = QTimer()
        self.timer.timeout.connect(self.progress)
        self.timer.start(40)  # 100ms entre actualizaciones
        self.increment = 0.5   # Incremento más pequeño para que dure ~10 segundos
        self.show()

    def layout_setup(self):
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 30, 30, 30)  # Márgenes más amplios
        layout.setSpacing(20)  # Espacio entre elementos

        # Logo
        self.logo = QLabel(self.container)
        self.logo.setPixmap(QPixmap(load_image('logo/logo.png')).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo)
        
        # Espacio flexible
        layout.addStretch()

        # Progress Bar mejorada
        self.progress_bar = QProgressBar(self.container)
        self.progress_bar.setFixedHeight(8)  # Altura más pequeña
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50,
                    stop:1 #45a049
                );
            }
        """)
        layout.addWidget(self.progress_bar)

        # Texto de carga con efecto de puntos
        self.loading_text = QLabel('Iniciando...', self.container)
        self.loading_text.setAlignment(Qt.AlignCenter)
        self.loading_text.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-family: 'Segoe UI';
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.loading_text)
        
        # Timer para los puntos animados
        self.dot_timer = QTimer(self)
        self.dot_timer.timeout.connect(self.update_loading_text)
        self.dot_timer.start(500)
        self.dot_count = 0

    def update_loading_text(self):
        dots = '.' * ((self.dot_count % 3) + 1)
        texts = ['Iniciando', 'Cargando módulos', 'Preparando launcher']
        current_text = texts[min(2, int(self.counter / 33))]  # Cambia el texto según el progreso
        self.loading_text.setText(f"{current_text}{dots}")
        self.dot_count += 1

    def progress(self):
        self.progress_bar.setValue(int(self.counter))
        if self.counter >= 100:
            self.timer.stop()
            self.dot_timer.stop()
            self.close()
            
            # Iniciar el launcher Minecraft
            root = tk.Tk()
            launcher = MinecraftLauncher(root)
            
            def on_closing():
                if ask_quit(root):
                    root.destroy()
                    self.app.quit()
            
            root.protocol("WM_DELETE_WINDOW", on_closing)
            root.mainloop()
            
        self.counter += self.increment

import json
import uuid
import minecraft_launcher_lib
from auth_manager import AuthManager
import tkinter.messagebox as messagebox
from game_window import GameWindow, VersionManager
from profile_window import ProfileWindow
from settings_window import SettingsWindow
import getpass
import time
from threading import Thread
from queue import Queue
from download_progress import DownloadProgress
from pygame import mixer
from bye import ask_quit
from PIL import Image, ImageTk

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
        
        self.window.configure(bg="#161616")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        main_frame = tk.Frame(
            self.window,
            bg="#161616",
            highlightbackground="#333333",
            highlightthickness=2
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
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
        
        def on_enter(e):
            e.widget.configure(bg="#3d8c40")
        
        def on_leave(e):
            e.widget.configure(bg="#4CAF50")
        
        accept_button.bind("<Enter>", on_enter)
        accept_button.bind("<Leave>", on_leave)
        
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

def create_rounded_button(parent, text, command):
    frame = tk.Frame(parent, bg="#252525")
    frame.pack(pady=5)
    
    canvas = tk.Canvas(frame, width=120, height=30, bg="#252525", highlightthickness=0)
    canvas.pack()

    # Crear rectángulo redondeado con esquinas suaves
    def create_rounded_rectangle(x1, y1, x2, y2, radius=15):
        points = [x1+radius, y1,
                 x2-radius, y1,
                 x2, y1,
                 x2, y1+radius,
                 x2, y2-radius,
                 x2, y2,
                 x2-radius, y2,
                 x1+radius, y2,
                 x1, y2,
                 x1, y2-radius,
                 x1, y1+radius,
                 x1, y1]
        return canvas.create_polygon(points, smooth=True, fill="#4CAF50")

    button_bg = create_rounded_rectangle(0, 0, 120, 30)
    button_text = canvas.create_text(60, 15, text=text, fill="white", font=("Segoe UI", 9, "bold"))

    def on_enter(e):
        canvas.itemconfig(button_bg, fill="#3d8c40")

    def on_leave(e):
        canvas.itemconfig(button_bg, fill="#4CAF50")

    def on_click(e):
        if command:
            command(e)

    # Vinculamos los eventos tanto al fondo como al texto
    canvas.tag_bind(button_bg, "<Enter>", on_enter)
    canvas.tag_bind(button_bg, "<Leave>", on_leave)
    canvas.tag_bind(button_bg, "<Button-1>", on_click)
    
    # También vinculamos los eventos al texto
    canvas.tag_bind(button_text, "<Enter>", on_enter)
    canvas.tag_bind(button_text, "<Leave>", on_leave)
    canvas.tag_bind(button_text, "<Button-1>", on_click)
    
    # Y al canvas completo
    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", on_click)

    return canvas

class VersionObserver:
    def __init__(self, version_manager, callback):
        self.version_manager = version_manager
        self.callback = callback
        self.running = False
        self.queue = Queue()
        self.known_versions = set()
        
    def start(self):
        self.running = True
        self.thread = Thread(target=self._observe, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1)
            
    def _observe(self):
        while self.running:
            try:
                current_versions = set(self.version_manager.installed_versions.keys())
                if current_versions != self.known_versions:
                    self.known_versions = current_versions
                    self.queue.put(list(current_versions))
                    if self.callback:
                        self.callback()
            except Exception as e:
                print(f"Error en observer: {e}")
            time.sleep(0.5)  # Revisar cada medio segundo

class MinecraftLauncher:
    def __init__(self, root):
        # Quitar código de AppUserModelID
        self.check_versions_timer = None
        self.version_observer = None
        
        self.auth_manager = AuthManager()
        self.root = root
        self.root.title("ModerLauncher")
        self.root.geometry("1200x668")
        
        # Inicializar timer primero
        self.check_versions_timer = None
        self.version_observer = None
        
        self.auth_manager = AuthManager()
        self.root = root
        self.root.title("ModerLauncher")
        self.root.geometry("1200x668")
        
        # Configurar el ícono de la ventana
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo', 'logo.png')
        try:
            icon_image = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")
            
        self.root.configure(bg="#1E1E1E")
        self.root.resizable(False, False)
        
        # Cambiar el color de la barra de título a oscuro
        self.root.tk_setPalette(background='#1E1E1E')
        self.root.update()
        
        # Ajustar el color de la barra de título en Windows
        if os.name == 'nt':  # Solo para Windows
            try:
                import ctypes
                HWND = ctypes.windll.user32.GetParent(self.root.winfo_id())
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    HWND,
                    35,  # DWMWA_TITLEBAR_COLOR
                    ctypes.byref(ctypes.c_int(0x001E1E1E)),  # Color en formato BGR
                    ctypes.sizeof(ctypes.c_int)
                )
            except:
                pass  # Si falla, mantener el estilo predeterminado
        
        # Inicializar mixer de pygame para los sonidos
        mixer.init()
        
        # Cargar el sonido del click
        self.sound_path = os.path.join(os.path.dirname(__file__), 'sonidos', 'click_botton.mp3')
        try:
            self.click_sound = mixer.Sound(self.sound_path)
            self.click_sound.set_volume(0.5)  # Ajustar volumen al 50%
        except:
            print("No se pudo cargar el sonido de click")
            self.click_sound = None
        
        # Centrar la ventana en la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 668) // 2
        self.root.geometry(f"1200x668+{x}+{y}")
        
        # Colores
        self.dark_bg = "#1E1E1E"
        self.lighter_bg = "#252525"
        self.accent_color = "#4CAF50"  # Verde Minecraft
        self.text_color = "#FFFFFF"
        self.secondary_text = "#AAAAAA"
        
        # Fuentes
        self.title_font = ("Segoe UI", 24, "bold")
        self.subtitle_font = ("Segoe UI", 12)
        self.button_font = ("Segoe UI", 10, "bold")
        
        self.current_window = None
        self.main_content_frame = None
        self.user_widget = None  # Agregamos esta línea
        self.current_user = getpass.getuser()
        
        # Usar solo el directorio .minecraft
        self.minecraft_directory = os.path.join(os.getenv('APPDATA'), '.minecraft')
        
        # Crear el directorio .minecraft si no existe
        try:
            if not os.path.exists(self.minecraft_directory):
                os.makedirs(self.minecraft_directory)
                print(f"Directorio .minecraft creado: {self.minecraft_directory}")
        except Exception as e:
            print(f"Error al crear directorio .minecraft: {e}")
            messagebox.showerror("Error", f"Error al crear directorio .minecraft: {e}")
            raise SystemExit(1)
            
        # Configuración en el directorio .minecraft
        self.config_file = os.path.join(self.minecraft_directory, "launcher_config.json")
        self.version_manager = VersionManager()
        
        # Crear directorios necesarios
        required_dirs = [
            os.path.join(self.minecraft_directory, 'versions'),
            os.path.join(self.minecraft_directory, 'assets'),
            os.path.join(self.minecraft_directory, 'libraries'),
            os.path.join(self.minecraft_directory, 'natives')
        ]
        
        for directory in required_dirs:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f"Error al crear directorio {directory}: {e}")

        self.load_config()

        self.create_sidebar()
        self.create_user_widget()  # Agregamos esta línea
        self.show_home_window()

        from java_manager import JavaManager
        self.java_manager = JavaManager()

    def play_click_sound(self):
        """Reproduce el sonido de click si está disponible"""
        if hasattr(self, 'click_sound') and self.click_sound:
            try:
                self.click_sound.play()
            except:
                pass

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "RAM": "2",
                    "Java": None,
                    "Nombre": "Player",
                    "offline_username": None  # Añadimos campo para usuario offline
                }
                self.save_config()
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            self.config = {
                "RAM": "2", 
                "Java": None, 
                "Nombre": "Player",
                "offline_username": None
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg="#121212", width=80)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Logo
        logo_frame = tk.Frame(sidebar, bg="#121212", width=80, height=80)
        logo_frame.pack(pady=10)
        logo_label = tk.Label(logo_frame, text="ML", font=("Segoe UI", 24, "bold"), bg="#121212", fg="white")
        logo_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Frame para información del usuario
        self.sidebar_user_frame = tk.Frame(sidebar, bg="#121212")
        self.sidebar_user_frame.pack(side=tk.TOP, pady=10)
        
        # Actualizar información del usuario
        self.update_sidebar_user()
        
        # Botones de navegación
        nav_frame = tk.Frame(sidebar, bg="#121212")
        nav_frame.pack(fill=tk.Y, expand=True)
        
        icons = ["👤", "🏠", "🧩", "📂", "⚙️"]  # Añadido icono de ajustes
        labels = ["Cuenta", "Home", "Mods", "Versiones", "Ajustes"]  # Añadido etiqueta de ajustes
        commands = [
            (self.show_profile_window, "profile"),
            (self.show_home_window, "home"),
            (self.show_mods_window, "mods"),
            (self.show_game_window, "games"),
            (self.show_settings_window, "settings")  # Añadido comando de ajustes
        ]
        
        self.nav_buttons = {}
        self.active_section = tk.StringVar(value="home")
        
        for i, (icon, label, (command, section)) in enumerate(zip(icons, labels, commands)):
            btn_frame = tk.Frame(nav_frame, bg="#121212")
            btn_frame.pack(pady=15)  # Reducido el padding vertical
            
            # Icono
            btn = tk.Label(btn_frame, text=icon, font=("Segoe UI", 20), bg="#121212", fg="#888888")
            btn.pack()
            
            # Texto debajo del icono
            text_label = tk.Label(btn_frame, text=label, font=("Segoe UI", 8), bg="#121212", fg="#888888")
            text_label.pack()
            
            # Línea indicadora
            indicator = tk.Frame(btn_frame, width=4, height=30, bg="#121212")
            indicator.place(x=-5, rely=0.3, anchor="w")
            
            # Guardar referencias incluyendo el texto
            self.nav_buttons[section] = (btn, indicator, text_label)
            
            def on_enter(e, btn=btn, ind=indicator, text=text_label, sect=section):
                if self.active_section.get() != sect:
                    btn.config(fg="white")
                    text.config(fg="white")
                    ind.config(bg="#4CAF50")

            def on_leave(e, btn=btn, ind=indicator, text=text_label, sect=section):
                if self.active_section.get() != sect:
                    btn.config(fg="#888888")
                    text.config(fg="#888888")
                    ind.config(bg="#121212")

            def on_click(cmd=command, sect=section):
                self.play_click_sound()
                self.active_section.set(sect)
                self.update_nav_buttons()
                cmd()

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            btn.bind("<Button-1>", lambda e, c=on_click: c())
            text_label.bind("<Enter>", on_enter)
            text_label.bind("<Leave>", on_leave)
            text_label.bind("<Button-1>", lambda e, c=on_click: c())

    def update_sidebar_user(self):
        # Limpiar widgets existentes
        for widget in self.sidebar_user_frame.winfo_children():
            widget.destroy()
        
        # Obtener información actualizada del usuario
        auth_manager = AuthManager()
        current_account = auth_manager.get_current_account()
        
        if current_account:
            # Icono de usuario
            tk.Label(self.sidebar_user_frame, text="👤", font=("Segoe UI", 20), 
                    bg="#121212", fg="white").pack()
            
            # Nombre de usuario
            username = current_account["username"]
            display_name = username[:10] + "..." if len(username) > 10 else username
            tk.Label(self.sidebar_user_frame, text=display_name,
                    font=("Segoe UI", 8), bg="#121212", fg="white").pack()
        else:
            # Usuario por defecto
            tk.Label(self.sidebar_user_frame, text="👤", font=("Segoe UI", 20), 
                    bg="#121212", fg="#888888").pack()
            tk.Label(self.sidebar_user_frame, text="Guest",
                    font=("Segoe UI", 8), bg="#121212", fg="#888888").pack()
        
        self.sidebar_user_frame.update()

    def update_nav_buttons(self):
        """Actualiza el estado visual de los botones de navegación"""
        active = self.active_section.get()
        for section, (btn, indicator, text_label) in self.nav_buttons.items():
            if section == active:
                btn.config(fg="white")
                text_label.config(fg="white")
                indicator.config(bg="#4CAF50")
            else:
                btn.config(fg="#888888")
                text_label.config(fg="#888888")
                indicator.config(bg="#121212")

    def create_user_widget(self):
        # Widget de usuario en la esquina superior derecha
        self.user_widget = tk.Frame(self.root, bg="#121212")
        self.user_widget.place(relx=1.0, y=10, anchor="ne", width=200)
        
        current_account = self.auth_manager.get_current_account()
        if current_account:
            self.update_user_widget(current_account["username"])
        else:
            # Si no hay usuario, mostramos "Guest"
            tk.Label(self.user_widget, text="👤", font=("Segoe UI", 16), 
                    bg="#121212", fg="#888888").pack(side=tk.LEFT, padx=5)
            tk.Label(self.user_widget, text="Guest", font=("Segoe UI", 10), 
                    bg="#121212", fg="#888888").pack(side=tk.LEFT)

    def update_user_widget(self, username):
        """Actualiza tanto el widget de usuario como la barra lateral"""
        try:
            # Actualizar configuración con el nuevo nombre de usuario
            if username and username != "Guest":
                self.config["offline_username"] = username
                self.config["Nombre"] = username
                self.save_config()

            # Limpiar widget actual
            for widget in self.user_widget.winfo_children():
                widget.destroy()
            
            # Crear nuevo contenido usando el nombre guardado
            display_name = username or self.config.get("offline_username") or "Guest"
            if len(display_name) > 15:
                display_name = display_name[:15] + "..."

            icon_label = tk.Label(self.user_widget, text="👤", font=("Segoe UI", 16), 
                                bg="#121212", fg="white")
            icon_label.pack(side=tk.LEFT, padx=5)
            
            username_label = tk.Label(self.user_widget, text=display_name,
                                    font=("Segoe UI", 10), bg="#121212", 
                                    fg="white")
            username_label.pack(side=tk.LEFT)
            
            self.user_widget.update_idletasks()
            self.root.update_idletasks()
            
            # Actualizar también la barra lateral
            self.update_sidebar_user()
        except Exception as e:
            print(f"Error actualizando widgets de usuario: {e}")

    def create_main_content(self):
        if not self.version_manager:
            self.version_manager = VersionManager()
            
        if self.main_content_frame:
            self.main_content_frame.destroy()
            
        self.main_content_frame = tk.Frame(self.root, bg=self.dark_bg)
        self.main_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Banner superior
        banner_frame = tk.Frame(self.main_content_frame, bg="#1A2327", height=200)
        banner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Obtener la versión instalada
        current_version = self.version_manager.get_installed_version()
        version_text = f"Minecraft"
        
        # Título del banner actualizado
        self.title_label = tk.Label(banner_frame, text=version_text, font=self.title_font, bg="#1A2327", fg=self.text_color)
        self.title_label.place(x=30, y=30)
        
        # Subtítulo
        subtitle_label = tk.Label(banner_frame, text="Custom Modpack", font=self.subtitle_font, bg="#1A2327", fg=self.accent_color)
        subtitle_label.place(x=30, y=70)
        
        # Descripción
        description_text = "La mejor versión de Minecraft Java para un rendimiento más fluido es la 1.20.1.\nEn esta versión, el juego corre mejor debido a varios factores que optimizan el rendimiento,\ncomo los mods de FPS. Para Fabric, tenemos Sodium y Extra Sodium, que mejoran notablemente\nla tasa de cuadros por segundo, y para Forge, están Embedium y Extra Embedium,\nque también optimizan el rendimiento, haciendo que el juego sea más estable y rápido."
        description_label = tk.Label(
            banner_frame,
            text=description_text,
            font=("Segoe UI", 10),  # Aumentado de 8 a 10
            bg="#1A2327",
            fg=self.secondary_text,
            justify=tk.LEFT,
            wraplength=900  # Añadido wraplength para que ocupe más ancho
        )
        description_label.place(x=30, y=100)
        
        # Frame para iconos sociales
        social_frame = tk.Frame(banner_frame, bg="#1A2327")
        social_frame.place(x=900, y=70)
        
        # Crear iconos sociales
        social_icons = [
            (os.path.join("assets", "redes", "github.gif"), "GitHub", "https://github.com/jephersonRD"),
            (os.path.join("assets", "redes", "youtube.gif"), "YouTube", "https://www.youtube.com/@jepherson_rd/videos"),
            (os.path.join("assets", "redes", "tiktok.gif"), "TikTok", "https://www.tiktok.com/@jepherson_rd")
        ]
        
        import webbrowser
        from PIL import Image, ImageTk
        
        for i, (icon_path, label, url) in enumerate(social_icons):
            icon_frame = tk.Frame(social_frame, bg="#1A2327")
            icon_frame.pack(side=tk.LEFT, padx=10)
            
            # Cargar y redimensionar la imagen
            try:
                image = Image.open(icon_path)
                image = image.resize((30, 30), Image.LANCZOS)  # Ajusta el tamaño según necesites
                photo = ImageTk.PhotoImage(image)
                
                # Icono
                icon_label = tk.Label(
                    icon_frame,
                    image=photo,
                    bg="#1A2327",
                    cursor="hand2"
                )
                icon_label.image = photo  # Mantener una referencia
                icon_label.pack()
                
            except Exception as e:
                print(f"Error cargando imagen {icon_path}: {e}")
                # Fallback a texto en caso de error
                icon_label = tk.Label(
                    icon_frame,
                    text="•",
                    font=("Segoe UI", 20),
                    bg="#1A2327",
                    fg="#888888",
                    cursor="hand2"
                )
                icon_label.pack()
            
            # Texto debajo del icono
            text_label = tk.Label(
                icon_frame,
                text=label,
                font=("Segoe UI", 8),
                bg="#1A2327",
                fg="#888888"
            )
            text_label.pack()
            
            def on_enter(e, lbl=icon_label, txt=text_label):
                lbl.config(fg="white")
                txt.config(fg="white")
            
            def on_leave(e, lbl=icon_label, txt=text_label):
                lbl.config(fg="#888888")
                txt.config(fg="#888888")
            
            def open_url(link):
                return lambda e: (
                    self.play_click_sound(),  # Reproducir sonido antes de abrir URL
                    webbrowser.open(link)
                )
            
            icon_label.bind("<Enter>", on_enter)
            icon_label.bind("<Leave>", on_leave)
            icon_label.bind("<Button-1>", open_url(url))
            text_label.bind("<Enter>", on_enter)
            text_label.bind("<Leave>", on_leave)
            text_label.bind("<Button-1>", open_url(url))
            
        # Agregar la imagen del juego
        try:
            # Cargar y redimensionar la imagen
            image_path = os.path.join(os.path.dirname(__file__), 'assets', 'fondo', '1.png')
            image = Image.open(image_path)
            image = image.resize((400, 400), Image.LANCZOS)
            
            # Crear una máscara de transparencia si la imagen tiene canal alfa
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGBA', image.size, (26, 35, 39, 255))  # Color #1A2327
                background.paste(image, mask=image.split()[-1])  # -1 es el canal alfa
                image = background
            
            photo = ImageTk.PhotoImage(image)
            
            # Crear label para la imagen
            image_label = tk.Label(
                banner_frame,
                image=photo,
                bg="#1A2327",
                bd=0
            )
            image_label.photo = photo  # Mantener una referencia
            
            # Centrar la imagen horizontalmente
            image_x = (banner_frame.winfo_reqwidth() - 400) // 2  # 400 es el ancho de la imagen
            image_label.place(x=image_x, y=220)  # y=220 para que esté debajo del texto
            
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")

        # Espacio para futuras características
        cards_frame = tk.Frame(self.main_content_frame, bg=self.dark_bg)
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Definir la función para crear rectángulos redondeados
        def create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
            points = [x1+radius, y1,
                     x2-radius, y1,
                     x2, y1,
                     x2, y1+radius,
                     x2, y2-radius,
                     x2, y2,
                     x2-radius, y2,
                     x1+radius, y2,
                     x1, y2,
                     x1, y2-radius,
                     x1, y1+radius,
                     x1, y1]
            return self.create_polygon(points, smooth=True, **kwargs)

        # Agregar el método al Canvas
        tk.Canvas.create_rounded_rectangle = create_rounded_rectangle
        
        # Modificar el frame de lanzamiento para incluir el selector
        launch_frame = tk.Frame(self.main_content_frame, bg=self.dark_bg)
        launch_frame.pack(side=tk.BOTTOM, pady=30)

        # Frame contenedor para el selector y el botón
        controls_frame = tk.Frame(launch_frame, bg=self.dark_bg)
        controls_frame.pack()

        # Frame para el selector de versiones con estilo
        version_frame = tk.Frame(controls_frame, bg=self.dark_bg)
        version_frame.pack(side=tk.LEFT, padx=(0, 20))

        # Obtener versiones instaladas
        installed_versions = []
        if self.version_manager and self.version_manager.installed_versions:
            installed_versions = [v for v in self.version_manager.installed_versions.keys()]

        # Estilo personalizado para el Combobox
        style = ttk.Style()
        style.configure('Rounded.TCombobox',
                       background=self.accent_color,
                       fieldbackground=self.lighter_bg,
                       foreground=self.text_color,
                       arrowcolor=self.text_color)

        # Iniciar el observador de versiones si no está activo
        if not self.version_observer:
            self.version_observer = VersionObserver(self.version_manager, self.refresh_version_list)
            self.version_observer.start()

        # Selector de versiones mejorado
        self.version_selector = ttk.Combobox(
            version_frame,
            values=self.get_installed_versions(),  # Usar nueva función
            state="readonly",
            width=15,
            style='Rounded.TCombobox',
            font=("Segoe UI", 12)
        )
        
        # Forzar actualización inicial
        self.refresh_version_list()
        
        # Actualizar versiones cuando el Combobox obtiene el foco
        self.version_selector.bind('<FocusIn>', lambda e: self.refresh_version_list())
        
        current_version = self.version_manager.get_installed_version()
        if current_version:
            self.version_selector.set(current_version)
        else:
            self.version_selector.set("Seleccionar versión")
        
        self.version_selector.pack(side=tk.BOTTOM)

        # Label para el selector
        tk.Label(
            version_frame,
            text="VERSION",
            font=("Segoe UI", 8, "bold"),
            bg=self.dark_bg,
            fg=self.secondary_text
        ).pack(side=tk.TOP, pady=(0, 5))

        # Canvas para el botón de PLAY (ahora al lado del selector)
        canvas = tk.Canvas(controls_frame, width=200, height=60,
                         bg=self.dark_bg, highlightthickness=0)
        canvas.pack(side=tk.LEFT)

        # El resto del código del botón PLAY se mantiene igual
        rounded_btn = canvas.create_rounded_rectangle(0, 0, 200, 60, radius=30,
                                                    fill=self.accent_color)
        
        play_text = canvas.create_text(100, 20, text="PLAY",
                                     font=("Segoe UI", 16, "bold"),
                                     fill=self.text_color)
        
        status_text = canvas.create_text(100, 42, text="READY TO LAUNCH",
                                       font=("Segoe UI", 8),
                                       fill=self.text_color)

        # Efecto hover
        def on_enter(e):
            canvas.itemconfig(rounded_btn, fill="#3d8c40")  # Verde más oscuro

        def on_leave(e):
            canvas.itemconfig(rounded_btn, fill=self.accent_color)

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)

        def launch_with_sound(event):
            self.play_click_sound()
            self.launch_game(event)

        # Modificar los bindings del botón PLAY
        canvas.tag_bind(rounded_btn, "<Button-1>", launch_with_sound)
        canvas.tag_bind(play_text, "<Button-1>", launch_with_sound)
        
        # Guardar referencia al texto de estado
        self.status_text = status_text

        # Actualizar la lista de versiones instaladas
        self.refresh_version_list()

    @staticmethod
    def version_key(version):
        """Función auxiliar para ordenar versiones de Minecraft correctamente"""
        try:
            # Dividir la versión en sus componentes
            parts = version.split('.')
            # Convertir cada parte a entero, usar 0 si no hay número
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            # Retornar una tupla para comparación
            return (major, minor, patch)
        except:
            # Si hay algún error, retornar (0,0,0) para poner la versión al final
            return (0, 0, 0)

    def get_installed_versions(self):
        """Obtiene la lista actualizada de versiones instaladas"""
        try:
            versions = []
            if self.version_observer and self.version_observer.known_versions:
                versions = list(self.version_observer.known_versions)
            elif self.version_manager and self.version_manager.installed_versions:
                versions = list(self.version_manager.installed_versions.keys())
            
            # Ordenar usando el método estático
            return sorted(versions, key=MinecraftLauncher.version_key, reverse=True)
        except Exception as e:
            print(f"Error obteniendo versiones: {e}")
            return []

    def refresh_version_list(self):
        """Actualiza la lista de versiones en el selector"""
        try:
            if hasattr(self, 'version_selector'):
                # Forzar actualización inmediata de versiones instaladas
                self.version_manager.refresh_installed_versions()
                
                # Ordenar usando el método estático
                versions = sorted(
                    list(self.version_manager.installed_versions.keys()),
                    key=MinecraftLauncher.version_key,
                    reverse=True
                )
                
                current = self.version_selector.get()
                self.version_selector['values'] = versions
                
                # Mantener la selección actual o seleccionar la más reciente
                if current in versions:
                    self.version_selector.set(current)
                elif versions:
                    self.version_selector.set(versions[0])  # Seleccionar la versión más nueva
                else:
                    self.version_selector.set("Seleccionar versión")
                
                # Forzar actualización visual inmediata
                self.version_selector.update_idletasks()
                if hasattr(self, 'main_content_frame'):
                    self.main_content_frame.update_idletasks()
                
        except Exception as e:
            print(f"Error en refresh_version_list: {e}")

    def start_version_checker(self):
        """Inicia el verificador periódico de versiones"""
        # Cancelar timer existente si hay uno
        if self.check_versions_timer:
            self.root.after_cancel(self.check_versions_timer)
        self.check_versions()

    def check_versions(self):
        """Verifica periódicamente si hay nuevas versiones instaladas"""
        try:
            self.refresh_version_list()
        except Exception as e:
            print(f"Error checking versions: {e}")
        finally:
            # Programar la próxima verificación en 2 segundos
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.check_versions_timer = self.root.after(2000, self.check_versions)

    def get_appropriate_java(self, minecraft_version):
        try:
            # Detectar versión requerida
            version_parts = minecraft_version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0

            print(f"DEBUG: Detectando Java para Minecraft {minecraft_version}")

            # Determinar versión de Java necesaria
            if major == 1 and minor <= 16:
                required_java = "Java 8 (Minecraft 1.1 - 1.16.5)"
                java_version = "8"
                print(f"DEBUG: Versión {minecraft_version}, requiere Java 8")
            else:
                required_java = "Java 17 (Minecraft 1.17+)"
                java_version = "17"
                print(f"DEBUG: Versión {minecraft_version}, requiere Java 17")

            # Intentar obtener Java instalado
            from Java_Downloader import JavaDownloader
            downloader = JavaDownloader()
            java_path = downloader.get_java_path(java_version)

            if java_path and os.path.exists(java_path):
                print(f"DEBUG: Usando {required_java} en {java_path}")
                return java_path

            print(f"DEBUG: {required_java} no encontrado, iniciando descarga...")
            
            # Mostrar mensaje antes de iniciar la descarga
            messagebox.showinfo(
                "Descarga de Java",
                f"Se necesita Java {java_version} para esta versión de Minecraft.\n"
                f"Se iniciará la descarga automáticamente."
            )

            def on_complete(success, installed_java_path=None):
                if success and installed_java_path:
                    print(f"DEBUG: Java {java_version} instalado en {installed_java_path}")
                    self.launch_game(None)
                else:
                    print("DEBUG: Error en la instalación de Java")
                    messagebox.showerror(
                        "Error de Java",
                        f"No se pudo instalar Java {java_version}.\n" +
                        f"Esta versión de Minecraft requiere Java {java_version}.\n" +
                        f"Por favor, intenta nuevamente o instálalo manualmente."
                    )

            # Iniciar descarga e instalación pasando la ventana principal
            Thread(
                target=lambda: downloader.download_and_install(java_version, on_complete, self.root),
                daemon=True
            ).start()
            return None

        except Exception as e:
            print(f"Error detectando Java: {e}")
            self.root.deiconify()
            return None

    def download_resources(self):
        try:
            # Verificar si los archivos ya existen
            if self.check_version_files():
                self.update_status("INICIANDO...")
                self.launch_minecraft()
                return

            # Variables para seguimiento de descarga
            total_size = 0
            downloaded_size = 0

            def progress_callback(name, current, total):
                nonlocal total_size, downloaded_size
                if total > 0:  # Solo si hay un tamaño total válido
                    downloaded_size += current
                    total_size += total
                    percentage = min(99, int((downloaded_size / total_size) * 100))
                    size_mb = total_size / 1048576  # Convertir a MB
                    self.update_status(f"Descargando... {percentage}% ({size_mb:.1f} MB)")

            try:
                minecraft_launcher_lib.install.install_minecraft_version(
                    self.version_selector.get(),
                    self.minecraft_directory,
                    callback={
                        "setStatus": lambda text: None,  # Ignorar el estado predeterminado
                        "setProgress": progress_callback
                    }
                )
                
                # Forzar actualización inmediata de la lista de versiones
                self.version_manager.refresh_installed_versions()
                self.refresh_version_list()
                
                # Seleccionar automáticamente la versión recién instalada
                if hasattr(self, 'version_selector'):
                    self.version_selector.set(self.version_selector.get())
                
                # Mostrar mensaje de éxito brevemente
                self.update_status("¡DESCARGA COMPLETA!")
                if self.root and self.root.winfo_exists():
                    self.root.after(1000, lambda: self.update_status("LISTO PARA JUGAR"))
                    self.root.after(1000, self.launch_minecraft)

            except Exception as download_error:
                if "Failed to resolve" in str(download_error) or "Max retries exceeded" in str(download_error):
                    if self.check_version_files():
                        self.update_status("INICIANDO EN MODO OFFLINE...")
                        self.launch_minecraft()
                    else:
                        error_message = "No hay conexión a Internet y los archivos del juego no están completos.\nNecesitas conexión a Internet para la primera descarga."
                        self.handle_error(error_message)
                else:
                    error_message = f"Error en la descarga: {str(download_error)}"
                    print(error_message)
                    self.handle_error(error_message)

        except Exception as e:
            error_message = f"Error general: {str(e)}"
            print(error_message)
            self.handle_error(error_message)

    def launch_game(self, event=None):
        selected_version = self.version_selector.get()
        if not selected_version or selected_version == "Seleccionar versión":
            messagebox.showinfo("Info", "Por favor, selecciona una versión")
            return

        try:
            canvas = event.widget if event else None

            def update_status(text):
                def update():
                    if canvas and hasattr(self, 'status_text'):
                        canvas.itemconfig(self.status_text, text=text)
                if self.root and self.root.winfo_exists():
                    self.root.after(0, update)

            def handle_error(error_msg):
                def show_error():
                    messagebox.showerror("Error", str(error_msg))
                    if canvas and hasattr(self, 'status_text'):
                        canvas.itemconfig(self.status_text, text="ERROR")
                if self.root and self.root.winfo_exists():
                    self.root.after(0, show_error)

            def check_version_files():
                version_dir = os.path.join(self.minecraft_directory, "versions", selected_version)
                jar_path = os.path.join(version_dir, f"{selected_version}.jar")
                json_path = os.path.join(version_dir, f"{selected_version}.json")
                
                if os.path.exists(jar_path) and os.path.exists(json_path):
                    return True
                return False

            def download_resources():
                try:
                    # Verificar si los archivos ya existen
                    if check_version_files():
                        update_status("INICIANDO...")
                        launch_minecraft()
                        return

                    # Si no existen, intentar descargar
                    try:
                        minecraft_launcher_lib.install.install_minecraft_version(
                            selected_version,
                            self.minecraft_directory,
                            callback={"setStatus": update_status}
                        )
                        if self.root and self.root.winfo_exists():
                            self.root.after(0, launch_minecraft)
                    except Exception as download_error:
                        if "Failed to resolve" in str(download_error) or "Max retries exceeded" in str(download_error):
                            # Error de conexión, verificar si tenemos los archivos necesarios
                            if check_version_files():
                                update_status("INICIANDO EN MODO OFFLINE...")
                                launch_minecraft()
                            else:
                                error_message = "No hay conexión a Internet y los archivos del juego no están completos.\nNecesitas conexión a Internet para la primera descarga."
                                handle_error(error_message)
                        else:
                            error_message = f"Error en la descarga: {str(download_error)}"
                            print(error_message)
                            handle_error(error_message)

                except Exception as e:
                    error_message = f"Error general: {str(e)}"
                    print(error_message)
                    handle_error(error_message)

            def launch_minecraft():
                try:
                    # Configuración de login
                    stored_username = self.config.get("offline_username") or self.config.get("Nombre", "Player")
                    login_data = self.auth_manager.get_login_data() or {
                        "username": stored_username,
                        "uuid": str(uuid.uuid4()),
                        "accessToken": "0",
                        "clientToken": str(uuid.uuid4()),
                        "type": "offline"
                    }

                    # Obtener Java y verificar
                    java_path = self.get_appropriate_java(selected_version)
                    if not java_path:
                        print("DEBUG: No se encontró Java")
                        return
                    
                    print(f"DEBUG: Verificando Java en: {java_path}")
                    if not os.path.exists(java_path):
                        print("DEBUG: Ruta de Java no existe")
                        messagebox.showerror("Error", "La ruta de Java no existe")
                        return

                    # Configurar argumentos
                    ram = self.config.get("RAM", "2")
                    version_number = float('.'.join(selected_version.split('.')[:2]))
                    
                    # Argumentos JVM básicos para debug
                    jvm_arguments = [
                        f"-Xmx{ram}G",
                        f"-Xms{ram}G",
                        "-XX:+UseG1GC",
                        "-Xmn128M"
                    ]

                    # Obtener comando base de Minecraft
                    try:
                        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                            version=selected_version,
                            minecraft_directory=self.minecraft_directory,
                            options={
                                "username": login_data["username"],
                                "uuid": login_data["uuid"],
                                "token": login_data["accessToken"]
                            }
                        )
                        print(f"DEBUG: Comando base generado: {' '.join(minecraft_command)}")
                    except Exception as e:
                        print(f"DEBUG: Error generando comando base: {e}")
                        raise

                    # Construir comando final
                    final_command = [java_path] + jvm_arguments + minecraft_command[1:]
                    print(f"DEBUG: Comando final: {' '.join(final_command)}")

                    # Verificar directorios y permisos
                    mc_dir = os.path.join(self.minecraft_directory, "versions", selected_version)
                    if not os.path.exists(mc_dir):
                        print(f"DEBUG: Directorio de versión no existe: {mc_dir}")
                        messagebox.showerror("Error", "Directorio de versión no encontrado")
                        return

                    try:
                        # Lanzar proceso con salida visible para debug
                        import subprocess
                        
                        # Crear archivo de log
                        log_path = os.path.join(self.minecraft_directory, "launcher_log.txt")
                        log_file = open(log_path, "w", encoding="utf-8")
                        
                        print("DEBUG: Iniciando proceso de Minecraft...")
                        process = subprocess.Popen(
                            final_command,
                            stdout=log_file,
                            stderr=log_file,
                            cwd=self.minecraft_directory,
                            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                        )
                        
                        # Ocultar launcher solo si el proceso inició
                        if process.pid:
                            print(f"DEBUG: Minecraft iniciado con PID: {process.pid}")
                            self.root.withdraw()
                        else:
                            print("DEBUG: Error al iniciar proceso")
                            raise Exception("No se pudo iniciar el proceso")

                        def check_minecraft():
                            try:
                                if process.poll() is not None:
                                    print(f"DEBUG: Proceso terminado con código: {process.returncode}")
                                    log_file.close()
                                    self.root.deiconify()
                                    if process.returncode != 0:
                                        messagebox.showerror("Error", 
                                            f"Minecraft cerró con error. Revisa el log en:\n{log_path}")
                                else:
                                    self.root.after(1000, check_minecraft)
                            except Exception as e:
                                print(f"DEBUG: Error en check_minecraft: {e}")
                                self.root.deiconify()

                        check_minecraft()

                    except Exception as e:
                        print(f"DEBUG: Error crítico al lanzar: {e}")
                        self.root.deiconify()
                        messagebox.showerror("Error", f"Error al iniciar Minecraft: {str(e)}")

                except Exception as e:
                    print(f"DEBUG: Error general: {e}")
                    if canvas and hasattr(self, 'status_text'):
                        canvas.itemconfig(self.status_text, text="ERROR")
                    self.root.deiconify()

            # Iniciar la descarga en un hilo separado
            Thread(target=download_resources, daemon=True).start()

        except Exception as e:
            error_message = f"Error general: {str(e)}"
            print(error_message)
            messagebox.showerror("Error", error_message)
            if canvas and hasattr(self, 'status_text'):
                canvas.itemconfig(self.status_text, text="ERROR")

    def show_profile_window(self):
        if hasattr(self, 'current_window') and self.current_window:
            if hasattr(self.current_window, 'stop_sound'):
                self.current_window.stop_sound()
        self.active_section.set("profile")
        self.update_nav_buttons()
        if self.main_content_frame:
            self.main_content_frame.destroy()
        
        self.main_content_frame = tk.Frame(self.root, bg=self.dark_bg)
        self.main_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.current_window = ProfileWindow(self.main_content_frame, self.update_user_widget)

    def show_home_window(self):
        if hasattr(self, 'current_window') and self.current_window:
            if hasattr(self.current_window, 'stop_sound'):
                self.current_window.stop_sound()
        self.active_section.set("home")
        self.update_nav_buttons()
        # Limpiar ventana actual
        if self.main_content_frame:
            self.main_content_frame.destroy()
            
        # Crear nuevo contenido
        self.create_main_content()

    def show_game_window(self):
        if hasattr(self, 'current_window') and self.current_window:
            if hasattr(self.current_window, 'stop_sound'):
                self.current_window.stop_sound()
        def on_version_installed(version):
            def show_message():
                from mensajeDoloand import MensajeDescarga
                MensajeDescarga(self.root, version)

            self.root.after(100, show_message)
            self.root.after(100, self.refresh_version_list)
            self.root.after(100, self.create_main_content)

        self.active_section.set("games")
        self.update_nav_buttons()
        if self.main_content_frame:
            self.main_content_frame.destroy()
        
        self.main_content_frame = tk.Frame(self.root, bg=self.dark_bg)
        self.main_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.current_window = GameWindow(
            self.main_content_frame,
            version_callback=on_version_installed,
            refresh_callback=lambda: self.root.after(100, self.create_main_content)
        )

    def show_settings_window(self):
        if hasattr(self, 'current_window') and self.current_window:
            if hasattr(self.current_window, 'stop_sound'):
                self.current_window.stop_sound()
        self.active_section.set("settings")
        self.update_nav_buttons()
        if self.main_content_frame:
            self.main_content_frame.destroy()
            
        self.main_content_frame = tk.Frame(self.root, bg=self.dark_bg)
        self.main_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.current_window = SettingsWindow(self.main_content_frame)

    def show_mods_window(self):
        """Muestra la ventana de mods"""
        # Detener el sonido de la ventana anterior si existe
        if hasattr(self, 'current_window') and self.current_window:
            if hasattr(self.current_window, 'stop_sound'):
                self.current_window.stop_sound()

        self.active_section.set("mods")
        self.update_nav_buttons()
        if self.main_content_frame:
            self.main_content_frame.destroy()
            
        self.main_content_frame = tk.Frame(self.root, bg=self.dark_bg)
        self.main_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        from mods_window import ModsWindow
        self.current_window = ModsWindow(self.main_content_frame)

    def __del__(self):
        """Destructor para limpiar recursos"""
        if self.version_observer:
            self.version_observer.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen(app)
    sys.exit(app.exec_())
