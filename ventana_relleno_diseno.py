"""
Ventana del Paso 2 del relleno sanitario: residuos, volumen, área y
celda diaria de operación (ver relleno_sanitario.py para las fórmulas).

Parte de la proyección poblacional guardada en el Paso 1 (campos rs_*
de EstadoProyecto) y guarda sus resultados en los campos rsd_*. Los
colores y fuentes salen del tema del software (tema.py).
"""

import tkinter as tk
from tkinter import ttk, messagebox

import relleno_sanitario as rs
from estado_proyecto import EstadoProyecto
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria


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

# Ancho (px) del panel de datos de entrada y de sus textos
ANCHO_PANEL = 430
ANCHO_TEXTO = 360


class VentanaDisenoRelleno(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Relleno Sanitario — Residuos, volumen y área")
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)

        self.al_guardar = al_guardar
        self.entradas = {}
        self.resultado = None

        self._crear_widgets()
        self._precargar()

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        tema.encabezado(
            self, "RELLENO SANITARIO — Residuos, volumen, área y celda diaria",
            f"Población del Paso 1: {EstadoProyecto.rs_metodo_adoptado}, "
            f"desde {EstadoProyecto.rs_año_inicio} — Método de celda diaria",
        )

        cuerpo = tk.Frame(self, bg=C.FONDO)
        cuerpo.pack(fill="both", expand=True, padx=32, pady=24)

        izq = tema.tarjeta(cuerpo)
        izq.configure(width=ANCHO_PANEL)
        izq.pack(side="left", fill="y", padx=(0, 24))
        izq.pack_propagate(False)
        marco = tema.area_desplazable(izq, bg=C.SUPERFICIE)
        panel = tk.Frame(marco, bg=C.SUPERFICIE)
        panel.pack(fill="both", expand=True, padx=(22, 14), pady=(6, 10))

        der = tema.tarjeta(cuerpo)
        der.pack(side="right", fill="both", expand=True)

        self._crear_panel_entradas(panel)
        self._crear_panel_resultados(der)

    def _crear_panel_entradas(self, padre):
        tk.Label(padre, text="DATOS DE DISEÑO", font=fuente(9, "bold"), bg=C.SUPERFICIE,
                 fg=C.TEXTO_TENUE, anchor="w").pack(fill="x", pady=(10, 0))
        for attr, etiqueta, defecto, nota in ENTRADAS:
            tk.Label(padre, text=f"✎ {etiqueta}:", font=fuente(10, "bold"),
                     bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO, anchor="w",
                     justify="left", wraplength=ANCHO_TEXTO).pack(fill="x", pady=(10, 3))
            entry = ttk.Entry(padre, style="Editable.TEntry")
            entry.insert(0, f"{defecto:g}")
            entry.pack(fill="x")
            if nota:
                tk.Label(padre, text=nota, font=fuente(8, "italic"), bg=C.SUPERFICIE,
                         fg=C.TEXTO_TENUE, anchor="w", justify="left",
                         wraplength=ANCHO_TEXTO).pack(fill="x", pady=(2, 0))
            self.entradas[attr] = entry

        for texto, color, comando, tam in [
                ("Calcular", C.PRIMARIO, self.calcular, 11),
                ("💾 Guardar y continuar", C.EXITO_BOTON, self.guardar, 12)]:
            tk.Button(padre, text=texto, font=fuente(tam, "bold"), bg=color, fg="white",
                      activebackground=color, activeforeground="white", bd=0,
                      cursor="hand2", command=comando,
                      ).pack(fill="x", pady=(16, 0), ipady=7)
        tk.Frame(padre, bg=C.SUPERFICIE, height=16).pack()

    def _crear_panel_resultados(self, padre):
        marco = tk.Frame(padre, bg=C.EXITO_FONDO, highlightbackground=C.EXITO,
                         highlightcolor=C.EXITO, highlightthickness=1, bd=0)
        marco.pack(fill="x", padx=20, pady=(20, 12))
        self.lbl_totales = tk.Label(
            marco, text="Calcule para ver el volumen y el área del relleno.",
            font=fuente(12, "bold"), bg=C.EXITO_FONDO, fg=C.EXITO,
            justify="center", pady=12,
        )
        self.lbl_totales.pack(fill="x", padx=10)

        tk.Label(padre, text="RESIDUOS Y VOLÚMENES AÑO POR AÑO", font=fuente(9, "bold"),
                 bg=C.SUPERFICIE, fg=C.TEXTO_TENUE, anchor="w").pack(fill="x", padx=20, pady=(6, 4))
        marco_tabla = tk.Frame(padre, bg=C.SUPERFICIE)
        marco_tabla.pack(fill="both", expand=True, padx=20, pady=(2, 6))
        barra = ttk.Scrollbar(marco_tabla, orient="vertical")
        self.tabla = ttk.Treeview(marco_tabla, columns=[c[0] for c in COLUMNAS_TABLA],
                                  show="headings", height=10, yscrollcommand=barra.set)
        barra.config(command=self.tabla.yview)
        for clave, texto, ancho, _ in COLUMNAS_TABLA:
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=ancho, minwidth=ancho, anchor="center")
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        leyenda = tk.Label(padre, text=LEYENDA_TABLA, font=fuente(8, "italic"), bg=C.SUPERFICIE,
                           fg=C.TEXTO_TENUE, anchor="w", justify="left", wraplength=760)
        leyenda.pack(fill="x", padx=20, pady=(0, 8))
        tema.ajustar_al_ancho(leyenda, margen=40)

        tk.Label(padre, text="CELDA DIARIA DE OPERACIÓN", font=fuente(9, "bold"),
                 bg=C.SUPERFICIE, fg=C.TEXTO_TENUE, anchor="w").pack(fill="x", padx=20, pady=(6, 4))
        self.lbl_celda = tk.Label(
            padre, text="—", font=fuente(10), bg=C.RESULTADO_FONDO,
            fg=C.RESULTADO_TEXTO, anchor="w", justify="left", relief="flat", bd=0,
            highlightthickness=1, highlightbackground=C.BORDE, padx=8, pady=6,
        )
        self.lbl_celda.pack(fill="x", padx=20, pady=(2, 20))
        tema.ajustar_al_ancho(self.lbl_celda, margen=60)

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
