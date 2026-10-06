"""
Ventana del Paso 2 del relleno sanitario: residuos, volumen, área y
celda diaria de operación (ver relleno_sanitario.py para las fórmulas).

Parte de la proyección poblacional guardada en el Paso 1 (campos rs_*
de EstadoProyecto) y guarda sus resultados en los campos rsd_*. Usa los
mismos COLORES y FUENTES que la ventana del Paso 1.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import relleno_sanitario as rs
from estado_proyecto import EstadoProyecto
from ui_utils import ajustar_geometria, hacer_scrollable
from ventana_relleno_sanitario import COLORES, FUENTES


# (atributo, etiqueta, valor por defecto, nota)
ENTRADAS = [
    ("vida_util", "Vida útil del relleno (años)", rs.VIDA_UTIL_DEFECTO,
     "Desde el primer año de la proyección del Paso 1 (máx. 50)."),
    ("ppc", "Producción per cápita inicial, PPC (kg/hab·día)", rs.PPC_DEFECTO, None),
    ("incremento", "Incremento anual de la PPC (%)", rs.INCREMENTO_PPC_DEFECTO,
     "Suele tomarse entre 0.5 y 1 % anual."),
    ("cobertura", "Cobertura de recolección (%)", rs.COBERTURA_DEFECTO, None),
    ("densidad", "Densidad de los residuos compactados, Drsm (kg/m³)",
     rs.DENSIDAD_COMPACTADA_DEFECTO, "Relleno manual: 400 a 600 kg/m³."),
    ("material", "Material de cobertura, m.c. (% del volumen)",
     rs.MATERIAL_COBERTURA_DEFECTO, "Usualmente 20 a 25 %."),
    ("profundidad", "Profundidad o altura media del relleno, hrs (m)", rs.PROFUNDIDAD_DEFECTO, None),
    ("factor", "Factor de área adicional, F", rs.FACTOR_AREA_DEFECTO,
     "Vías, cerca, drenajes y retiros: 1.2 a 1.4."),
    ("dias", "Días laborables por semana", rs.DIAS_LABORABLES_DEFECTO, None),
    ("altura_celda", "Altura de la celda diaria, hc (m)", rs.ALTURA_CELDA_DEFECTO,
     "Relleno manual: 1.0 a 1.5 m."),
    ("ancho_celda", "Ancho de la celda (frente de trabajo, m)", rs.ANCHO_CELDA_DEFECTO, None),
]

COLUMNAS_TABLA = [
    ("AÑO", "Año", 50, "{:.0f}"),
    ("Población", "Población", 80, "{:,.0f}"),
    ("PPC", "PPC", 55, "{:.3f}"),
    ("DSr", "t/día", 60, "{:,.2f}"),
    ("DSa", "t/año", 70, "{:,.0f}"),
    ("Vcompactado", "V. comp.", 75, "{:,.0f}"),
    ("Vcobertura", "V. cob.", 70, "{:,.0f}"),
    ("Vrelleno", "V. relleno", 80, "{:,.0f}"),
    ("Vacumulado", "V. acum.", 85, "{:,.0f}"),
]
LEYENDA_TABLA = (
    "PPC en kg/hab·día · t/día: residuos recolectados · t/año: residuos dispuestos · "
    "V. comp.: residuos compactados · V. cob.: material de cobertura · "
    "V. relleno y V. acum.: volumen del año y acumulado (todos los volúmenes en m³)"
)


class VentanaDisenoRelleno(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Relleno Sanitario — Residuos, volumen y área")
        self.resizable(True, True)
        ajustar_geometria(self, ancho=1180, alto=780)
        self.configure(bg=COLORES["fondo"])

        self.al_guardar = al_guardar
        self.entradas = {}
        self.resultado = None

        self._crear_widgets()
        self._precargar()

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        tk.Label(
            self, text="RELLENO SANITARIO — Residuos, volumen, área y celda diaria",
            font=FUENTES["titulo"], bg=COLORES["encabezado"],
            fg=COLORES["encabezado_texto"], pady=10,
        ).pack(fill="x")
        tk.Label(
            self, text=f"Población del Paso 1: {EstadoProyecto.rs_metodo_adoptado}, "
                       f"desde {EstadoProyecto.rs_año_inicio} — Método de celda diaria",
            font=FUENTES["subtitulo"], bg=COLORES["encabezado"],
            fg=COLORES["encabezado_sub"], pady=4,
        ).pack(fill="x")

        cuerpo = tk.Frame(self, bg=COLORES["fondo"])
        cuerpo.pack(fill="both", expand=True, padx=15, pady=10)

        izq = tk.Frame(cuerpo, bg=COLORES["fondo"], width=340)
        izq.pack(side="left", fill="y", padx=(0, 15))
        izq.pack_propagate(False)
        canvas = tk.Canvas(izq, bg=COLORES["fondo"], highlightthickness=0)
        barra = ttk.Scrollbar(izq, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=barra.set)
        canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        panel = tk.Frame(canvas, bg=COLORES["fondo"])
        hacer_scrollable(canvas, panel)

        der = tk.Frame(cuerpo, bg=COLORES["panel"], bd=1, relief="solid")
        der.pack(side="right", fill="both", expand=True)

        self._crear_panel_entradas(panel)
        self._crear_panel_resultados(der)

    def _crear_panel_entradas(self, padre):
        for attr, etiqueta, defecto, nota in ENTRADAS:
            tk.Label(padre, text=f"✎ {etiqueta}:", font=FUENTES["seccion"],
                     bg=COLORES["fondo"], fg=COLORES["editable"], anchor="w",
                     justify="left", wraplength=300).pack(fill="x", pady=(8, 2), padx=(0, 8))
            entry = ttk.Entry(padre)
            entry.insert(0, f"{defecto:g}")
            entry.pack(fill="x", padx=(0, 8))
            if nota:
                tk.Label(padre, text=nota, font=FUENTES["nota"], bg=COLORES["fondo"],
                         fg=COLORES["texto_suave"], anchor="w", justify="left",
                         wraplength=300).pack(fill="x", padx=(0, 8))
            self.entradas[attr] = entry

        for texto, color, comando in [("Calcular", COLORES["boton_calcular"], self.calcular),
                                      ("Guardar y continuar", COLORES["boton_guardar"], self.guardar)]:
            tk.Button(padre, text=texto, font=FUENTES["boton"], bg=color, fg="white",
                      activebackground=color, bd=0, cursor="hand2", command=comando,
                      ).pack(fill="x", pady=(14, 0), padx=(0, 8), ipady=6)
        tk.Frame(padre, bg=COLORES["fondo"], height=14).pack()

    def _crear_panel_resultados(self, padre):
        marco = tk.Frame(padre, bg=COLORES["ok_fondo"],
                         highlightbackground=COLORES["ok_texto"], highlightthickness=2)
        marco.pack(fill="x", padx=10, pady=(10, 6))
        self.lbl_totales = tk.Label(
            marco, text="Calcule para ver el volumen y el área del relleno.",
            font=FUENTES["resultado"], bg=COLORES["ok_fondo"], fg=COLORES["ok_texto"],
            justify="center", pady=8,
        )
        self.lbl_totales.pack(fill="x")

        tk.Label(padre, text="Residuos y volúmenes año por año", font=FUENTES["seccion"],
                 bg=COLORES["panel"], fg=COLORES["texto"], anchor="w").pack(fill="x", padx=10)
        marco_tabla = tk.Frame(padre, bg=COLORES["panel"])
        marco_tabla.pack(fill="both", expand=True, padx=10, pady=(2, 6))
        barra = ttk.Scrollbar(marco_tabla, orient="vertical")
        self.tabla = ttk.Treeview(marco_tabla, columns=[c[0] for c in COLUMNAS_TABLA],
                                  show="headings", height=10, yscrollcommand=barra.set)
        barra.config(command=self.tabla.yview)
        for clave, texto, ancho, _ in COLUMNAS_TABLA:
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=ancho, minwidth=ancho, anchor="center")
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        tk.Label(padre, text=LEYENDA_TABLA, font=FUENTES["nota"], bg=COLORES["panel"],
                 fg=COLORES["texto_suave"], anchor="w", justify="left",
                 wraplength=760).pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(padre, text="Celda diaria de operación", font=FUENTES["seccion"],
                 bg=COLORES["panel"], fg=COLORES["texto"], anchor="w").pack(fill="x", padx=10)
        self.lbl_celda = tk.Label(
            padre, text="—", font=FUENTES["normal"], bg=COLORES["panel"],
            fg=COLORES["resultado"], anchor="w", justify="left",
        )
        self.lbl_celda.pack(fill="x", padx=10, pady=(2, 12))

    # ------------------------------------------------------------------
    def _leer(self):
        valores = {}
        for attr, etiqueta, _, _ in ENTRADAS:
            texto = self.entradas[attr].get().strip().replace(",", ".")
            try:
                valores[attr] = float(texto)
            except ValueError:
                raise ValueError(f"Revise el dato «{etiqueta}»: debe ser un número.")
        for attr in ("vida_util", "dias"):
            if valores[attr] != int(valores[attr]):
                raise ValueError("La vida útil y los días laborables deben ser números enteros.")
            valores[attr] = int(valores[attr])
        return valores

    def calcular(self):
        try:
            v = self._leer()
            tabla, totales = rs.calcular_volumen_area(
                EstadoProyecto.rs_tabla_proyeccion, EstadoProyecto.rs_metodo_adoptado,
                v["vida_util"], v["ppc"], v["incremento"], v["cobertura"], v["densidad"],
                v["material"], v["profundidad"], v["factor"],
            )
            celdas = [
                rs.calcular_celda_diaria(tabla.iloc[i]["DSr"], v["densidad"], v["material"],
                                         v["dias"], v["altura_celda"], v["ancho_celda"])
                for i in (0, -1)
            ]
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e), parent=self)
            return
        self.resultado = (v, tabla, totales, celdas)
        self._mostrar()

    def _mostrar(self):
        v, tabla, totales, (celda_ini, celda_fin) = self.resultado
        self.lbl_totales.config(text=(
            f"Volumen total del relleno: {totales['volumen_total']:,.0f} m³\n"
            f"Área a rellenar: {totales['area_relleno']:,.0f} m²   ·   "
            f"Área total requerida: {totales['area_total']:,.0f} m² "
            f"({totales['area_total'] / 10000:,.2f} ha)"
        ))

        self.tabla.delete(*self.tabla.get_children())
        for _, fila in tabla.iterrows():
            self.tabla.insert("", "end", values=[fmt.format(fila[clave])
                                                 for clave, _, _, fmt in COLUMNAS_TABLA])

        lineas = []
        for nombre, fila, celda in [("Primer año", tabla.iloc[0], celda_ini),
                                    ("Último año", tabla.iloc[-1], celda_fin)]:
            lineas.append(
                f"{nombre} ({int(fila['AÑO'])}): {celda['residuos_dia_laboral']:,.2f} t por día laborable  →  "
                f"volumen {celda['volumen']:,.1f} m³, área {celda['area']:,.1f} m², "
                f"{celda['largo']:,.1f} m de largo × {v['ancho_celda']:g} m de ancho × "
                f"{v['altura_celda']:g} m de alto"
            )
        self.lbl_celda.config(text="\n".join(lineas))

    # ------------------------------------------------------------------
    def _precargar(self):
        if not EstadoProyecto.relleno_diseno_definido():
            return
        for attr, entry in self.entradas.items():
            entry.delete(0, "end")
            entry.insert(0, f"{EstadoProyecto.rsd_entradas[attr]:g}")
        self.calcular()

    def guardar(self):
        if self.resultado is None:
            messagebox.showwarning("Falta calcular", "Primero presione Calcular.", parent=self)
            return
        v, tabla, totales, (celda_ini, celda_fin) = self.resultado
        EstadoProyecto.rsd_entradas = dict(v)
        EstadoProyecto.rsd_tabla = tabla
        EstadoProyecto.rsd_volumen_total = totales["volumen_total"]
        EstadoProyecto.rsd_residuos_total = totales["residuos_total"]
        EstadoProyecto.rsd_area_relleno = totales["area_relleno"]
        EstadoProyecto.rsd_area_total = totales["area_total"]
        EstadoProyecto.rsd_celda_inicial = celda_ini
        EstadoProyecto.rsd_celda_final = celda_fin

        messagebox.showinfo("Datos guardados",
                            "El diseño del relleno sanitario se guardó correctamente.\n\n"
                            + EstadoProyecto.resumen_relleno_diseno(), parent=self)
        if self.al_guardar:
            self.al_guardar()
        self.destroy()
