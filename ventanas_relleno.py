"""
Submenú del Relleno Sanitario (DORS).

Paso 1: cálculo poblacional. Paso 2: residuos, volumen, área y celda
diaria de operación (requiere el Paso 1 guardado).
"""

import tkinter as tk
from tkinter import messagebox

from estado_proyecto import EstadoProyecto
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria
from ventana_relleno_sanitario import VentanaRellenoSanitario
from ventana_relleno_diseno import VentanaDisenoRelleno


PASO_POBLACION = "1. Cálculo poblacional"
PASO_DISENO = "2. Residuos, volumen, área y celda diaria"


class ProcesosRelleno(tk.Toplevel):
    """Ventana con los pasos de diseño del relleno sanitario."""

    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Relleno Sanitario — Pasos de diseño")
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)
        self.al_guardar = al_guardar

        tema.encabezado(
            self, "Relleno Sanitario — Pasos de diseño",
            "Diseño de Operación de Relleno Sanitario (DORS) · elija el paso que desea calcular",
        )

        cuerpo = tema.area_desplazable(self, bg=C.FONDO, ancho_max=1180, padx=40)

        tk.Label(
            cuerpo, text="Pasos del diseño", font=fuente(18, "bold"),
            bg=C.FONDO, fg=C.TEXTO, anchor="w",
        ).pack(fill="x", pady=(28, 4))
        tk.Label(
            cuerpo,
            text="Los pasos marcados con ✔ ya fueron calculados y guardados. "
                 "El Paso 2 requiere el Paso 1 guardado.",
            font=fuente(10), bg=C.FONDO, fg=C.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x", pady=(0, 14))

        contenedor = tk.Frame(cuerpo, bg=C.FONDO)
        contenedor.pack(fill="x", pady=(0, 30))
        columnas = 2
        for c in range(columnas):
            contenedor.grid_columnconfigure(c, weight=1, uniform="pasos")

        self.botones = {}
        for i, (paso, comando) in enumerate([(PASO_POBLACION, self.abrir_poblacion),
                                             (PASO_DISENO, self.abrir_diseno)]):
            btn = tk.Button(
                contenedor, text=paso, font=fuente(12, "bold"),
                bg=C.SUPERFICIE, fg=C.TEXTO, anchor="w", padx=24, pady=22,
                highlightthickness=1, highlightbackground=C.BORDE,
                cursor="hand2", command=comando,
            )
            btn.grid(row=i // columnas, column=i % columnas, sticky="nsew", padx=6, pady=6)
            self.botones[paso] = btn

        self._actualizar_estado_botones()

    def _actualizar_estado_botones(self):
        """Marca con ✔ los pasos ya guardados."""
        for paso, hecho in [(PASO_POBLACION, EstadoProyecto.relleno_definido()),
                            (PASO_DISENO, EstadoProyecto.relleno_diseno_definido())]:
            if hecho:
                self.botones[paso].config(text=f"✔     {paso}", bg=C.EXITO_FONDO,
                                          fg=C.EXITO, highlightbackground=C.EXITO)
            else:
                self.botones[paso].config(text=paso, bg=C.SUPERFICIE, fg=C.TEXTO,
                                          highlightbackground=C.BORDE)
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
