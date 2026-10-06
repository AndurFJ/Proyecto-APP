"""
SOFTWARE DE DISEÑO PTAP / PTAR
Aplicación principal — estructura tipo H-Canales

Ventana principal -> selecciona PTAP o PTAR -> submenú de procesos
-> cada proceso abre su propia ventana de cálculo.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from ventanas_ptap import ProcesosPTAP
from ventana_datos_preliminares import VentanaDatosPreliminares
from ventana_caudal_diseno import VentanaCaudalDiseño
from ventana_datos_tecnicos import VentanaDatosTecnicos
from ventana_relleno_sanitario import VentanaRellenoSanitario
from estado_proyecto import EstadoProyecto
from generador_pdf import generar_informe_pdf
from ui_utils import ajustar_geometria, hacer_scrollable


class AplicacionPrincipal(tk.Tk):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()
        self.title("HydroLab")
        self.resizable(False, True)
        self.configure(bg="#1F4E78")
        ajustar_geometria(self, ancho=520, alto=760, alto_minimo=480)

        self._crear_widgets()

    def _crear_widgets(self):
        titulo = tk.Label(
            self,
            text="HydroLab",
            font=("Arial", 26, "bold"),
            fg="white",
            bg="#1F4E78",
            justify="center",
        )
        titulo.pack(pady=(20, 5))

        subtitulo = tk.Label(
            self,
            text="Software de Diseño de Plantas de Tratamiento\nde Agua Potable y Residual (PTAP / PTAR)",
            font=("Arial", 11),
            fg="#D9E1F2",
            bg="#1F4E78",
            justify="center",
        )
        subtitulo.pack(pady=(0, 15))

        # --- A partir de aquí, todo el contenido va dentro de un área
        # con scroll: así, sin importar qué tan pequeña sea la pantalla,
        # nunca queda nada oculto por debajo del borde de la ventana. ---
        contenedor = tk.Frame(self, bg="#1F4E78")
        contenedor.pack(fill="both", expand=True)

        canvas = tk.Canvas(contenedor, bg="#1F4E78", highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        cuerpo = tk.Frame(canvas, bg="#1F4E78")
        hacer_scrollable(canvas, cuerpo)

        btn_datos_tecnicos = tk.Button(
            cuerpo,
            text="📚 Datos Técnicos de Referencia",
            font=("Arial", 10, "bold"),
            bg="#5DADE2",
            fg="white",
            activebackground="#2E86C1",
            width=28,
            bd=0,
            cursor="hand2",
            command=self.abrir_datos_tecnicos,
        )
        btn_datos_tecnicos.pack(pady=(0, 10))

        btn_exportar = tk.Button(
            cuerpo,
            text="📄 Exportar Informe PDF",
            font=("Arial", 10, "bold"),
            bg="#8E44AD",
            fg="white",
            activebackground="#6C3483",
            width=28,
            bd=0,
            cursor="hand2",
            command=self.exportar_informe,
        )
        btn_exportar.pack(pady=(0, 20))

        btn_datos = tk.Button(
            cuerpo,
            text="① Datos Preliminares",
            font=("Arial", 12, "bold"),
            bg="#F1C40F",
            fg="#1B2631",
            activebackground="#D4AC0D",
            width=22,
            height=1,
            bd=0,
            cursor="hand2",
            command=self.abrir_datos_preliminares,
        )
        btn_datos.pack(pady=(0, 10))

        self.lbl_estado = tk.Label(
            cuerpo, text="⚠ Datos preliminares aún no definidos",
            font=("Arial", 9), fg="#F5B041", bg="#1F4E78",
        )
        self.lbl_estado.pack(pady=(0, 8))

        btn_caudal_ptap = tk.Button(
            cuerpo,
            text="② Caudal de Diseño — PTAP",
            font=("Arial", 12, "bold"),
            bg="#F1C40F",
            fg="#1B2631",
            activebackground="#D4AC0D",
            width=24,
            height=1,
            bd=0,
            cursor="hand2",
            command=self.abrir_caudal_diseño_ptap,
        )
        btn_caudal_ptap.pack(pady=(0, 5))

        self.lbl_estado_caudal_ptap = tk.Label(
            cuerpo, text="⚠ Caudal de diseño (PTAP) aún no calculado",
            font=("Arial", 9), fg="#F5B041", bg="#1F4E78",
        )
        self.lbl_estado_caudal_ptap.pack(pady=(0, 8))

        btn_caudal_ptar = tk.Button(
            cuerpo,
            text="② Caudal de Diseño — PTAR",
            font=("Arial", 12, "bold"),
            bg="#F1C40F",
            fg="#1B2631",
            activebackground="#D4AC0D",
            width=24,
            height=1,
            bd=0,
            cursor="hand2",
            command=self.abrir_caudal_diseño_ptar,
        )
        btn_caudal_ptar.pack(pady=(0, 5))

        self.lbl_estado_caudal_ptar = tk.Label(
            cuerpo, text="⚠ Caudal de diseño (PTAR) aún no calculado",
            font=("Arial", 9), fg="#F5B041", bg="#1F4E78",
        )
        self.lbl_estado_caudal_ptar.pack(pady=(0, 8))

        frame_botones = tk.Frame(cuerpo, bg="#1F4E78")
        frame_botones.pack(pady=8)

        estilo_boton = {
            "font": ("Arial", 14, "bold"),
            "width": 18,
            "height": 2,
            "bd": 0,
            "cursor": "hand2",
        }

        btn_ptap = tk.Button(
            frame_botones,
            text="PTAP",
            bg="#2E86C1",
            fg="white",
            activebackground="#1B4F72",
            command=self.abrir_ptap,
            **estilo_boton,
        )
        btn_ptap.grid(row=0, column=0, padx=15, pady=10)

        btn_ptar = tk.Button(
            frame_botones,
            text="PTAR",
            bg="#28B463",
            fg="white",
            activebackground="#1D8348",
            command=self.abrir_ptar,
            **estilo_boton,
        )
        btn_ptar.grid(row=0, column=1, padx=15, pady=10)

        btn_relleno = tk.Button(
            cuerpo,
            text="Relleno Sanitario (DORS)",
            font=("Arial", 14, "bold"),
            bg="#A04000",
            fg="white",
            activebackground="#6E2C00",
            width=24,
            height=2,
            bd=0,
            cursor="hand2",
            command=self.abrir_relleno_sanitario,
        )
        btn_relleno.pack(pady=(8, 5))

        self.lbl_estado_relleno = tk.Label(
            cuerpo, text="⚠ Cálculo poblacional del relleno aún no realizado",
            font=("Arial", 9), fg="#F5B041", bg="#1F4E78",
        )
        self.lbl_estado_relleno.pack(pady=(0, 8))

        btn_salir = tk.Button(
            cuerpo,
            text="Salir",
            font=("Arial", 10, "bold"),
            bg="#C0392B",
            fg="white",
            activebackground="#922B21",
            width=12,
            bd=0,
            cursor="hand2",
            command=self.salir,
        )
        btn_salir.pack(pady=(20, 10))

        version = tk.Label(
            cuerpo,
            text="HydroLab v0.2",
            font=("Arial", 8),
            fg="#AAB7C4",
            bg="#1F4E78",
        )
        version.pack(pady=(0, 2))

        autor = tk.Label(
            cuerpo,
            text="Elier Mendoza — Ing. Ambiental y Sanitario",
            font=("Arial", 8, "italic"),
            fg="#AAB7C4",
            bg="#1F4E78",
        )
        autor.pack(pady=(0, 15))

    def salir(self):
        respuesta = messagebox.askyesno("Salir", "¿Seguro que desea cerrar el programa?")
        if respuesta:
            self.destroy()

    def abrir_datos_tecnicos(self):
        ventana = VentanaDatosTecnicos(self)
        ventana.grab_set()

    def exportar_informe(self):
        if not (EstadoProyecto.esta_definido() or EstadoProyecto.relleno_definido()):
            respuesta = messagebox.askyesno(
                "Datos preliminares requeridos",
                "Aún no hay nada calculado. Para exportar el informe, primero "
                "debe definir al menos los Datos Preliminares.\n\n"
                "¿Desea definirlos ahora?",
            )
            if respuesta:
                self.abrir_datos_preliminares()
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar informe como PDF",
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialfile=f"Informe_PTAP_{EstadoProyecto.municipio or EstadoProyecto.rs_municipio or 'proyecto'}.pdf",
        )
        if not ruta:
            return

        try:
            generar_informe_pdf(ruta)
        except Exception as e:
            messagebox.showerror("Error al generar el informe", str(e))
            return

        respuesta = messagebox.askyesno(
            "Informe generado",
            f"El informe se guardó correctamente en:\n{ruta}\n\n¿Desea abrirlo ahora?",
        )
        if respuesta:
            try:
                if sys.platform == "win32":
                    os.startfile(ruta)
                elif sys.platform == "darwin":
                    os.system(f'open "{ruta}"')
                else:
                    os.system(f'xdg-open "{ruta}"')
            except Exception:
                pass

    def abrir_datos_preliminares(self):
        ventana = VentanaDatosPreliminares(self, al_guardar=self._actualizar_estado)
        ventana.grab_set()

    def _actualizar_estado(self):
        self.lbl_estado.config(
            text=f"✔ {EstadoProyecto.municipio} — "
                 f"Población de diseño: {EstadoProyecto.poblacion_diseño:,.0f} hab.",
            fg="#82E0AA",
        )

    def abrir_caudal_diseño_ptap(self):
        if not EstadoProyecto.esta_definido():
            respuesta = messagebox.askyesno(
                "Datos preliminares requeridos",
                "Primero debe definir los Datos Preliminares (proyección poblacional).\n\n"
                "¿Desea definirlos ahora?",
            )
            if respuesta:
                self.abrir_datos_preliminares()
            return

        ventana = VentanaCaudalDiseño(
            self, tipo="PTAP", al_guardar=self._actualizar_estado_caudal_ptap
        )
        ventana.grab_set()

    def _actualizar_estado_caudal_ptap(self):
        self.lbl_estado_caudal_ptap.config(
            text=f"✔ Caudal de diseño (PTAP): {EstadoProyecto.caudal_diseño_Ls:,.2f} L/s",
            fg="#82E0AA",
        )

    def abrir_caudal_diseño_ptar(self):
        if not EstadoProyecto.esta_definido():
            respuesta = messagebox.askyesno(
                "Datos preliminares requeridos",
                "Primero debe definir los Datos Preliminares (proyección poblacional).\n\n"
                "¿Desea definirlos ahora?",
            )
            if respuesta:
                self.abrir_datos_preliminares()
            return

        ventana = VentanaCaudalDiseño(
            self, tipo="PTAR", al_guardar=self._actualizar_estado_caudal_ptar
        )
        ventana.grab_set()

    def _actualizar_estado_caudal_ptar(self):
        self.lbl_estado_caudal_ptar.config(
            text=f"✔ Caudal de diseño (PTAR): {EstadoProyecto.ptar_caudal_diseño_Ls:,.2f} L/s",
            fg="#82E0AA",
        )

    def abrir_ptap(self):
        if not EstadoProyecto.esta_definido():
            respuesta = messagebox.askyesno(
                "Datos preliminares requeridos",
                "Aún no ha definido los Datos Preliminares (proyección poblacional).\n\n"
                "¿Desea definirlos ahora?",
            )
            if respuesta:
                self.abrir_datos_preliminares()
            return

        if not EstadoProyecto.caudal_definido():
            respuesta = messagebox.askyesno(
                "Caudal de diseño requerido",
                "Aún no ha calculado el Caudal de Diseño (PTAP).\n\n"
                "¿Desea calcularlo ahora?",
            )
            if respuesta:
                self.abrir_caudal_diseño_ptap()
            return

        ventana = ProcesosPTAP(self)
        ventana.grab_set()

    def abrir_relleno_sanitario(self):
        ventana = VentanaRellenoSanitario(self, al_guardar=self._actualizar_estado_relleno)
        ventana.grab_set()

    def _actualizar_estado_relleno(self):
        self.lbl_estado_relleno.config(
            text=f"✔ Relleno sanitario — Población {EstadoProyecto.rs_año_horizonte}: "
                 f"{EstadoProyecto.rs_poblacion_diseño:,.0f} hab.",
            fg="#82E0AA",
        )

    def abrir_ptar(self):
        messagebox.showinfo(
            "PTAR",
            "El módulo de PTAR todavía no está implementado.\n"
            "Vamos a construirlo después de terminar PTAP.",
        )


if __name__ == "__main__":
    app = AplicacionPrincipal()
    app.mainloop()
