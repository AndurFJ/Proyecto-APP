"""
Submenú de procesos de PTAP (Planta de Tratamiento de Agua Potable).

Cada botón abrirá, más adelante, la ventana de cálculo específica de
ese proceso. Por ahora son placeholders, salvo los que ya estén
implementados.
"""

import tkinter as tk
from tkinter import messagebox

from estado_proyecto import EstadoProyecto
from ventana_bocatoma_rejilla import VentanaBocatomaRejilla
from ventana_desarenador import VentanaDesarenador
from ventana_aduccion_conduccion import VentanaAduccionConduccion
from ventana_datos_tecnicos import VentanaDatosTecnicos
from ui_utils import ajustar_geometria


PROCESOS_PTAP = [
    "Captación (bocatoma con rejilla)",
    "Desarenador",
    "Aducción / conducción",
    "Mezcla rápida / coagulación",
    "Floculación",
    "Sedimentación",
    "Filtración",
    "Desinfección",
    "Tanque de almacenamiento",
]


class ProcesosPTAP(tk.Toplevel):
    """Ventana con el listado de procesos de diseño de una PTAP."""

    def __init__(self, master):
        super().__init__(master)
        self.title("PTAP — Procesos de diseño")
        self.resizable(False, True)
        ajustar_geometria(self, ancho=420, alto=620, alto_minimo=400)
        self.configure(bg="#F2F4F4")

        self._crear_widgets()
        self._actualizar_estado_botones()

    def _crear_widgets(self):
        titulo = tk.Label(
            self,
            text="PTAP — Procesos de diseño",
            font=("Arial", 14, "bold"),
            bg="#2E86C1",
            fg="white",
            pady=12,
        )
        titulo.pack(fill="x")

        tk.Button(
            self, text="📚 Datos Técnicos de Referencia",
            font=("Arial", 9, "bold"), bg="#5DADE2", fg="white",
            activebackground="#2E86C1", bd=0, cursor="hand2",
            command=self.abrir_datos_tecnicos,
        ).pack(fill="x", padx=20, pady=(10, 0), ipady=4)

        contenedor = tk.Frame(self, bg="#F2F4F4")
        contenedor.pack(fill="both", expand=True, padx=20, pady=15)

        self.botones = {}
        for proceso in PROCESOS_PTAP:
            btn = tk.Button(
                contenedor,
                text=proceso,
                font=("Arial", 11),
                bg="white",
                fg="#1B2631",
                anchor="w",
                relief="groove",
                bd=1,
                cursor="hand2",
                command=lambda p=proceso: self.abrir_proceso(p),
            )
            btn.pack(fill="x", pady=4, ipady=8)
            self.botones[proceso] = btn

    def _actualizar_estado_botones(self):
        """Marca con ✔ los procesos que ya fueron calculados y guardados."""
        btn_bocatoma = self.botones.get("Captación (bocatoma con rejilla)")
        if btn_bocatoma and EstadoProyecto.rejilla_definida():
            btn_bocatoma.config(
                text="✔ Captación (bocatoma con rejilla)",
                bg="#EAFAF1", fg="#1E8449",
            )

        btn_desarenador = self.botones.get("Desarenador")
        if btn_desarenador and EstadoProyecto.desarenador_definido():
            btn_desarenador.config(
                text="✔ Desarenador",
                bg="#EAFAF1", fg="#1E8449",
            )

        btn_aduccion = self.botones.get("Aducción / conducción")
        if btn_aduccion and EstadoProyecto.aduccion_definida():
            btn_aduccion.config(
                text="✔ Aducción / conducción",
                bg="#EAFAF1", fg="#1E8449",
            )

    def abrir_proceso(self, nombre_proceso):
        if nombre_proceso == "Captación (bocatoma con rejilla)":
            self.abrir_bocatoma_rejilla()
            return

        if nombre_proceso == "Desarenador":
            self.abrir_desarenador()
            return

        if nombre_proceso == "Aducción / conducción":
            self.abrir_aduccion_conduccion()
            return

        messagebox.showinfo(
            nombre_proceso,
            f"La ventana de cálculo para '{nombre_proceso}' "
            f"todavía no está implementada.\n\n"
            f"La iremos construyendo paso a paso.",
        )

    def abrir_bocatoma_rejilla(self):
        if not EstadoProyecto.caudal_definido():
            messagebox.showwarning(
                "Falta el caudal de diseño",
                "Primero debe calcular el Caudal de Diseño antes de "
                "diseñar la bocatoma.",
            )
            return

        ventana = VentanaBocatomaRejilla(self, al_guardar=self._actualizar_estado_botones)
        ventana.grab_set()

    def abrir_desarenador(self):
        if not EstadoProyecto.caudal_definido():
            messagebox.showwarning(
                "Falta el caudal de diseño",
                "Primero debe calcular el Caudal de Diseño antes de "
                "diseñar el desarenador.",
            )
            return

        ventana = VentanaDesarenador(self, al_guardar=self._actualizar_estado_botones)
        ventana.grab_set()

    def abrir_aduccion_conduccion(self):
        if not EstadoProyecto.caudal_definido():
            messagebox.showwarning(
                "Falta el caudal de diseño",
                "Primero debe calcular el Caudal de Diseño antes de "
                "diseñar la aducción / conducción.",
            )
            return

        ventana = VentanaAduccionConduccion(self, al_guardar=self._actualizar_estado_botones)
        ventana.grab_set()

    def abrir_datos_tecnicos(self):
        ventana = VentanaDatosTecnicos(self)
        ventana.grab_set()
