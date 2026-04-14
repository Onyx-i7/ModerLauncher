import tkinter as tk
from tkinter import messagebox

class LoadingSpinner(tk.Canvas):
    def __init__(self, parent, size=50, color="#25b09b"):
        super().__init__(parent, width=size, height=size, bg="#161616", highlightthickness=0)
        self.size = size
        self.color = color
        self._angle = 0
        self._running = False
        
        # Crear arco inicial
        self.arc = self.create_arc(5, 5, size-5, size-5, 
                                 start=0, extent=36,
                                 fill=color)
        
    def start(self):
        self._running = True
        self._animate()
        
    def stop(self):
        self._running = False
        
    def _animate(self):
        if not self._running:
            return
        
        self._angle = (self._angle + 10) % 360
        self.delete(self.arc)
        self.arc = self.create_arc(5, 5, self.size-5, self.size-5,
                                 start=self._angle, extent=36,
                                 fill=self.color)
        
        self.after(20, self._animate)

class DownloadProgress:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Descargando")
        self.error_detected = False
        self.error_timeout = None
        
        # Configurar ventana
        window_width = 400
        window_height = 250  # Aumentado para acomodar el cuadro de texto
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
        
        # Spinner personalizado
        self.spinner = LoadingSpinner(main_frame, size=50, color="#25b09b")
        self.spinner.pack(pady=(20, 10))
        self.spinner.start()
        
        # Mensaje principal
        self.message_label = tk.Label(
            main_frame,
            text="Descargando los archivos necesarios...",
            bg="#161616",
            fg="white",
            font=("Segoe UI", 12)
        )
        self.message_label.pack(pady=10)
        
        # Cuadro de texto para detalles de la descarga
        self.details_frame = tk.Frame(
            main_frame,
            bg="#161616",
            highlightbackground="#333333",
            highlightthickness=1
        )
        self.details_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20), ipady=5)
        
        self.details_text = tk.Text(
            self.details_frame,
            height=4,
            width=40,
            bg="#202020",
            fg="#8f8f8f",
            font=("Consolas", 9),
            relief="flat",
            padx=10,
            pady=5
        )
        self.details_text.pack(fill="both", expand=True)
        
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

    def update_status(self, text):
        try:
            # Detectar errores comunes en el texto
            error_keywords = ["error", "failed", "cannot", "exception", "unable"]
            is_error = any(keyword in text.lower() for keyword in error_keywords)
            
            self.details_text.insert('end', text + '\n')
            self.details_text.see('end')
            
            if is_error:
                self.error_detected = True
                # Cancelar el timeout anterior si existe
                if self.error_timeout:
                    self.window.after_cancel(self.error_timeout)
                # Programar cierre en 3 segundos
                self.error_timeout = self.window.after(3000, self.show_error_and_close)
            
            self.window.update()
            
        except tk.TclError:  # Si la ventana fue cerrada
            pass
        except Exception as e:
            print(f"Error en update_status: {e}")
            self.show_error_and_close()

    def show_error_and_close(self):
        try:
            if self.error_detected:
                messagebox.showerror(
                    "Error de Descarga",
                    "Se produjo un error durante la descarga.\nPor favor, intenta nuevamente."
                )
            self.close()
        except:
            pass

    def close(self):
        try:
            if self.error_timeout:
                self.window.after_cancel(self.error_timeout)
            self.spinner.stop()
            self.window.destroy()
        except:
            pass
