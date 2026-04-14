import tkinter as tk
from pygame import mixer
import os

class MensajeDescarga:
    def __init__(self, parent, version):
        # Reproducir sonido de éxito
        try:
            mixer.init()
            success_sound_path = os.path.join(os.path.dirname(__file__), 'sonidos', '2.mp3')
            success_sound = mixer.Sound(success_sound_path)
            success_sound.set_volume(0.5)  # Ajustar volumen al 50%
            success_sound.play()
        except Exception as e:
            print(f"Error reproduciendo sonido de éxito: {e}")

        self.window = tk.Toplevel(parent)
        self.window.title("Descarga Completada")
        
        # Configurar ventana
        window_width = 400
        window_height = 200
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
        
        # Icono de éxito
        success_label = tk.Label(
            main_frame,
            text="✅",
            font=("Segoe UI", 48),
            bg="#161616",
            fg="#4CAF50"
        )
        success_label.pack(pady=(20, 10))
        
        # Mensaje
        message = f"¡Minecraft {version} se ha\ndescargado correctamente!"
        message_label = tk.Label(
            main_frame,
            text=message,
            bg="#161616",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            wraplength=350,
            justify="center"
        )
        message_label.pack(pady=10)
        
        # Botón Aceptar (cambiado a azul)
        accept_button = tk.Button(
            main_frame,
            text="Aceptar",
            command=self.window.destroy,
            bg="#2196F3",  # Cambiado a azul
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=15,
            height=1,
            bd=0,
            relief="flat"
        )
        accept_button.pack(pady=(10, 20))
        
        # Efectos hover para el botón (actualizado para azul)
        def on_enter(e):
            e.widget.configure(bg="#1976D2")  # Azul más oscuro
        
        def on_leave(e):
            e.widget.configure(bg="#2196F3")  # Volver al azul original
        
        accept_button.bind("<Enter>", on_enter)
        accept_button.bind("<Leave>", on_leave)
        
        # Agregar temporizador de auto-cierre
        self.window.after(4000, self.window.destroy)  # 4000ms = 4s
        
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

# Para usar esta ventana, importarla y llamarla así:
# MensajeDescarga(root, "1.20.1")
