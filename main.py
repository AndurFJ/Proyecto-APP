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
from estado_proyecto import EstadoProyecto
from generador_pdf import generar_informe_pdf
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria


class AplicacionPrincipal(tk.Tk):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()
        self.title("HydroLab")
        tema.aplicar_tema(self)
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)

        self._crear_widgets()

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        self._crear_barra_lateral()

        zona = tk.Frame(self, bg=C.FONDO)
        zona.pack(side="left", fill="both", expand=True)
        cuerpo = tema.area_desplazable(zona, bg=C.FONDO, ancho_max=1180, padx=40)

        # --- Encabezado del panel ---
        cabecera = tk.Frame(cuerpo, bg=C.FONDO)
        cabecera.pack(fill="x", pady=(36, 6))
        tk.Label(
            cabecera, text="Panel del proyecto", font=fuente(24, "bold"),
            bg=C.FONDO, fg=C.TEXTO, anchor="w",
        ).pack(fill="x")
        tk.Label(
            cabecera,
            text="Diseño de plantas de tratamiento de agua potable y residual · "
                 "Res. 0330 de 2017 (mod. Res. 799 de 2021)",
            font=fuente(11), bg=C.FONDO, fg=C.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x", pady=(4, 0))

        # --- Paso 1 y 2: datos base del proyecto ---
        tema.titulo_seccion(cuerpo, "Datos base del proyecto", bg=C.FONDO)
        fila_pasos = tk.Frame(cuerpo, bg=C.FONDO)
        fila_pasos.pack(fill="x")
        for col in range(3):
            fila_pasos.grid_columnconfigure(col, weight=1, uniform="pasos")

        self.lbl_estado = self._tarjeta_paso(
            fila_pasos, 0, "1", "Datos preliminares",
            "Ubicación, periodo de diseño y proyección poblacional.",
            "⚠ Datos preliminares aún no definidos", self.abrir_datos_preliminares,
        )
        self.lbl_estado_caudal_ptap = self._tarjeta_paso(
            fila_pasos, 1, "2", "Caudal de diseño — PTAP",
            "Dotación, pérdidas y coeficientes K1 / K2.",
            "⚠ Caudal de diseño (PTAP) aún no calculado", self.abrir_caudal_diseño_ptap,
        )
        self.lbl_estado_caudal_ptar = self._tarjeta_paso(
            fila_pasos, 2, "2", "Caudal de diseño — PTAR",
            "Caudal de aguas residuales para la PTAR.",
            "⚠ Caudal de diseño (PTAR) aún no calculado", self.abrir_caudal_diseño_ptar,
        )

        # --- Módulos de diseño ---
        tema.titulo_seccion(cuerpo, "Módulos de diseño", bg=C.FONDO)
        self.fila_modulos = tk.Frame(cuerpo, bg=C.FONDO)
        self.fila_modulos.pack(fill="x", pady=(0, 30))
        self._modulos = 0
        self.agregar_modulo(
            "PTAP", "Planta de Tratamiento de Agua Potable",
            "Captación, desarenador, aducción, mezcla rápida, floculación, "
            "sedimentación, filtración, desinfección y almacenamiento.",
            C.PTAP, self.abrir_ptap,
        )
        self.agregar_modulo(
            "PTAR", "Planta de Tratamiento de Aguas Residuales",
            "Pretratamiento, tratamiento primario y secundario de las aguas "
            "residuales del municipio.",
            C.PTAR, self.abrir_ptar,
        )

    # ------------------------------------------------------------------
    def _crear_barra_lateral(self):
        barra = tk.Frame(self, bg=C.ENCABEZADO, width=320)
        barra.pack(side="left", fill="y")
        barra.pack_propagate(False)

        marca = tk.Frame(barra, bg=C.ENCABEZADO)
        marca.pack(fill="x", padx=28, pady=(36, 28))
        tk.Label(
            marca, text="💧", font=fuente(28), bg=C.ENCABEZADO, fg=C.ACENTO, anchor="w",
        ).pack(fill="x")
        tk.Label(
            marca, text="HydroLab", font=fuente(24, "bold"),
            bg=C.ENCABEZADO, fg="white", anchor="w",
        ).pack(fill="x")
        tk.Label(
            marca,
            text="Software de Diseño de Plantas de Tratamiento de Agua Potable "
                 "y Residual (PTAP / PTAR)",
            font=fuente(9), bg=C.ENCABEZADO, fg=C.ENCABEZADO_SUBTEXTO,
            anchor="w", justify="left", wraplength=240,
        ).pack(fill="x", pady=(6, 0))

        tk.Frame(barra, bg=C.ENCABEZADO_2, height=1).pack(fill="x", padx=28)

        tk.Label(
            barra, text="HERRAMIENTAS", font=fuente(8, "bold"),
            bg=C.ENCABEZADO, fg=C.ENCABEZADO_SUBTEXTO, anchor="w",
        ).pack(fill="x", padx=28, pady=(24, 8))

        def opcion(texto, comando):
            tk.Button(
                barra, text=texto, font=fuente(10), anchor="w",
                bg=C.ENCABEZADO, fg="white", padx=16, pady=10,
                command=comando,
            ).pack(fill="x", padx=12, pady=2)

        opcion("📚   Datos técnicos de referencia", self.abrir_datos_tecnicos)
        opcion("📄   Exportar informe PDF", self.exportar_informe)

        pie = tk.Frame(barra, bg=C.ENCABEZADO)
        pie.pack(side="bottom", fill="x", padx=28, pady=(0, 28))
        tema.boton(pie, "Salir", self.salir, tipo="oscuro", tamano=10).pack(fill="x", pady=(0, 18))
        tk.Label(
            pie, text="HydroLab v0.2", font=fuente(8, "bold"),
            bg=C.ENCABEZADO, fg=C.ENCABEZADO_SUBTEXTO, anchor="w",
        ).pack(fill="x")
        tk.Label(
            pie, text="Elier Mendoza\nIng. Ambiental y Sanitario",
            font=fuente(8, "italic"), bg=C.ENCABEZADO, fg=C.ENCABEZADO_SUBTEXTO,
            anchor="w", justify="left",
        ).pack(fill="x")

    # ------------------------------------------------------------------
    def _tarjeta_paso(self, padre, columna, numero, titulo, descripcion, estado, comando):
        """Tarjeta de un paso previo (datos preliminares / caudal). Devuelve su etiqueta de estado."""
        card = tema.tarjeta(padre)
        card.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 8, 0 if columna == 2 else 8))
        interior = tk.Frame(card, bg=C.SUPERFICIE)
        interior.pack(fill="both", expand=True, padx=22, pady=20)

        cabeza = tk.Frame(interior, bg=C.SUPERFICIE)
        cabeza.pack(fill="x")
        tk.Label(
            cabeza, text=f"PASO {numero}", font=fuente(8, "bold"),
            bg=C.PRIMARIO_SUAVE, fg=C.PRIMARIO, padx=8, pady=3,
        ).pack(side="left")
        lbl_titulo = tk.Label(
            interior, text=titulo, font=fuente(13, "bold"),
            bg=C.SUPERFICIE, fg=C.TEXTO, anchor="w", justify="left",
        )
        tema.ajustar_al_ancho(lbl_titulo).pack(fill="x", pady=(10, 0))

        lbl_desc = tk.Label(
            interior, text=descripcion, font=fuente(10), bg=C.SUPERFICIE,
            fg=C.TEXTO_SECUNDARIO, anchor="w", justify="left",
        )
        tema.ajustar_al_ancho(lbl_desc).pack(fill="x", pady=(6, 10))

        lbl = tk.Label(
            interior, text=estado, font=fuente(9, "bold"), bg=C.ADVERTENCIA_FONDO,
            fg=C.ADVERTENCIA, anchor="w", justify="left", padx=10, pady=6,
        )
        tema.ajustar_al_ancho(lbl, margen=20)
        lbl.pack(fill="x", pady=(0, 14))

        tema.boton(interior, "Abrir  →", comando, tipo="secundario", tamano=10).pack(anchor="w")
        return lbl

    def agregar_modulo(self, sigla, nombre, descripcion, color, comando):
        """Agrega una tarjeta grande de módulo (PTAP, PTAR, ...) al panel."""
        col = self._modulos % 2
        fila = self._modulos // 2
        self._modulos += 1
        self.fila_modulos.grid_columnconfigure(col, weight=1, uniform="modulos")

        card = tema.tarjeta(self.fila_modulos)
        card.grid(row=fila, column=col, sticky="nsew",
                  padx=(0 if col == 0 else 8, 8 if col == 0 else 0), pady=(0, 16))
        tk.Frame(card, bg=color, height=6).pack(fill="x")
        interior = tk.Frame(card, bg=C.SUPERFICIE)
        interior.pack(fill="both", expand=True, padx=26, pady=22)

        tk.Label(
            interior, text=sigla, font=fuente(26, "bold"),
            bg=C.SUPERFICIE, fg=color, anchor="w",
        ).pack(fill="x")
        lbl_nombre = tk.Label(
            interior, text=nombre, font=fuente(12, "bold"),
            bg=C.SUPERFICIE, fg=C.TEXTO, anchor="w", justify="left",
        )
        tema.ajustar_al_ancho(lbl_nombre).pack(fill="x")
        lbl_desc = tk.Label(
            interior, text=descripcion, font=fuente(10), bg=C.SUPERFICIE,
            fg=C.TEXTO_SECUNDARIO, anchor="w", justify="left",
        )
        tema.ajustar_al_ancho(lbl_desc).pack(fill="x", pady=(8, 16))
        tk.Button(
            interior, text=f"Diseñar {sigla}  →", font=fuente(12, "bold"),
            bg=color, fg="white", padx=22, pady=10, command=comando,
        ).pack(anchor="w")

    def salir(self):
        respuesta = messagebox.askyesno("Salir", "¿Seguro que desea cerrar el programa?")
        if respuesta:
            self.destroy()

    def abrir_datos_tecnicos(self):
        ventana = VentanaDatosTecnicos(self)
        ventana.grab_set()

    def exportar_informe(self):
        if not EstadoProyecto.esta_definido():
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
            initialfile=f"Informe_PTAP_{EstadoProyecto.municipio or 'proyecto'}.pdf",
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
            fg=C.EXITO, bg=C.EXITO_FONDO,
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
            fg=C.EXITO, bg=C.EXITO_FONDO,
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
            fg=C.EXITO, bg=C.EXITO_FONDO,
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

    def abrir_ptar(self):
        messagebox.showinfo(
            "PTAR",
            "El módulo de PTAR todavía no está implementado.\n"
            "Vamos a construirlo después de terminar PTAP.",
        )


if __name__ == "__main__":
    app = AplicacionPrincipal()
    app.mainloop()
