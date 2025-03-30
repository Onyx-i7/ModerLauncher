import tkinter as tk
from PIL import Image, ImageTk
import os
from pygame import mixer  # Añadimos mixer para el sonido

class ByeWindow:
    def __init__(self, parent):
        self.parent = parent
        self.result = False
        
        # Inicializar y cargar el sonido
        mixer.init()
        self.sound_path = os.path.join(os.path.dirname(__file__), 'sonidos', 'click_botton.mp3')
        try:
            self.click_sound = mixer.Sound(self.sound_path)
            self.click_sound.set_volume(0.5)
        except:
            print("No se pudo cargar el sonido de click")
            self.click_sound = None

        # Crear ventana
        self.window = tk.Toplevel(parent)
        self.window.title("Confirmar salida")
        
        # Configurar ventana
        window_width = 300
        window_height = 250  # Aumentado de 180 a 250 para dar más espacio
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configuración de la ventana
        self.window.configure(bg="#161616")
        self.window.overrideredirect(True)  # Quitar bordes de ventana
        self.window.attributes('-topmost', True)
        
        # Frame principal
        main_frame = tk.Frame(
            self.window,
            bg="#161616",
            highlightbackground="#333333",
            highlightthickness=2
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Reemplazar emojis con imagen
        image_frame = tk.Frame(main_frame, bg="#161616")
        image_frame.pack(pady=(10, 5))  # Reducido el padding vertical
        
        # Cargar y redimensionar la imagen
        image_path = os.path.join(os.path.dirname(__file__), 'assets', 'bye', 'bye.png')
        try:
            # Cargar la imagen y redimensionarla
            original_image = Image.open(image_path)
            # Redimensionar manteniendo la proporción pero un poco más pequeña
            desired_width = 80  # Reducido de 100 a 80
            aspect_ratio = original_image.height / original_image.width
            desired_height = int(desired_width * aspect_ratio)
            resized_image = original_image.resize((desired_width, desired_height), Image.Resampling.LANCZOS)
            
            # Convertir a PhotoImage
            self.photo = ImageTk.PhotoImage(resized_image)
            
            # Crear y mostrar el label con la imagen
            image_label = tk.Label(
                image_frame,
                image=self.photo,
                bg="#161616"
            )
            image_label.pack()
        except Exception as e:
            print(f"Error cargando la imagen: {e}")
            # Mostrar un texto alternativo si la imagen falla
            tk.Label(
                image_frame,
                text="ModerLauncher",
                font=("Segoe UI", 16, "bold"),
                bg="#161616",
                fg="white"
            ).pack()
        
        # Mensaje
        message_label = tk.Label(
            main_frame,
            text="¿Quieres cerrar ModerLauncher?",
            bg="#161616",
            fg="white",
            font=("Segoe UI", 11, "bold")
        )
        message_label.pack(pady=(5, 15))  # Ajustado el padding
        
        # Frame para botones
        buttons_frame = tk.Frame(main_frame, bg="#161616")
        buttons_frame.pack(pady=(0, 15), expand=True)  # Añadido expand=True
        
        # Botón No
        no_button = tk.Button(
            buttons_frame,
            text="No",
            command=self.on_no_with_sound,  # Cambiamos el comando
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=10,
            bd=0,
            relief="flat",
            cursor="hand2"
        )
        no_button.pack(side=tk.LEFT, padx=10)
        
        # Botón Sí
        yes_button = tk.Button(
            buttons_frame,
            text="Sí",
            command=self.on_yes,
            bg="#FF5252",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=10,
            bd=0,
            relief="flat",
            cursor="hand2"
        )
        yes_button.pack(side=tk.LEFT, padx=10)
        
        # Efectos hover para los botones
        def on_enter(e):
            if (e.widget == no_button):
                e.widget.configure(bg="#3d8c40")
            else:
                e.widget.configure(bg="#ff3333")
        
        def on_leave(e):
            if (e.widget == no_button):
                e.widget.configure(bg="#4CAF50")
            else:
                e.widget.configure(bg="#FF5252")
        
        no_button.bind("<Enter>", on_enter)
        no_button.bind("<Leave>", on_leave)
        yes_button.bind("<Enter>", on_enter)
        yes_button.bind("<Leave>", on_leave)
        
        # Hacer la ventana arrastrable
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
        
        # Centrar la ventana
        self.window.update_idletasks()
        self.window.grab_set()
        
    def play_click_sound(self):
        """Reproduce el sonido de click si está disponible"""
        if hasattr(self, 'click_sound') and self.click_sound:
            try:
                self.click_sound.play()
            except:
                pass
                
    def on_no_with_sound(self):
        """Reproduce el sonido y ejecuta la acción del botón No"""
        self.play_click_sound()
        self.on_no()
        
    def on_yes(self):
        try:
            # Cargar y reproducir el sonido del creeper
            creeper_sound = mixer.Sound(os.path.join(os.path.dirname(__file__), 'sonidos', 'creeper.mp3'))
            creeper_sound.set_volume(0.5)
            creeper_sound.play()
            # Pequeña pausa para que el sonido se reproduzca antes de cerrar
            self.window.after(500, self._close_window)
        except Exception as e:
            print(f"Error reproduciendo sonido del creeper: {e}")
            self._close_window()
    
    def _close_window(self):
        self.result = True
        self.window.destroy()
        
    def on_no(self):
        self.result = False
        self.window.destroy()
        
def ask_quit(root):
    # Inicializar mixer para el sonido
    mixer.init()
    sound_path = os.path.join(os.path.dirname(__file__), 'sonidos', 'click_botton.mp3')
    try:
        click_sound = mixer.Sound(sound_path)
        click_sound.set_volume(0.5)
        click_sound.play()
    except:
        print("No se pudo reproducir el sonido de click")
    
    bye_window = ByeWindow(root)
    root.wait_window(bye_window.window)
    return bye_window.result
