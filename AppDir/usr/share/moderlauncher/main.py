"""
ModerLauncher - Punto de entrada principal
Ejecuta la ventana principal del archivo 1.py
"""

import os
import runpy

# Importar y ejecutar el código principal del 1.py
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    runpy.run_path(os.path.join(script_dir, '1.py'), run_name='__main__')