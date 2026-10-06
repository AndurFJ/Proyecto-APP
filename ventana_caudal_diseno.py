"""
Ventana de Caudal de Diseño.

Paso 2 del proyecto: a partir de la población de diseño (Datos
Preliminares), calcula el nivel de complejidad, la dotación,
los caudales medio diario / máximo diario / máximo horario, y el
caudal de diseño final — replicando la lógica de la hoja
"CAUDAL DE DISEÑO" del archivo de referencia (RAS 2000).
"""

import tkinter as tk
from tkinter import ttk, messagebox

from estado_proyecto import EstadoProyecto
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria


def nivel_de_complejidad(poblacion):
    """RAS 2000 - Título A: nivel de complejidad según población."""
    if poblacion < 2500:
        return "Bajo"
    elif poblacion < 12500:
        return "Medio"
    elif poblacion < 60000:
        return "Medio Alto"
    else:
        return "Alto"


def dotacion_neta_maxima(poblacion):
    """
    Dotación neta máxima (L/hab*día) según población, replicando la
    fórmula del Excel de referencia:
        <=2500 -> 110 | <=12500 -> 135 | <=60000 -> 145 | resto -> 155
    """
    if poblacion <= 2500:
        return 110
    elif poblacion <= 12500:
        return 135
    elif poblacion <= 60000:
        return 145
    else:
        return 155


