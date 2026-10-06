"""
Submenú del Relleno Sanitario (DORS).

Paso 1: cálculo poblacional. Paso 2: residuos, volumen, área y celda
diaria de operación (requiere el Paso 1 guardado).
"""

import tkinter as tk
from tkinter import messagebox

from estado_proyecto import EstadoProyecto
from ui_utils import ajustar_geometria
from ventana_relleno_sanitario import VentanaRellenoSanitario, COLORES, FUENTES
from ventana_relleno_diseno import VentanaDisenoRelleno


PASO_POBLACION = "1. Cálculo poblacional"
PASO_DISENO = "2. Residuos, volumen, área y celda diaria"


class ProcesosRelleno(tk.Toplevel):
    """Ventana con los pasos de diseño del relleno sanitario."""

    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Relleno Sanitario — Pasos de diseño")
        self.resizable(False, True)
        ajustar_geometria(self, ancho=440, alto=250, alto_minimo=230)
        self.configure(bg=COLORES["fondo"])
        self.al_guardar = al_guardar

        tk.Label(
            self, text="Relleno Sanitario — Pasos de diseño", font=FUENTES["titulo"],
            bg=COLORES["encabezado"], fg=COLORES["encabezado_texto"], pady=12,
        ).pack(fill="x")

        contenedor = tk.Frame(self, bg=COLORES["fondo"])
        contenedor.pack(fill="both", expand=True, padx=20, pady=15)

        self.botones = {}
        for paso, comando in [(PASO_POBLACION, self.abrir_poblacion),
                              (PASO_DISENO, self.abrir_diseno)]:
            btn = tk.Button(
                contenedor, text=paso, font=("Arial", 11), bg="white", fg=COLORES["texto"],
                anchor="w", relief="groove", bd=1, cursor="hand2", command=comando,
            )
            btn.pack(fill="x", pady=4, ipady=8)
            self.botones[paso] = btn

        self._actualizar_estado_botones()

    def _actualizar_estado_botones(self):
        """Marca con ✔ los pasos ya guardados."""
        for paso, hecho in [(PASO_POBLACION, EstadoProyecto.relleno_definido()),
                            (PASO_DISENO, EstadoProyecto.relleno_diseno_definido())]:
            if hecho:
                self.botones[paso].config(text=f"✔ {paso}", bg=COLORES["ok_fondo"],
                                          fg=COLORES["ok_texto"])
            else:
                self.botones[paso].config(text=paso, bg="white", fg=COLORES["texto"])
        if self.al_guardar:
            self.al_guardar()

    def abrir_poblacion(self):
        ventana = VentanaRellenoSanitario(self, al_guardar=self._actualizar_estado_botones)
        ventana.grab_set()

    def abrir_diseno(self):
        if not EstadoProyecto.relleno_definido():
            messagebox.showwarning(
                "Falta el cálculo poblacional",
                "Primero calcule y guarde el Paso 1 (cálculo poblacional).", parent=self,
            )
            return
        ventana = VentanaDisenoRelleno(self, al_guardar=self._actualizar_estado_botones)
        ventana.grab_set()
