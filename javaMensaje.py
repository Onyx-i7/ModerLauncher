import tkinter as tk
from pygame import mixer
import os
import webbrowser

class JavaVersionAlert:
    def __init__(self, parent, mc_version, required_java):
        # Reproducir sonido de alerta
        try:
            mixer.init()
            alert_sound_path = os.path.join(os.path.dirname(__file__), 'sonidos', 'alert.mp3')
            alert_sound = mixer.Sound(alert_sound_path)
            alert_sound.set_volume(0.5)
            alert_sound.play()
        except Exception as e:
            print(f"Error reproduciendo sonido de alerta: {e}")

        self.window = tk.Toplevel(parent)
        self.window.title("Java Requerido")
        self.required_java = required_java
        
        # Configurar ventana
        window_width = 400
        window_height = 250
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
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
        
        # Icono de advertencia
        warning_label = tk.Label(
            main_frame,
            text="⚠️",
            font=("Segoe UI", 48),
            bg="#161616",
            fg="#FFB900"
        )
        warning_label.pack(pady=(20, 10))
        
        # Mensaje
        message = f"Se requiere Java {required_java}\npara Minecraft {mc_version}"
        message_label = tk.Label(
            main_frame,
            text=message,
            bg="#161616",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            justify="center"
        )
        message_label.pack(pady=5)
        
        # Submensaje
        submessage = "Por favor, instala la versión correcta de Java\no selecciona otra versión de Minecraft"
        submessage_label = tk.Label(
            main_frame,
            text=submessage,
            bg="#161616",
            fg="#CCCCCC",
            font=("Segoe UI", 10),
            justify="center"
        )
        submessage_label.pack(pady=5)
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg="#161616")
        buttons_frame.pack(pady=15)
        
        # Botón Descargar Java
        download_button = tk.Button(
            buttons_frame,
            text="Descargar Java",
            command=self.download_java,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=15,
            bd=0,
            relief="flat"
        )
        download_button.pack(pady=5)
        
        # Botón Ir a Ajustes
        settings_button = tk.Button(
            buttons_frame,
            text="Ir a Ajustes",
            command=self.go_to_settings,
            bg="#2196F3",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=15,
            bd=0,
            relief="flat"
        )
        settings_button.pack(pady=5)
        
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
        
        # Temporizador para cerrar
        self.window.after(10000, self.window.destroy)  # 10 segundos
        
    def download_java(self):
        java_urls = {
            "17": "https://adoptium.net/temurin/releases/?version=17",
            "8": "https://adoptium.net/temurin/releases/?version=8"
        }
        webbrowser.open(java_urls.get(self.required_java, java_urls["17"]))
        self.window.destroy()
        
    def go_to_settings(self):
        # Esta función debe ser sobreescrita al crear la instancia
        self.window.destroy()