class VentanaCaudalDiseño(tk.Toplevel):
    def __init__(self, master, tipo="PTAP", al_guardar=None):
        """
        tipo: "PTAP" o "PTAR" — determina el título de la ventana y en qué
        bloque de EstadoProyecto se guardan los resultados. Por ahora usa
        exactamente las mismas fórmulas para ambos tipos; cuando se
        definan las fórmulas propias de caudal de diseño para PTAR, solo
        hay que ajustar el cálculo — el guardado ya está separado.
        """
        super().__init__(master)
        self.tipo = tipo
        self.title(f"Caudal de Diseño — {tipo}")
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)

        self.al_guardar = al_guardar

        self._crear_estilos()
        self._crear_widgets()
        self._precargar_poblacion()

    # ------------------------------------------------------------------
    def _crear_estilos(self):
        """Los estilos Editable.TEntry / Editable.TCombobox los define tema.py."""

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        cuerpo, lateral = tema.layout_formulario(
            self, f"CAUDAL DE DISEÑO — {self.tipo}",
            "Dotación, pérdidas y coeficientes de consumo (Res. 0330 de 2017)",
        )

        def etiqueta(padre, texto, negrita=False, editable=False):
            if editable:
                texto = f"✎ {texto}   (dato editable)"
            tk.Label(
                padre, text=texto,
                font=fuente(10, "bold" if (negrita or editable) else "normal"),
                bg=C.SUPERFICIE,
                fg=C.EDITABLE_TEXTO if editable else C.TEXTO,
                anchor="w",
            ).pack(fill="x", pady=(8, 2))

        def resultado(padre, nombre_attr, valor_inicial="—"):
            lbl = tk.Label(
                padre, text=valor_inicial, font=fuente(11, "bold"),
                bg=C.RESULTADO_FONDO, fg=C.RESULTADO_TEXTO, anchor="w", relief="flat", bd=0,
                highlightthickness=1, highlightbackground=C.BORDE, padx=8,
            )
            lbl.pack(fill="x", ipady=4)
            setattr(self, nombre_attr, lbl)
            return lbl

        # --- Método de proyección y población ---
        etiqueta(cuerpo, "Método de proyección poblacional:", editable=True)
        self.cb_metodo = ttk.Combobox(
            cuerpo, values=["MÉTODO ARITMÉTICO", "MÉTODO GEOMÉTRICO", "MÉTODO EXPONENCIAL"],
            state="readonly", style="Editable.TCombobox",
        )
        self.cb_metodo.pack(fill="x")
        self.cb_metodo.bind("<<ComboboxSelected>>", lambda e: self.calcular())

        etiqueta(cuerpo, "Población proyectada (hab):")
        resultado(cuerpo, "lbl_poblacion")

        etiqueta(cuerpo, "Nivel de complejidad:")
        resultado(cuerpo, "lbl_nivel")

        etiqueta(cuerpo, "Dotación neta máxima (L/hab·día):")
        resultado(cuerpo, "lbl_dot_max")

        # --- Coeficiente de afectación (temperatura) ---
        etiqueta(cuerpo, "Coeficiente de afectación por temperatura:", editable=True)
        self.entry_coef = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_coef.insert(0, "1.2")
        self.entry_coef.pack(fill="x")

        etiqueta(cuerpo, "Dotación neta (L/hab·día):")
        resultado(cuerpo, "lbl_dot_neta")

        # --- % pérdidas ---
        etiqueta(cuerpo, "% Pérdidas técnicas (ej. 0.25 = 25%):", editable=True)
        self.entry_perdidas = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_perdidas.insert(0, "0.25")
        self.entry_perdidas.pack(fill="x")

        etiqueta(cuerpo, "Dotación bruta (L/hab·día):")
        resultado(cuerpo, "lbl_dot_bruta")

        etiqueta(cuerpo, "Caudal medio diario — Qmd (L/s):")
        resultado(cuerpo, "lbl_qmd")

        # --- K1 y K2 ---
        frame_k = tk.Frame(cuerpo, bg=C.SUPERFICIE)
        frame_k.pack(fill="x", pady=(8, 2))
        sub_k1 = tk.Frame(frame_k, bg=C.SUPERFICIE)
        sub_k1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        sub_k2 = tk.Frame(frame_k, bg=C.SUPERFICIE)
        sub_k2.pack(side="left", fill="x", expand=True, padx=(5, 0))

        tk.Label(sub_k1, text="✎ K1 (coef. día máx.):", font=fuente(10, "bold"),
                 bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO, anchor="w").pack(fill="x")
        self.entry_k1 = ttk.Entry(sub_k1, style="Editable.TEntry")
        self.entry_k1.insert(0, "1.4")
        self.entry_k1.pack(fill="x")

        tk.Label(sub_k2, text="✎ K2 (coef. hora máx.):", font=fuente(10, "bold"),
                 bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO, anchor="w").pack(fill="x")
        self.entry_k2 = ttk.Entry(sub_k2, style="Editable.TEntry")
        self.entry_k2.insert(0, "1.5")
        self.entry_k2.pack(fill="x")

        etiqueta(cuerpo, "Caudal máximo diario — QMD (L/s):")
        resultado(cuerpo, "lbl_qmax_diario")

        etiqueta(cuerpo, "Caudal máximo horario — QMH (L/s):")
        resultado(cuerpo, "lbl_qmax_horario")

        # --- Almacenamiento en casa ---
        etiqueta(cuerpo, "¿Se contempla almacenamiento en casa?", editable=True)
        self.var_almacenamiento = tk.StringVar(value="SI")
        frame_radio = tk.Frame(cuerpo, bg=C.EDITABLE_FONDO, bd=1, relief="solid")
        frame_radio.pack(fill="x")
        tk.Radiobutton(frame_radio, text="Sí", variable=self.var_almacenamiento, value="SI",
                        bg=C.EDITABLE_FONDO, command=self.calcular).pack(side="left", padx=10, pady=4)
        tk.Radiobutton(frame_radio, text="No", variable=self.var_almacenamiento, value="NO",
                        bg=C.EDITABLE_FONDO, command=self.calcular).pack(side="left", padx=10, pady=4)

        # --- Botón calcular ---
        tk.Button(
            lateral, text="Calcular", font=fuente(11, "bold"),
            bg=C.PRIMARIO, fg="white", cursor="hand2", command=self.calcular,
        ).pack(fill="x", pady=(15, 10), ipady=6)

        # --- Caudal de diseño (resultado final destacado en verde) ---
        marco_final = tk.Frame(
            lateral, bg=C.EXITO_FONDO, bd=0,
            highlightbackground=C.EXITO, highlightthickness=1,
        )
        marco_final.pack(fill="x", pady=(10, 15))
        tk.Label(marco_final, text="✅ ESTE ES EL CAUDAL DE DISEÑO", font=fuente(11, "bold"),
                 bg=C.EXITO_FONDO, fg=C.EXITO).pack(pady=(10, 0))
        self.lbl_caudal_final = tk.Label(
            marco_final, text="— L/s   (— m³/s)", font=fuente(18, "bold"),
            bg=C.EXITO_FONDO, fg=C.EXITO,
        )
        self.lbl_caudal_final.pack(pady=(0, 10))
        tk.Label(
            marco_final,
            text="Con este valor se diseñarán todos los procesos de la PTAP.",
            font=fuente(8, "italic"), bg=C.EXITO_FONDO, fg=C.EXITO,
        ).pack(pady=(0, 8))

        tk.Button(
            lateral, text="💾 Guardar y continuar", font=fuente(12, "bold"),
            bg=C.EXITO_BOTON, fg="white", cursor="hand2", command=self.guardar,
        ).pack(fill="x", ipady=8, pady=(0, 20))

        for entry in (self.entry_coef, self.entry_perdidas, self.entry_k1, self.entry_k2):
            entry.bind("<FocusOut>", lambda e: self.calcular())

    # ------------------------------------------------------------------
    def _precargar_poblacion(self):
        """Al abrir, selecciona por defecto el método usado en Datos Preliminares."""
        if not EstadoProyecto.esta_definido():
            messagebox.showwarning(
                "Faltan datos preliminares",
                "Primero debe definir los Datos Preliminares (proyección poblacional).",
            )
            self.destroy()
            return

        mapa = {
            "Aritmético": "MÉTODO ARITMÉTICO",
            "Geométrico": "MÉTODO GEOMÉTRICO",
            "Exponencial": "MÉTODO EXPONENCIAL",
        }
        self.cb_metodo.set(mapa.get(EstadoProyecto.metodo_diseño, "MÉTODO GEOMÉTRICO"))
        self.calcular()

    # ------------------------------------------------------------------
    def _poblacion_segun_metodo(self):
        columna = {
            "MÉTODO ARITMÉTICO": "Aritmético",
            "MÉTODO GEOMÉTRICO": "Geométrico",
            "MÉTODO EXPONENCIAL": "Exponencial",
        }[self.cb_metodo.get()]
        return float(EstadoProyecto.tabla_proyeccion.iloc[-1][columna])

    # ------------------------------------------------------------------
    def calcular(self):
        try:
            poblacion = self._poblacion_segun_metodo()
            coef_afect = float(self.entry_coef.get())
            perdidas = float(self.entry_perdidas.get())
            k1 = float(self.entry_k1.get())
            k2 = float(self.entry_k2.get())

            if not (0 <= perdidas < 1):
                raise ValueError("Las pérdidas deben estar entre 0 y 1 (ej. 0.25)")

        except (ValueError, TypeError) as e:
            messagebox.showwarning("Datos inválidos", f"Revise los valores ingresados.\n{e}")
            return

        nivel = nivel_de_complejidad(poblacion)
        dot_max = dotacion_neta_maxima(poblacion)
        dot_neta = dot_max * coef_afect
        dot_bruta = dot_neta / (1 - perdidas)

        qmd = dot_bruta * poblacion / 86400          # L/s
        q_max_diario = qmd * k1                        # L/s
        q_max_horario = q_max_diario * k2               # L/s

        if self.var_almacenamiento.get() == "SI":
            caudal_diseño = q_max_diario
        else:
            caudal_diseño = q_max_horario

        # Guardamos temporalmente (se confirman al presionar "Guardar")
        self._resultado = dict(
            poblacion=poblacion, nivel=nivel, dot_max=dot_max,
            coef_afect=coef_afect, dot_neta=dot_neta, perdidas=perdidas,
            dot_bruta=dot_bruta, qmd=qmd, k1=k1, k2=k2,
            q_max_diario=q_max_diario, q_max_horario=q_max_horario,
            almacenamiento=self.var_almacenamiento.get(),
            caudal_diseño_Ls=caudal_diseño, caudal_diseño_m3s=caudal_diseño / 1000,
        )

        self.lbl_poblacion.config(text=f"{poblacion:,.0f}")
        self.lbl_nivel.config(text=nivel)
        self.lbl_dot_max.config(text=f"{dot_max:,.0f}")
        self.lbl_dot_neta.config(text=f"{dot_neta:,.1f}")
        self.lbl_dot_bruta.config(text=f"{dot_bruta:,.1f}")
        self.lbl_qmd.config(text=f"{qmd:,.2f}")
        self.lbl_qmax_diario.config(text=f"{q_max_diario:,.2f}")
        self.lbl_qmax_horario.config(text=f"{q_max_horario:,.2f}")
        self.lbl_caudal_final.config(
            text=f"{caudal_diseño:,.2f} L/s   ({caudal_diseño / 1000:,.5f} m³/s)"
        )

    # ------------------------------------------------------------------
    def guardar(self):
        if not hasattr(self, "_resultado"):
            messagebox.showwarning("Falta calcular", "Primero presione Calcular.")
            return

        r = self._resultado

        if self.tipo == "PTAR":
            EstadoProyecto.ptar_nivel_complejidad = r["nivel"]
            EstadoProyecto.ptar_dotacion_neta_max = r["dot_max"]
            EstadoProyecto.ptar_coef_afectacion = r["coef_afect"]
            EstadoProyecto.ptar_dotacion_neta = r["dot_neta"]
            EstadoProyecto.ptar_porc_perdidas = r["perdidas"]
            EstadoProyecto.ptar_dotacion_bruta = r["dot_bruta"]
            EstadoProyecto.ptar_qmd = r["qmd"]
            EstadoProyecto.ptar_k1 = r["k1"]
            EstadoProyecto.ptar_k2 = r["k2"]
            EstadoProyecto.ptar_q_max_diario = r["q_max_diario"]
            EstadoProyecto.ptar_q_max_horario = r["q_max_horario"]
            EstadoProyecto.ptar_almacenamiento_en_casa = r["almacenamiento"]
            EstadoProyecto.ptar_caudal_diseño_Ls = r["caudal_diseño_Ls"]
            EstadoProyecto.ptar_caudal_diseño_m3s = r["caudal_diseño_m3s"]
            resumen = EstadoProyecto.resumen_caudal_ptar()
        else:
            EstadoProyecto.nivel_complejidad = r["nivel"]
            EstadoProyecto.dotacion_neta_max = r["dot_max"]
            EstadoProyecto.coef_afectacion = r["coef_afect"]
            EstadoProyecto.dotacion_neta = r["dot_neta"]
            EstadoProyecto.porc_perdidas = r["perdidas"]
            EstadoProyecto.dotacion_bruta = r["dot_bruta"]
            EstadoProyecto.qmd = r["qmd"]
            EstadoProyecto.k1 = r["k1"]
            EstadoProyecto.k2 = r["k2"]
            EstadoProyecto.q_max_diario = r["q_max_diario"]
            EstadoProyecto.q_max_horario = r["q_max_horario"]
            EstadoProyecto.almacenamiento_en_casa = r["almacenamiento"]
            EstadoProyecto.caudal_diseño_Ls = r["caudal_diseño_Ls"]
            EstadoProyecto.caudal_diseño_m3s = r["caudal_diseño_m3s"]
            resumen = EstadoProyecto.resumen_caudal()

        messagebox.showinfo(
            "Guardado",
            f"Caudal de diseño ({self.tipo}) guardado correctamente.\n\n" + resumen,
        )

        if self.al_guardar:
            self.al_guardar()

        self.destroy()
