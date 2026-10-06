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
import tema
from tema import C, fuente
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
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)

        self._crear_widgets()
        self._actualizar_estado_botones()

    def _crear_widgets(self):
        tema.encabezado(
            self, "PTAP — Procesos de diseño",
            "Planta de Tratamiento de Agua Potable · elija el proceso que desea diseñar",
        )

        cuerpo = tema.area_desplazable(self, bg=C.FONDO, ancho_max=1180, padx=40)

        barra = tk.Frame(cuerpo, bg=C.FONDO)
        barra.pack(fill="x", pady=(28, 4))
        tk.Label(
            barra, text="Procesos de la planta", font=fuente(18, "bold"),
            bg=C.FONDO, fg=C.TEXTO, anchor="w",
        ).pack(side="left")
        tema.boton(
            barra, "📚  Datos técnicos de referencia", self.abrir_datos_tecnicos,
            tipo="secundario", tamano=10,
        ).pack(side="right")

        tk.Label(
            cuerpo,
            text="Los procesos marcados con ✔ ya fueron calculados y guardados.",
            font=fuente(10), bg=C.FONDO, fg=C.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x", pady=(0, 14))

        contenedor = tk.Frame(cuerpo, bg=C.FONDO)
        contenedor.pack(fill="x", pady=(0, 30))
        columnas = 2
        for c in range(columnas):
            contenedor.grid_columnconfigure(c, weight=1, uniform="procesos")

        self.botones = {}
        for i, proceso in enumerate(PROCESOS_PTAP):
            btn = tk.Button(
                contenedor,
                text=f"{i + 1:02d}    {proceso}",
                font=fuente(12, "bold"),
                bg=C.SUPERFICIE,
                fg=C.TEXTO,
                anchor="w",
                padx=24,
                pady=22,
                highlightthickness=1,
                highlightbackground=C.BORDE,
                cursor="hand2",
                command=lambda p=proceso: self.abrir_proceso(p),
            )
            btn.grid(row=i // columnas, column=i % columnas, sticky="nsew", padx=6, pady=6)
            self.botones[proceso] = btn

    def _actualizar_estado_botones(self):
        """Marca con ✔ los procesos que ya fueron calculados y guardados."""
        btn_bocatoma = self.botones.get("Captación (bocatoma con rejilla)")
        if btn_bocatoma and EstadoProyecto.rejilla_definida():
            btn_bocatoma.config(
                text="✔     Captación (bocatoma con rejilla)",
                bg=C.EXITO_FONDO, fg=C.EXITO, highlightbackground=C.EXITO,
            )

        btn_desarenador = self.botones.get("Desarenador")
        if btn_desarenador and EstadoProyecto.desarenador_definido():
            btn_desarenador.config(
                text="✔     Desarenador",
                bg=C.EXITO_FONDO, fg=C.EXITO, highlightbackground=C.EXITO,
            )

        btn_aduccion = self.botones.get("Aducción / conducción")
        if btn_aduccion and EstadoProyecto.aduccion_definida():
            btn_aduccion.config(
                text="✔     Aducción / conducción",
                bg=C.EXITO_FONDO, fg=C.EXITO, highlightbackground=C.EXITO,
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
