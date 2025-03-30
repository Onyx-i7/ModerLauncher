import tkinter as tk
from pygame import mixer
import os

class ModsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.sound = None
        self.setup_sound()
        self.create_mods_window()

    def setup_sound(self):
        try:
            # Asegurarse de que mixer está inicializado
            if not mixer.get_init():
                mixer.init()
            
            # Ruta al archivo de sonido
            sound_path = os.path.join(os.path.dirname(__file__), 'sonidos', 'Fallos-tecnicos.mp3')
            
            # Cargar y reproducir el sonido en bucle
            if os.path.exists(sound_path):
                self.sound = mixer.Sound(sound_path)
                self.sound.play(loops=-1)  # -1 significa reproducir en bucle infinito
                self.sound.set_volume(0.5)  # Ajustar volumen al 50%
        except Exception as e:
            print(f"Error al configurar el sonido: {e}")

    def stop_sound(self):
        """Detiene la reproducción del sonido"""
        try:
            if self.sound:
                self.sound.stop()
                self.sound = None
        except Exception as e:
            print(f"Error al detener el sonido: {e}")

    def __del__(self):
        """Asegura que el sonido se detenga cuando se destruye la ventana"""
        self.stop_sound()

    def create_mods_window(self):
        # Frame principal
        main_frame = tk.Frame(self.parent, bg="#1E1E1E")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Frame central para el contenido
        center_frame = tk.Frame(main_frame, bg="#252525")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Título "Coming Soon"
        title_label = tk.Label(
            center_frame,
            text="🚧 Coming Soon 🚧",
            font=("Segoe UI", 40, "bold"),
            bg="#252525",
            fg="#4CAF50"
        )
        title_label.pack(pady=20)

        # Mensaje con emojis
        message_text = "¡La sección de mods está en desarrollo! 🛠️\n\n"
        message_text += "Próximamente podrás:\n"
        message_text += "📦 Instalar mods fácilmente\n"
        message_text += "🔄 Actualizar tus mods\n"
        message_text += "⚙️ Configurar modpacks\n"
        message_text += "🎮 ¡Y mucho más!\n\n"
        message_text += "🌟 ¡Vuelve pronto! 🌟"

        message_label = tk.Label(
            center_frame,
            text=message_text,
            font=("Segoe UI", 14),
            bg="#252525",
            fg="white",
            justify=tk.CENTER
        )
        message_label.pack(pady=20)

