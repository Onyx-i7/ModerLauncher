import tkinter as tk
from tkinter import ttk, filedialog
import json
import os
import psutil
import ctypes
from tkinter import messagebox
import webbrowser
import subprocess
import threading
import time

class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        # Configurar el tamaño mínimo del frame padre
        self.parent.configure(width=800, height=600)
        self.parent.pack_propagate(False)  # Evitar que el frame se encoja
        
        self.system_ram = self.get_system_ram()
        self.cpu_cores = psutil.cpu_count()  # Obtener número de núcleos
        self.load_settings()
        self.setup_styles()
        
        # Inicializar java_versions antes de create_widgets
        self.java_versions = {
            "Java 17 (Minecraft 1.17 - 1.20.4)": {
                "versions": ["1.17", "1.18", "1.19", "1.20"],
                "path": "",
                "min_version": "1.17",
                "download": "https://adoptium.net/temurin/releases/?version=17"
            },
            "Java 8 (Minecraft 1.1 - 1.16.5)": {  # Cambiado para incluir 1.1
                "versions": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12", "1.13", "1.14", "1.15", "1.16"],
                "path": "",
                "min_version": "1.1",
                "download": "https://adoptium.net/temurin/releases/?version=8"
            }
        }
        
        # Detectar instalaciones de Java antes de crear widgets
        self.detect_java_installations()
        
        # Crear widgets después de tener todo inicializado
        self.create_widgets()
    
    def get_system_ram(self):
        """Obtiene la RAM total del sistema en MB"""
        try:
            return int(psutil.virtual_memory().total / (1024 * 1024))
        except:
            return 4096  # Valor por defecto si no se puede detectar
    
    def setup_styles(self):
        """Configura los estilos personalizados"""
        style = ttk.Style()
        
        # Estilos generales
        style.configure("Title.TLabel", 
                      font=("Segoe UI", 24, "bold"), 
                      foreground="white", 
                      background="#1E1E1E")
        
        # Estilo para escalas
        style.configure("Custom.Horizontal.TScale",
                      background="#252525",
                      troughcolor="#1E1E1E",
                      slidercolor="#4CAF50",
                      bordercolor="#333333")
        
        # Estilo para radio buttons
        style.configure("Custom.TRadiobutton",
                      background="#252525",
                      foreground="white",
                      selectcolor="#4CAF50")
        
        # Estilo para Combobox
        style.configure("Custom.TCombobox",
                      selectbackground="#4CAF50",
                      selectforeground="white",
                      fieldbackground="#1E1E1E",
                      background="#252525",
                      foreground="white",
                      arrowcolor="white")
        
        style.map("Custom.TCombobox",
                 fieldbackground=[("readonly", "#1E1E1E")],
                 selectbackground=[("readonly", "#4CAF50")],
                 background=[("readonly", "#252525")])

        # Añadir estilo para Entry
        style.configure("Custom.TEntry",
                      fieldbackground="#1E1E1E",
                      foreground="white",
                      insertcolor="white",
                      bordercolor="#333333",
                      lightcolor="#333333",
                      darkcolor="#333333")

    def create_section(self, parent, title, description=None):
        section = tk.Frame(parent, bg="#252525")
        section.configure(width=350, height=150)  # Tamaño fijo para cada sección
        section.pack_propagate(False)  # Mantener el tamaño
        
        # Título con icono
        header_frame = tk.Frame(section, bg="#252525")
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        title_label = tk.Label(header_frame, text=title, 
                             font=("Segoe UI", 12, "bold"),
                             bg="#252525", fg="white")
        title_label.pack(side=tk.LEFT)
        
        if description:
            desc_label = tk.Label(section, text=description,
                                font=("Segoe UI", 9),
                                bg="#252525", fg="#888888",
                                wraplength=300)
            desc_label.pack(fill=tk.X, pady=(0, 10))
        
        content_frame = tk.Frame(section, bg="#252525")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        return section
    
    def load_settings(self):
        """Carga o crea las configuraciones por defecto"""
        default_settings = {
            'ram': 2048,
            'java_path': '',
            'jvm_args': '-XX:+UseG1GC -XX:+ParallelRefProcEnabled',
            'language': 'es',
            'install_path': os.path.expanduser('~/.minecraft'),
            'compatibility_mode': False,
            'display_mode': 'window',
            'cpu_cores': psutil.cpu_count(),
            'process_priority': 'normal',
            'selected_java': '',
        }
        
        try:
            with open('settings.json', 'r') as f:
                self.settings = {**default_settings, **json.load(f)}
        except:
            self.settings = default_settings
    
    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)
            tk.messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            
    def create_widgets(self):
        # Asegurarse de que el parent tenga un fondo oscuro
        self.parent.configure(bg="#1E1E1E")
        
        # Canvas y contenedor principal
        main_container = tk.Frame(self.parent, bg="#1E1E1E")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Canvas sin scrollbar
        canvas = tk.Canvas(main_container, bg="#1E1E1E", highlightthickness=0)
        canvas.configure(width=760)
        canvas.pack(fill="both", expand=True)
        
        # Frame principal sin scroll
        main_frame = tk.Frame(canvas, bg="#1E1E1E")
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Grid container con tamaño fijo
        grid_container = tk.Frame(main_frame, bg="#1E1E1E")
        grid_container.pack(fill=tk.BOTH, expand=True)
        
        # Configurar el grid
        for i in range(3):
            grid_container.grid_rowconfigure(i, weight=1, minsize=150)  # Altura mínima
        for j in range(2):
            grid_container.grid_columnconfigure(j, weight=1, minsize=350)  # Ancho mínimo
            
        # Crear las secciones con tamaños específicos
        self.create_ram_section(grid_container).grid(row=0, column=0, sticky="nsew", padx=10, pady=10, ipadx=10, ipady=10)
        self.create_java_section(grid_container).grid(row=0, column=1, sticky="nsew", padx=10, pady=10, ipadx=10, ipady=10)
        self.create_display_mode_section(grid_container).grid(row=1, column=0, sticky="nsew", padx=10, pady=10, ipadx=10, ipady=10)
        self.create_cpu_cores_section(grid_container).grid(row=1, column=1, sticky="nsew", padx=10, pady=10, ipadx=10, ipady=10)
        self.create_language_section(grid_container).grid(row=2, column=0, sticky="nsew", padx=10, pady=10, ipadx=10, ipady=10)
        self.create_priority_section(grid_container).grid(row=2, column=1, sticky="nsew", padx=10, pady=10, ipadx=10, ipady=10)

        # === Botón Guardar ===
        save_frame = tk.Frame(main_frame, bg="#1E1E1E")
        save_frame.pack(fill=tk.X, pady=30)
        
        save_btn = tk.Button(
            save_frame,
            text="💾 Guardar Cambios",
            font=("Segoe UI", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.save_all,
            cursor="hand2"
        )
        save_btn.pack()

        # Configurar eventos
        save_btn.bind("<Enter>", lambda e: save_btn.configure(bg="#3d8c40"))
        save_btn.bind("<Leave>", lambda e: save_btn.configure(bg="#4CAF50"))

    def create_ram_section(self, parent):
        section = self.create_section(parent, "🔧 Memoria RAM",
                                    f"RAM detectada: {self.system_ram}MB\nAjusta la cantidad de memoria que Minecraft podrá utilizar. Se recomienda asignar al menos 2GB (2048MB) para un mejor rendimiento.")
        
        ram_control = tk.Frame(section, bg="#252525")
        ram_control.pack(fill=tk.X, padx=10)
        
        # Etiqueta de valor mínimo
        tk.Label(ram_control, text="1GB", bg="#252525", fg="#888888").pack(side=tk.LEFT)
        
        self.ram_scale = ttk.Scale(
            ram_control, 
            from_=1024,
            to=min(self.system_ram, 16384),
            value=self.settings['ram'],
            orient=tk.HORIZONTAL,
            style="Custom.Horizontal.TScale",
            command=self.update_ram_label  # Añadir callback
        )
        self.ram_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Etiqueta de valor máximo
        tk.Label(ram_control, text=f"{min(self.system_ram, 16384)//1024}GB", 
                bg="#252525", fg="#888888").pack(side=tk.LEFT)
        
        self.ram_label = tk.Label(ram_control, 
                                text=f"{self.settings['ram']}MB",
                                bg="#252525", fg="#4CAF50",
                                font=("Segoe UI", 10, "bold"))
        self.ram_label.pack(side=tk.LEFT, padx=10)
        
        # Texto informativo adicional
        tk.Label(section,
                text="Nota: No asignes más del 70% de tu RAM total para evitar problemas de rendimiento.",
                bg="#252525", fg="#888888",
                font=("Segoe UI", 8),
                wraplength=300).pack(pady=(10,0), padx=10)
        
        return section

    def create_java_section(self, parent):
        section = self.create_section(parent, "☕ Java",
                                    "Selecciona la versión de Java para Minecraft")
        
        # Frame para el selector de Java
        java_select = tk.Frame(section, bg="#252525")
        java_select.pack(fill=tk.X, padx=10, pady=5)
        
        # Label para versión de Java
        tk.Label(java_select, text="VERSIÓN", font=("Segoe UI", 8, "bold"),
                bg="#252525", fg="#888888").pack(anchor="w")
        
        # Frame para controles de Java
        java_controls = tk.Frame(java_select, bg="#252525")
        java_controls.pack(fill=tk.X, pady=5)
        
        # Combobox mejorado para Java
        java_versions_list = list(self.java_versions.keys())
        
        self.java_combo = ttk.Combobox(
            java_controls,
            values=java_versions_list,
            state="readonly",
            width=40,
            style="Custom.TCombobox"
        )
        self.java_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # Seleccionar el primer elemento si hay versiones disponibles
        if java_versions_list:
            self.java_combo.set(java_versions_list[0])
        
        # Botón de descarga
        download_btn = ttk.Button(
            java_controls,
            text="Descargar Java",
            command=self.download_java,
            style="Accent.TButton"
        )
        download_btn.pack(side=tk.LEFT)

        # Info de versiones
        info_text = """
Versiones de Java recomendadas:
• Minecraft 1.17 - 1.20.4 → Java 17
• Minecraft 1.12 - 1.16.5 → Java 8
• Minecraft 1.5 - 1.11.2 → Java 8
• Minecraft 1.2.5 - 1.4.7 → Java 7
• Minecraft Beta y Alpha → Java 6 o 7"""
        
        info_label = tk.Label(section,
                            text=info_text,
                            justify=tk.LEFT,
                            bg="#252525",
                            fg="#888888",
                            font=("Segoe UI", 9))
        info_label.pack(anchor="w", padx=10, pady=10)

        # Añadir sección de argumentos JVM
        jvm_frame = tk.Frame(section, bg="#252525")
        jvm_frame.pack(fill=tk.X, padx=10, pady=(10,5))
        
        tk.Label(jvm_frame, text="Argumentos JVM:", 
                bg="#252525", fg="#888888",
                font=("Segoe UI", 8, "bold")).pack(anchor="w")
        
        self.jvm_entry = ttk.Entry(jvm_frame, 
                                 style="Custom.TEntry",
                                 width=40)
        self.jvm_entry.pack(fill=tk.X, pady=2)
        self.jvm_entry.insert(0, self.settings.get('jvm_args', '-XX:+UseG1GC -XX:+ParallelRefProcEnabled'))
        
        # Texto de ayuda para JVM args
        tk.Label(jvm_frame,
                text="Argumentos avanzados para optimizar el rendimiento de Java",
                bg="#252525", fg="#666666",
                font=("Segoe UI", 7)).pack(anchor="w")

        return section

    def create_language_section(self, parent):
        section = self.create_section(parent, "🌍 Idioma",
                                    "Selecciona el idioma del launcher")
        
        self.lang_combo = ttk.Combobox(
            section,
            values=['Español', 'English'],
            state='readonly',
            width=20,
            style="Custom.TCombobox"
        )
        self.lang_combo.set('Español' if self.settings['language'] == 'es' else 'English')
        self.lang_combo.pack(padx=10, pady=5)
        return section

    def create_display_mode_section(self, parent):
        section = self.create_section(parent, "📺 Modo de Pantalla",
                                    "Configura cómo se mostrará el juego en tu pantalla")
        
        self.display_var = tk.StringVar(value=self.settings.get('display_mode', 'window'))
        modes = [
            ("Ventana", "window", "Modo tradicional con bordes de ventana"),
            ("Pantalla Completa", "fullscreen", "Aprovecha toda la pantalla"),
            ("Sin Bordes", "borderless", "Como pantalla completa pero más rápido al cambiar")
        ]
        
        for text, value, desc in modes:
            mode_frame = tk.Frame(section, bg="#252525")
            mode_frame.pack(fill=tk.X, padx=10, pady=2)
            
            rb = ttk.Radiobutton(mode_frame, text=text, value=value, 
                               variable=self.display_var,
                               style="Custom.TRadiobutton")
            rb.pack(side=tk.LEFT)
            
            tk.Label(mode_frame, text=desc,
                    bg="#252525", fg="#888888",
                    font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=5)
        
        return section

    def create_cpu_cores_section(self, parent):
        section = self.create_section(parent, "⚙️ Núcleos CPU",
                                    f"Núcleos detectados: {self.cpu_cores}\nConfigura cuántos núcleos del procesador podrá utilizar Minecraft.")
        
        cores_control = tk.Frame(section, bg="#252525")
        cores_control.pack(fill=tk.X, padx=10)
        
        tk.Label(cores_control, text="1", bg="#252525", fg="#888888").pack(side=tk.LEFT)
        
        self.cores_scale = ttk.Scale(
            cores_control, 
            from_=1,
            to=self.cpu_cores,
            value=self.settings.get('cpu_cores', self.cpu_cores),
            orient=tk.HORIZONTAL,
            style="Custom.Horizontal.TScale",
            command=self.update_cores_label  # Añadir callback
        )
        self.cores_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Label(cores_control, text=str(self.cpu_cores), 
                bg="#252525", fg="#888888").pack(side=tk.LEFT)
        
        self.cores_label = tk.Label(cores_control, 
                                  text=f"{int(self.cores_scale.get())} núcleos",
                                  bg="#252525", fg="#4CAF50",
                                  font=("Segoe UI", 10, "bold"))
        self.cores_label.pack(side=tk.LEFT, padx=10)
        
        # Texto informativo
        tk.Label(section,
                text="Recomendación: Deja al menos 1-2 núcleos libres para el sistema operativo.",
                bg="#252525", fg="#888888",
                font=("Segoe UI", 8),
                wraplength=300).pack(pady=(10,0), padx=10)
        
        return section

    def create_priority_section(self, parent):
        section = self.create_section(parent, "🏗 Prioridad del Proceso",
                                    "Establece la prioridad de ejecución")
        
        self.priority_var = tk.StringVar(value=self.settings.get('process_priority', 'normal'))
        priorities = [
            ("Baja", "low"),
            ("Normal", "normal"),
            ("Alta", "high"),
            ("Tiempo Real", "realtime")
        ]
        
        for text, value in priorities:
            rb = ttk.Radiobutton(section, text=text, value=value, variable=self.priority_var)
            rb.pack(anchor=tk.W, padx=10, pady=2)
        return section

    def update_ram_label(self, event=None):
        """Actualiza la etiqueta de RAM en tiempo real"""
        try:
            value = int(float(self.ram_scale.get()))
            gb_value = value / 1024
            self.ram_label.config(text=f"{value}MB ({gb_value:.1f}GB)")
        except:
            pass

    def update_cores_label(self, event=None):
        """Actualiza la etiqueta de núcleos en tiempo real"""
        try:
            value = int(float(self.cores_scale.get()))
            percent = (value / self.cpu_cores) * 100
            self.cores_label.config(text=f"{value} núcleos ({percent:.0f}%)")
        except:
            pass
        
    def browse_java(self, entry):
        path = filedialog.askopenfilename(
            title="Seleccionar Java Executable",
            filetypes=[("Java Executable", "java.exe"), ("All files", "*.*")]
        )
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
            
    def browse_path(self):
        path = filedialog.askdirectory(
            title="Seleccionar Carpeta de Instalación"
        )
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            
    def create_save_message(self):
        """Crea una ventana de mensaje emergente para el guardado"""
        msg_window = tk.Toplevel()
        msg_window.transient(self.parent)
        msg_window.overrideredirect(True)
        msg_window.configure(bg="#161616")
        
        # Centrar la ventana
        width = 300
        height = 80
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - width) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - height) // 2
        msg_window.geometry(f"{width}x{height}+{x}+{y}")
        
        frame = tk.Frame(msg_window, bg="#161616", highlightbackground="#333333", highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        label = tk.Label(frame, text="⚙️ Guardando...", font=("Segoe UI", 12, "bold"),
                        bg="#161616", fg="#4CAF50")
        label.pack(pady=20)
        
        return msg_window, label

    def save_all(self):
        """Guardar configuración de forma simplificada"""
        try:
            # Verificar Java
            selected_java = self.java_combo.get()
            if not selected_java:
                messagebox.showwarning("Advertencia", "Por favor selecciona una versión de Java")
                return
            
            java_path = self.java_versions[selected_java]["path"]
            if not java_path or not os.path.exists(java_path):
                from java_error_window import JavaErrorWindow
                JavaErrorWindow(self.parent, selected_java.split("(")[1].split(")")[0], 
                              selected_java.split()[1])
                return

            # Crear ventana de mensaje
            msg_window, msg_label = self.create_save_message()
            self.parent.update_idletasks()

            # Preparar configuración
            settings = {
                'ram': int(float(self.ram_scale.get())),
                'java_path': java_path,
                'jvm_args': self.jvm_entry.get(),
                'language': 'es' if self.lang_combo.get() == 'Español' else 'en',
                'selected_java': selected_java,
                'display_mode': self.display_var.get(),
                'cpu_cores': int(float(self.cores_scale.get())),
                'process_priority': self.priority_var.get()
            }

            def save():
                try:
                    # Guardar configuración
                    with open('settings.json', 'w') as f:
                        json.dump(settings, f, indent=4)
                    
                    # Actualizar settings en memoria
                    self.settings.update(settings)
                    
                    # Actualizar mensaje y cerrar
                    msg_label.config(text="✔️ ¡Guardado completado!")
                    self.parent.after(800, msg_window.destroy)
                    
                except Exception as e:
                    msg_window.destroy()
                    messagebox.showerror("Error", f"Error al guardar: {str(e)}")

            # Ejecutar guardado después de mostrar el mensaje
            self.parent.after(100, save)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la configuración: {str(e)}")

    def show_error(self, window, message):
        """Muestra un error y cierra la ventana de mensaje"""
        window.destroy()
        messagebox.showwarning("Advertencia", message)

    def show_java_error(self, window, selected_java):
        """Muestra el error de Java y abre la ventana de error"""
        window.destroy()
        from java_error_window import JavaErrorWindow
        error_window = JavaErrorWindow(
            self.parent,
            selected_java.split("(")[1].split(")")[0],
            selected_java.split()[1]
        )

    def apply_process_priority(self):
        """Aplica la prioridad del proceso a Minecraft si está en ejecución"""
        priority_map = {
            'low': psutil.IDLE_PRIORITY_CLASS,
            'normal': psutil.NORMAL_PRIORITY_CLASS,
            'high': psutil.HIGH_PRIORITY_CLASS,
            'realtime': psutil.REALTIME_PRIORITY_CLASS
        }
        
        try:
            # Buscar proceso de Minecraft
            for proc in psutil.process_iter(['name']):
                if 'javaw.exe' in proc.info['name'].lower():
                    proc.nice(priority_map[self.priority_var.get()])
        except:
            pass  # Silenciosamente ignorar errores si el proceso no existe
        
    def detect_java_installations(self):
        """Detecta las instalaciones de Java en el sistema"""
        java_search_paths = [
            "C:/Program Files/Java",
            "C:/Program Files (x86)/Java",
            "C:/Program Files/Eclipse Adoptium",
            "C:/Program Files/Eclipse Foundation",
            "C:/Program Files/BellSoft",
            "C:/Program Files/Zulu",
            os.path.expanduser("~/AppData/Local/Programs/Eclipse Adoptium"),
            os.path.expanduser("~/AppData/Local/Programs/Eclipse Foundation")
        ]
        
        # Limpiar paths anteriores
        for version in self.java_versions:
            self.java_versions[version]["path"] = ""

        for search_path in java_search_paths:
            if os.path.exists(search_path):
                for java_dir in os.listdir(search_path):
                    java_path = os.path.join(search_path, java_dir, "bin", "java.exe")
                    if os.path.exists(java_path):
                        version_info = self.get_java_version(java_path)
                        if version_info:
                            for java_ver, data in self.java_versions.items():
                                if version_info in java_ver and not data["path"]:
                                    data["path"] = java_path
                                    print(f"Java {version_info} encontrado en: {java_path}")
                                    break

    def get_java_version(self, java_path):
        """Obtiene la versión de Java de una instalación"""
        try:
            result = subprocess.run(
                [java_path, "-version"], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            version_output = result.stderr
            if "version" in version_output:
                if "17" in version_output:
                    return "17"
                elif "1.8" in version_output or "8" in version_output:
                    return "8"
                elif "1.7" in version_output or "7" in version_output:
                    return "7"
                elif "1.6" in version_output or "6" in version_output:
                    return "6"
        except Exception as e:
            print(f"Error obteniendo versión de Java: {e}")
        return None

    def download_java(self):
        """Abre el enlace de descarga para la versión de Java seleccionada"""
        selected = self.java_combo.get()
        if selected in self.java_versions:
            webbrowser.open(self.java_versions[selected]["download"])
