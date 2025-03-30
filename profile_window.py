import tkinter as tk
from tkinter import ttk, messagebox
from auth_manager import AuthManager
import minecraft_launcher_lib

class ProfileWindow:
    def __init__(self, parent, update_callback=None):
        self.parent = parent
        self.update_callback = update_callback  # Para actualizar el widget de usuario
        self.auth_manager = AuthManager()
        self.current_account = self.auth_manager.get_current_account()
        self.root = self.get_root(parent)  # Obtener la ventana raíz
        self.create_profile_view()
        self.setup_refresh_timer()

    def setup_refresh_timer(self):
        """Configura un timer para actualizar la UI periódicamente"""
        def refresh_ui():
            if self.parent.winfo_exists():
                current = self.auth_manager.get_current_account()
                if current != self.current_account:
                    self.current_account = current
                    self.refresh_profile_view()
                self.parent.after(1000, refresh_ui)
        self.parent.after(1000, refresh_ui)

    def refresh_profile_view(self):
        """Actualiza la vista del perfil"""
        # Limpiar widgets actuales
        for widget in self.parent.winfo_children():
            widget.destroy()
            
        # Recargar cuenta actual
        self.current_account = self.auth_manager.get_current_account()
        
        # Recrear la vista
        self.create_profile_view()

    def get_root(self, widget):
        """Obtiene la ventana raíz desde cualquier widget"""
        parent = widget.master
        while parent.master:
            parent = parent.master
        return parent

    def create_profile_view(self):
        # Título
        title_frame = tk.Frame(self.parent, bg="#1E1E1E")
        title_frame.pack(fill=tk.X, pady=20)
        
        if self.current_account:
            # Mostrar información del usuario logueado
            self.create_logged_in_view(title_frame)
        else:
            # Mostrar vista de login
            title = tk.Label(title_frame, text="Account Manager", 
                           font=("Segoe UI", 24, "bold"), 
                           bg="#1E1E1E", fg="white")
            title.pack()
            
            # Contenedor principal
            self.main_container = tk.Frame(self.parent, bg="#1E1E1E")
            self.main_container.pack(fill=tk.BOTH, expand=True, padx=50)
            
            # Crear pestañas
            self.create_tabs()

    def create_logged_in_view(self, parent):
        # Contenedor principal para usuario logueado
        container = tk.Frame(self.parent, bg="#1E1E1E")
        container.pack(fill=tk.BOTH, expand=True, padx=50)

        # Información del usuario
        user_frame = tk.Frame(container, bg="#1E1E1E")
        user_frame.pack(pady=30)

        # Icono de usuario (emoji por ahora, podrías usar una imagen)
        tk.Label(user_frame, text="👤", font=("Segoe UI", 48), 
                bg="#1E1E1E", fg="white").pack()

        # Nombre de usuario
        tk.Label(user_frame, text=self.current_account["username"],
                font=("Segoe UI", 24, "bold"), 
                bg="#1E1E1E", fg="white").pack(pady=10)

        # Tipo de cuenta
        account_type = "Premium ✨" if self.current_account["type"] == "premium" else "Offline ⚡"
        tk.Label(user_frame, text=account_type,
                font=("Segoe UI", 14), 
                bg="#1E1E1E", fg="#4CAF50").pack()

        if "email" in self.current_account:
            tk.Label(user_frame, text=self.current_account["email"],
                    font=("Segoe UI", 12), 
                    bg="#1E1E1E", fg="#AAAAAA").pack(pady=5)

        # UUID
        tk.Label(user_frame, text=f"UUID: {self.current_account['uuid']}",
                font=("Segoe UI", 10), 
                bg="#1E1E1E", fg="#888888").pack(pady=5)

        # Botón de cerrar sesión
        self.create_modern_button(container, "Logout", self.logout)

    def logout(self):
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres cerrar sesión?"):
            if self.auth_manager.logout():
                # Actualizar callback primero
                if self.update_callback:
                    self.update_callback(None)
                
                # Limpiar la vista actual
                self.current_account = None
                self.refresh_profile_view()
                
                # Mostrar mensaje de éxito
                messagebox.showinfo("Éxito", "Se ha cerrado la sesión correctamente")
                
                # Redireccionar a la pantalla principal
                if hasattr(self.root, 'show_home_window'):
                    self.root.after(100, self.root.show_home_window)
            else:
                messagebox.showerror("Error", "Error al cerrar sesión")

    def create_tabs(self):
        # Contenedor para los botones de navegación
        buttons_frame = tk.Frame(self.main_container, bg="#1E1E1E")
        buttons_frame.pack(fill=tk.X, pady=(0,20))

        # Contenedor para el contenido
        self.content_frame = tk.Frame(self.main_container, bg="#1E1E1E")
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Crear los frames de contenido
        self.premium_content = tk.Frame(self.content_frame, bg="#1E1E1E")
        self.offline_content = tk.Frame(self.content_frame, bg="#1E1E1E")

        # Variable para controlar qué pestaña está activa
        self.active_tab = tk.StringVar(value="premium")

        # Función para cambiar entre pestañas
        def switch_tab(tab_name):
            self.active_tab.set(tab_name)
            if tab_name == "premium":
                self.premium_content.pack(fill=tk.BOTH, expand=True)
                self.offline_content.pack_forget()
                premium_canvas.itemconfig(premium_bg, fill="#4CAF50")
                offline_canvas.itemconfig(offline_bg, fill="#252525")
            else:
                self.offline_content.pack(fill=tk.BOTH, expand=True)
                self.premium_content.pack_forget()
                premium_canvas.itemconfig(premium_bg, fill="#252525")
                offline_canvas.itemconfig(offline_bg, fill="#4CAF50")

        # Botón Premium
        premium_canvas = tk.Canvas(buttons_frame, width=200, height=40, bg="#1E1E1E", highlightthickness=0)
        premium_canvas.pack(side=tk.LEFT, padx=10)

        premium_bg = premium_canvas.create_rounded_rectangle(0, 0, 200, 40, radius=20, fill="#4CAF50")
        premium_text = premium_canvas.create_text(100, 20, text="PREMIUM MINECRAFT ✨", 
                                               fill="white", font=("Segoe UI", 10, "bold"))

        # Botón Offline
        offline_canvas = tk.Canvas(buttons_frame, width=200, height=40, bg="#1E1E1E", highlightthickness=0)
        offline_canvas.pack(side=tk.LEFT, padx=10)

        offline_bg = offline_canvas.create_rounded_rectangle(0, 0, 200, 40, radius=20, fill="#252525")
        offline_text = offline_canvas.create_text(100, 20, text="OFFLINE MODE ⚡", 
                                               fill="white", font=("Segoe UI", 10, "bold"))

        # Efectos hover para Premium
        def on_premium_enter(e):
            if self.active_tab.get() != "premium":
                premium_canvas.itemconfig(premium_bg, fill="#3d8c40")

        def on_premium_leave(e):
            if self.active_tab.get() != "premium":
                premium_canvas.itemconfig(premium_bg, fill="#252525")

        # Efectos hover para Offline
        def on_offline_enter(e):
            if self.active_tab.get() != "offline":
                offline_canvas.itemconfig(offline_bg, fill="#3d8c40")

        def on_offline_leave(e):
            if self.active_tab.get() != "offline":
                offline_canvas.itemconfig(offline_bg, fill="#252525")

        # Bind eventos
        for item in [premium_bg, premium_text]:
            premium_canvas.tag_bind(item, "<Enter>", on_premium_enter)
            premium_canvas.tag_bind(item, "<Leave>", on_premium_leave)
            premium_canvas.tag_bind(item, "<Button-1>", lambda e: switch_tab("premium"))

        for item in [offline_bg, offline_text]:
            offline_canvas.tag_bind(item, "<Enter>", on_offline_enter)
            offline_canvas.tag_bind(item, "<Leave>", on_offline_leave)
            offline_canvas.tag_bind(item, "<Button-1>", lambda e: switch_tab("offline"))

        # Crear el contenido de las pestañas
        self.create_premium_tab(self.premium_content)
        self.create_offline_tab(self.offline_content)

        # Mostrar la pestaña premium por defecto
        switch_tab("premium")

    def create_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
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
        return canvas.create_polygon(points, smooth=True, **kwargs)

    tk.Canvas.create_rounded_rectangle = lambda self, *args, **kwargs: ProfileWindow.create_rounded_rectangle(None, self, *args, **kwargs)

    def create_premium_tab(self, parent):
        login_frame = tk.Frame(parent, bg="#1E1E1E")
        login_frame.pack(pady=(10,30))

        # Status premium
        status_frame = tk.Frame(login_frame, bg="#1E1E1E")
        status_frame.pack(fill="x", pady=(0,20))
        
        tk.Label(status_frame, text="✨ Original Minecraft Account", 
                font=("Segoe UI", 10), bg="#1E1E1E", 
                fg="#55FFFF").pack(side="left", padx=5)
        
        # Título
        tk.Label(login_frame, text="Login with Minecraft Account", 
                font=("Segoe UI", 16, "bold"), bg="#1E1E1E", fg="white").pack(pady=20)

        # Campos de entrada
        self.premium_email = self.create_modern_entry(login_frame, "Email/Username")
        self.premium_password = self.create_modern_entry(login_frame, "Password", show="*")

        # Botón de login
        self.create_modern_button(login_frame, "Login with Microsoft", self.login_premium)
        
        # Información adicional
        info_text = "Use your Microsoft account to login to Minecraft.\nThis allows you to play online on official servers."
        tk.Label(login_frame, text=info_text, bg="#1E1E1E", fg="#AAAAAA",
                font=("Segoe UI", 9), justify=tk.LEFT).pack(pady=20)

    def create_offline_tab(self, parent):
        offline_frame = tk.Frame(parent, bg="#1E1E1E")
        offline_frame.pack(pady=(10,30))

        # Status offline
        status_frame = tk.Frame(offline_frame, bg="#1E1E1E")
        status_frame.pack(fill="x", pady=(0,20))
        
        tk.Label(status_frame, text="⚠️ Limited Features Account", 
                font=("Segoe UI", 10), bg="#1E1E1E", 
                fg="#FFAA00").pack(side="left", padx=5)
        
        # Título
        tk.Label(offline_frame, text="Create Offline Account", 
                font=("Segoe UI", 16, "bold"), bg="#1E1E1E", fg="white").pack(pady=20)

        # Campo de nombre de usuario
        self.offline_username = self.create_modern_entry(offline_frame, "Username")

        # Botón para crear cuenta
        self.create_modern_button(offline_frame, "Create Account", self.create_offline_account)

        # Información adicional
        info_text = "Create an offline account to play in single player mode.\nThis account won't work on official online servers."
        tk.Label(offline_frame, text=info_text, bg="#1E1E1E", fg="#AAAAAA",
                font=("Segoe UI", 9), justify=tk.LEFT).pack(pady=20)

    def create_modern_button(self, parent, text, command):
        button_frame = tk.Frame(parent, bg="#1E1E1E")
        button_frame.pack(pady=10)
        
        canvas = tk.Canvas(button_frame, width=200, height=40, 
                         bg="#1E1E1E", highlightthickness=0)
        canvas.pack()

        # Crear rectángulo redondeado
        button_bg = canvas.create_rectangle(0, 0, 200, 40, 
                                         fill="#4CAF50", outline="",
                                         width=0)
        button_text = canvas.create_text(100, 20, text=text, 
                                       fill="white", 
                                       font=("Segoe UI", 10, "bold"))

        def on_enter(e):
            canvas.itemconfig(button_bg, fill="#3d8c40")

        def on_leave(e):
            canvas.itemconfig(button_bg, fill="#4CAF50")

        def on_click(e):
            command()

        # Vinculamos los eventos tanto al canvas como al texto
        for item in [canvas, button_text]:
            canvas.tag_bind(button_text, "<Enter>", on_enter)
            canvas.tag_bind(button_text, "<Leave>", on_leave)
            canvas.tag_bind(button_text, "<Button-1>", on_click)
        
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)

    def create_modern_entry(self, parent, placeholder, show=None):
        entry_frame = tk.Frame(parent, bg="#1E1E1E")
        entry_frame.pack(pady=5)
        
        # Label encima del entry
        tk.Label(entry_frame, text=placeholder, 
                bg="#1E1E1E", fg="#AAAAAA",
                font=("Segoe UI", 9)).pack(anchor="w")
        
        entry = tk.Entry(entry_frame, 
                        font=("Segoe UI", 10),
                        bg="#2A2A2A",
                        fg="white",
                        insertbackground="white",
                        show=show,
                        width=25)
        entry.pack(pady=(5,0))
        
        return entry

    def login_premium(self):
        email = self.premium_email.get()
        password = self.premium_password.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Por favor completa todos los campos")
            return

        result = self.auth_manager.authenticate_premium(email, password)
        if result:
            # Primero actualizamos el widget de usuario
            if self.update_callback:
                self.update_callback(result["username"])
            # Mostramos mensaje
            messagebox.showinfo("Éxito", "Inicio de sesión exitoso")
            # Redirigimos a la pantalla principal
            if hasattr(self.root, 'show_home_window'):
                self.root.after(100, self.root.show_home_window)
        else:
            messagebox.showerror("Error", "Error al iniciar sesión")

    def create_offline_account(self):
        username = self.offline_username.get()
        
        if not username:
            messagebox.showerror("Error", "Por favor ingresa un nombre de usuario")
            return
            
        if len(username) < 3 or len(username) > 16:
            messagebox.showerror("Error", "El nombre de usuario debe tener entre 3 y 16 caracteres")
            return

        # Validar que solo contenga caracteres permitidos
        if not all(c.isalnum() or c == '_' for c in username):
            messagebox.showerror("Error", "El nombre solo puede contener letras, números y guiones bajos")
            return

        # Generar UUID offline usando el mismo método que Minecraft
        import uuid
        player_uuid = uuid.uuid3(uuid.NAMESPACE_OID, f"OfflinePlayer:{username}")
        
        # Intentar autenticar y guardar la cuenta offline
        result = self.auth_manager.authenticate_offline(username, str(player_uuid))
        if result:
            if self.update_callback:
                self.update_callback(username)
            self.refresh_profile_view()
            messagebox.showinfo("Éxito", f"Cuenta offline '{username}' creada exitosamente")
            if hasattr(self.root, 'show_home_window'):
                self.root.after(100, self.root.show_home_window)
        else:
            messagebox.showerror("Error", "Error al crear la cuenta offline")

    def create_account(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showwarning("Error", "Por favor completa todos los campos")
            return
            
        try:
            result = minecraft_launcher_lib.microsoft_account.complete_login(email, password)
            if result and 'access_token' in result:
                # Guardar la cuenta
                self.auth_manager.save_account(result)
                # Actualizar el widget de usuario
                if self.update_user_widget:
                    self.update_user_widget(result.get('username', 'Unknown'))
                messagebox.showinfo("Éxito", "Cuenta creada exitosamente")
                # Redirigir a la pantalla principal
                if hasattr(self.master, 'master') and hasattr(self.master.master, 'show_home_window'):
                    self.master.master.show_home_window()
            else:
                messagebox.showerror("Error", "No se pudo crear la cuenta")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear cuenta: {str(e)}")
