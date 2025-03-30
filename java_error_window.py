import tkinter as tk
from tkinter import ttk
import webbrowser
import threading
from tkinter import messagebox
import json

class JavaErrorWindow:
    def __init__(self, parent, minecraft_version, required_java):
        self.window = tk.Toplevel(parent)
        self.window.title("Java no encontrado")
        self.window.overrideredirect(True)  # Quitar barra de título
        
        # Configurar ventana
        window_width = 400
        window_height = 280
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.window.configure(bg="#161616")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(
            self.window,
            bg="#161616",
            highlightbackground="#333333",
            highlightthickness=2
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Barra superior personalizada
        title_bar = tk.Frame(main_frame, bg="#121212", height=30)
        title_bar.pack(fill="x", pady=(0, 10))
        
        # Botón cerrar
        close_btn = tk.Button(
            title_bar,
            text="✕",
            bg="#121212",
            fg="#888888",
            font=("Segoe UI", 9),
            bd=0,
            command=self.window.destroy,
            cursor="hand2"
        )
        close_btn.pack(side="right", padx=10)
        
        # Título
        title = tk.Label(
            title_bar,
            text="Java no encontrado",
            bg="#121212",
            fg="white",
            font=("Segoe UI", 10)
        )
        title.pack(side="left", padx=10)
        
        # Resto de widgets
        warning_label = tk.Label(
            main_frame,
            text="⚠️",
            font=("Segoe UI", 48),
            bg="#161616",
            fg="#FFB900"
        )
        warning_label.pack(pady=(10, 10))
        
        message = f"Para ejecutar Minecraft {minecraft_version} necesitas\ntener instalado Java {required_java}."
        message_label = tk.Label(
            main_frame,
            text=message,
            bg="#161616",
            fg="white",
            font=("Segoe UI", 11),
            justify="center"
        )
        message_label.pack(pady=(0, 20))
        
        # Solo botón de descarga
        download_btn = tk.Button(
            main_frame,
            text="Instalar Java",
            command=lambda: self.download_java(required_java),
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2"
        )
        download_btn.pack(pady=(0, 30))
        
        # Efecto hover
        download_btn.bind("<Enter>", lambda e: download_btn.configure(bg="#3d8c40"))
        download_btn.bind("<Leave>", lambda e: download_btn.configure(bg="#4CAF50"))
        
        # Hacer la ventana arrastrable
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<ButtonRelease-1>", self.stop_move)
        title_bar.bind("<B1-Motion>", self.do_move)
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

    def on_enter(self, e, button):
        if button["bg"] == "#4CAF50":
            button.configure(bg="#3d8c40")
        else:
            button.configure(bg="#1976D2")
    
    def on_leave(self, e, button):
        if button["bg"] == "#3d8c40":
            button.configure(bg="#4CAF50")
        else:
            button.configure(bg="#2196F3")
    
    def download_java(self, java_version):
        from Java_Downloader import JavaDownloader
        downloader = JavaDownloader()
        
        def on_complete(success, java_path=None):
            if success and java_path:
                # Actualizar settings.json con la nueva ruta de Java
                try:
                    with open('settings.json', 'r') as f:
                        settings = json.load(f)
                    
                    if java_version == "17":
                        java_key = "Java 17 (Minecraft 1.17 - 1.20.4)"
                    else:
                        java_key = "Java 8 (Minecraft 1.1 - 1.16.5)"
                    
                    if 'java_versions' not in settings:
                        settings['java_versions'] = {}
                    
                    settings['java_versions'][java_key] = java_path
                    
                    with open('settings.json', 'w') as f:
                        json.dump(settings, f)
                        
                    self.window.destroy()
                    messagebox.showinfo(
                        "Java Instalado",
                        "Java se ha instalado y configurado correctamente. Puedes iniciar Minecraft ahora."
                    )
                    if hasattr(self, 'on_settings_click'):
                        self.on_settings_click()
                except Exception as e:
                    print(f"Error actualizando settings.json: {e}")
                    messagebox.showerror(
                        "Error",
                        "Java se instaló pero hubo un error al guardar la configuración."
                    )
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo instalar Java. Por favor, intenta descargarlo manualmente."
                )
        
        # Iniciar descarga e instalación automática
        thread = threading.Thread(
            target=lambda: downloader.download_and_install(java_version, on_complete),
            daemon=True
        )
        thread.start()
    
    def go_to_settings(self):
        self.window.destroy()
        if hasattr(self, 'on_settings_click'):
            self.on_settings_click()
