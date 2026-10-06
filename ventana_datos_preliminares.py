"""
Ventana de Datos Preliminares.

Primer paso obligatorio antes de diseñar cualquier proceso de PTAP o
PTAR: define la ubicación, el periodo de diseño, calcula la
proyección poblacional (3 métodos de cálculo: aritmético, geométrico
y exponencial) y permite elegir la población de diseño que usarán
las demás ventanas de cálculo.

La proyección se puede alimentar con tres FUENTES de datos distintas
(seleccionables por el usuario):

Para los métodos 1 y 2 (que entregan varios datos poblacionales), la
tasa/coeficiente de cada uno de los 3 métodos de proyección (aritmético,
geométrico, exponencial) NO se calcula solo con el primer y el último
dato. Se calcula la tasa entre cada PAR DE AÑOS CONSECUTIVOS de la
serie (ej.: 2018-2019, 2019-2020, 2020-2021, ...) y luego se PROMEDIAN
todas esas tasas parciales (ver _tasas_desde_serie). Así se aprovechan
todos los datos intermedios y no solo los dos extremos.

1. Base de datos DANE — selecciona departamento/municipio y toma
   automáticamente los últimos 5 datos poblacionales disponibles
   antes del año de inicio del proyecto (para calcular las tasas de
   crecimiento, promediando cada par consecutivo). En la tabla y la
   gráfica, TODOS los años con dato real en la base de datos anteriores
   al año de inicio se muestran tal cual (columna "Tipo" = Histórico
   (BD)); solo año_inicio en adelante se calcula con los 3 métodos de
   proyección.
2. Ingreso manual de los últimos 5 datos censales — el usuario digita
   directamente 5 pares (año, población); la tasa de cada método se
   calcula igual que en el método 1: promediando cada par de años
   consecutivos.
3. Año censal + tasa de crecimiento — el usuario digita un único año
   base, su población y una tasa de crecimiento anual (%), y esa tasa
   se usa para alimentar los 3 métodos de proyección (ver detalle en
   _tasas_desde_censo_y_tasa).
"""

import math

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import datos_dane
from estado_proyecto import EstadoProyecto
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria


FUENTE_DANE = "Base de datos DANE (departamento / municipio)"
FUENTE_MANUAL = "Ingreso manual — datos censales (2 o más)"
FUENTE_TASA = "Año censal + tasa de crecimiento"


class VentanaDatosPreliminares(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Datos Preliminares — Proyección Poblacional")
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)

        self.al_guardar = al_guardar  # callback opcional al guardar
        self.df_proyeccion = None
        self._elementos_resaltado = []
        self.entries_manual = []  # [(entry_año, entry_pob), ...]

        self._crear_widgets()

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        tema.encabezado(
            self, "DATOS PRELIMINARES — Proyección Poblacional",
            "Ubicación, periodo de diseño y proyección por los métodos aritmético, "
            "geométrico y exponencial",
        )

        cuerpo = tk.Frame(self, bg=C.FONDO)
        cuerpo.pack(fill="both", expand=True, padx=32, pady=24)

        panel_izq_contenedor = tema.tarjeta(cuerpo)
        panel_izq_contenedor.configure(width=400)
        panel_izq_contenedor.pack(side="left", fill="y", padx=(0, 24))
        panel_izq_contenedor.pack_propagate(False)

        canvas_izq = tk.Canvas(panel_izq_contenedor, bg=C.SUPERFICIE, highlightthickness=0, width=380)
        canvas_izq._hydrolab_scroll = True
        scrollbar_izq = ttk.Scrollbar(panel_izq_contenedor, orient="vertical", command=canvas_izq.yview)
        canvas_izq.configure(yscrollcommand=scrollbar_izq.set)
        canvas_izq.pack(side="left", fill="both", expand=True)
        scrollbar_izq.pack(side="right", fill="y")

        panel_izq = tk.Frame(canvas_izq, bg=C.SUPERFICIE, padx=22, pady=10)
        ventana_izq_id = canvas_izq.create_window((0, 0), window=panel_izq, anchor="nw")
        panel_izq.bind(
            "<Configure>",
            lambda e: canvas_izq.configure(scrollregion=canvas_izq.bbox("all")),
        )
        canvas_izq.bind(
            "<Configure>",
            lambda e: canvas_izq.itemconfig(ventana_izq_id, width=e.width),
        )

        panel_der = tema.tarjeta(cuerpo)
        panel_der.pack(side="right", fill="both", expand=True)

        self._crear_panel_entrada(panel_izq)
        self._crear_panel_resultados(panel_der)

    # ------------------------------------------------------------------
    def _crear_panel_entrada(self, padre):
        def etiqueta(texto):
            tk.Label(padre, text=texto, font=fuente(10, "bold"),
                     bg=C.SUPERFICIE, anchor="w").pack(fill="x", pady=(10, 2))

        etiqueta("Fuente de datos poblacionales:")
        self.cb_fuente = ttk.Combobox(
            padre, values=[FUENTE_DANE, FUENTE_MANUAL, FUENTE_TASA],
            state="readonly", width=30,
        )
        self.cb_fuente.current(0)
        self.cb_fuente.pack(fill="x")
        self.cb_fuente.bind("<<ComboboxSelected>>", self._cambiar_fuente)

        etiqueta("Departamento:")
        self.cb_depto = ttk.Combobox(padre, values=datos_dane.obtener_departamentos(),
                                       state="readonly", width=30)
        self.cb_depto.pack(fill="x")
        self.cb_depto.bind("<<ComboboxSelected>>", self._al_cambiar_depto)

        etiqueta("Municipio:")
        self.cb_municipio = ttk.Combobox(padre, values=[], state="readonly", width=30)
        self.cb_municipio.pack(fill="x")

        # --- Contenedor que alterna entre los 3 paneles de fuente de datos ---
        self.contenedor_fuente = tk.Frame(padre, bg=C.SUPERFICIE)
        self.contenedor_fuente.pack(fill="x")

        self._crear_panel_area(self.contenedor_fuente)
        self._crear_panel_manual(self.contenedor_fuente)
        self._crear_panel_tasa(self.contenedor_fuente)

        self.frame_area.pack(fill="x")  # visible por defecto (fuente DANE)

        etiqueta("Año de inicio del proyecto:")
        self.entry_año_inicio = ttk.Entry(padre, width=32)
        self.entry_año_inicio.pack(fill="x")
        self.entry_año_inicio.insert(0, "2025")

        etiqueta("Periodo de diseño (años):")
        self.entry_periodo = ttk.Entry(padre, width=32)
        self.entry_periodo.pack(fill="x")
        self.entry_periodo.insert(0, "25")

        btn_calcular = tk.Button(
            padre, text="Calcular proyección", font=fuente(11, "bold"),
            bg=C.PRIMARIO, fg="white", cursor="hand2",
            command=self.calcular_proyeccion,
        )
        btn_calcular.pack(fill="x", pady=(20, 10), ipady=6)

        etiqueta("Método a usar como diseño:")
        self.cb_metodo_diseño = ttk.Combobox(
            padre, values=["Aritmético", "Geométrico", "Exponencial"],
            state="readonly", width=30,
        )
        self.cb_metodo_diseño.pack(fill="x")
        self.cb_metodo_diseño.current(1)  # geométrico por defecto

        self.lbl_poblacion_diseño = tk.Label(
            padre, text="Población de diseño: —", font=fuente(10, "bold"),
            bg=C.SUPERFICIE, fg=C.RESULTADO_TEXTO, justify="left", anchor="w", wraplength=320,
        )
        self.lbl_poblacion_diseño.pack(fill="x", pady=(10, 5))
        self.cb_metodo_diseño.bind("<<ComboboxSelected>>", self._actualizar_poblacion_diseño)

        btn_guardar = tk.Button(
            padre, text="Guardar y continuar", font=fuente(11, "bold"),
            bg=C.EXITO_BOTON, fg="white", cursor="hand2",
            command=self.guardar,
        )
        btn_guardar.pack(fill="x", pady=(20, 10), ipady=6)

    # ------------------------------------------------------------------
    def _crear_panel_area(self, padre):
        """Panel de la fuente DANE: área geográfica."""
        self.frame_area = tk.Frame(padre, bg=C.SUPERFICIE)
        tk.Label(self.frame_area, text="Área geográfica:", font=fuente(10, "bold"),
                 bg=C.SUPERFICIE, anchor="w").pack(fill="x", pady=(10, 2))
        self.cb_area = ttk.Combobox(
            self.frame_area,
            values=["Cabecera Municipal", "Centros Poblados y Rural Disperso", "Total"],
            state="readonly", width=30,
        )
        self.cb_area.pack(fill="x")
        self.cb_area.current(2)

    # ------------------------------------------------------------------
    def _crear_panel_manual(self, padre):
        """Panel de la fuente 'Ingreso manual — datos censales (2 o más)'."""
        self.frame_manual = tk.Frame(padre, bg=C.SUPERFICIE)
        tk.Label(self.frame_manual, text="✎ Datos censales — mínimo 2, sin máximo (dato editable):",
                 font=fuente(10, "bold"), bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO,
                 anchor="w", wraplength=320, justify="left").pack(fill="x", pady=(10, 4))

        cabecera = tk.Frame(self.frame_manual, bg=C.SUPERFICIE)
        cabecera.pack(fill="x")
        tk.Label(cabecera, text="Año", width=13, bg=C.SUPERFICIE,
                 font=fuente(9, "bold"), anchor="w").pack(side="left")
        tk.Label(cabecera, text="Población (hab.)", width=16, bg=C.SUPERFICIE,
                 font=fuente(9, "bold"), anchor="w").pack(side="left")

        # Contenedor donde viven las filas — permite agregar más dinámicamente
        self.frame_filas_manual = tk.Frame(self.frame_manual, bg=C.SUPERFICIE)
        self.frame_filas_manual.pack(fill="x")

        self.entries_manual = []
        for _ in range(5):
            self._agregar_fila_manual()

        frame_botones_filas = tk.Frame(self.frame_manual, bg=C.SUPERFICIE)
        frame_botones_filas.pack(fill="x", pady=(6, 0))

        tk.Button(
            frame_botones_filas, text="+ Agregar dato", font=fuente(9, "bold"),
            bg=C.PRIMARIO, fg="white", cursor="hand2",
            command=self._agregar_fila_manual,
        ).pack(side="left")

        tk.Button(
            frame_botones_filas, text="− Quitar última fila", font=fuente(9),
            bg=C.TEXTO_TENUE, fg="white", cursor="hand2",
            command=self._quitar_fila_manual,
        ).pack(side="left", padx=(6, 0))

        tk.Label(
            self.frame_manual,
            text="Puede dejar filas en blanco si no las necesita; con 2 datos completos alcanza.",
            font=fuente(8, "italic"), bg=C.SUPERFICIE, fg=C.TEXTO_SECUNDARIO,
            anchor="w", justify="left", wraplength=320,
        ).pack(fill="x", pady=(4, 0))

    # ------------------------------------------------------------------
    def _agregar_fila_manual(self):
        """Agrega una nueva fila (año, población) al panel de ingreso manual."""
        fila = tk.Frame(self.frame_filas_manual, bg=C.SUPERFICIE)
        fila.pack(fill="x", pady=2)
        e_año = ttk.Entry(fila, width=13)
        e_año.pack(side="left", padx=(0, 4))
        e_pob = ttk.Entry(fila, width=16)
        e_pob.pack(side="left")
        self.entries_manual.append((e_año, e_pob))

    # ------------------------------------------------------------------
    def _quitar_fila_manual(self):
        """Quita la última fila del panel de ingreso manual (mínimo 2 filas visibles)."""
        if len(self.entries_manual) <= 2:
            return
        e_año, e_pob = self.entries_manual.pop()
        e_año.master.destroy()  # destruye el Frame contenedor de esa fila

    # ------------------------------------------------------------------
    def _crear_panel_tasa(self, padre):
        """Panel de la fuente 'Año censal + tasa de crecimiento'."""
        self.frame_tasa = tk.Frame(padre, bg=C.SUPERFICIE)

        tk.Label(self.frame_tasa, text="✎ Año del dato base (dato editable):",
                 font=fuente(10, "bold"), bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO,
                 anchor="w").pack(fill="x", pady=(10, 2))
        self.entry_año_censo = ttk.Entry(self.frame_tasa, width=32)
        self.entry_año_censo.pack(fill="x")

        tk.Label(self.frame_tasa, text="✎ Población en ese año (dato editable):",
                 font=fuente(10, "bold"), bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO,
                 anchor="w").pack(fill="x", pady=(10, 2))
        self.entry_pob_censo = ttk.Entry(self.frame_tasa, width=32)
        self.entry_pob_censo.pack(fill="x")

        tk.Label(self.frame_tasa, text="✎ Tasa de crecimiento anual, % (dato editable):",
                 font=fuente(10, "bold"), bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO,
                 anchor="w").pack(fill="x", pady=(10, 2))
        self.entry_tasa = ttk.Entry(self.frame_tasa, width=32)
        self.entry_tasa.pack(fill="x")

    # ------------------------------------------------------------------
    def _cambiar_fuente(self, event=None):
        """Muestra el panel correspondiente y habilita/bloquea depto-municipio
        según si la fuente elegida usa o no la base de datos DANE."""
        fuente = self.cb_fuente.get()

        self.frame_area.pack_forget()
        self.frame_manual.pack_forget()
        self.frame_tasa.pack_forget()

        if fuente == FUENTE_DANE:
            self.cb_depto.config(state="readonly")
            self.cb_municipio.config(state="readonly")
            self.frame_area.pack(fill="x")
        elif fuente == FUENTE_MANUAL:
            self.cb_depto.config(state="normal")
            self.cb_municipio.config(state="normal")
            self.frame_manual.pack(fill="x")
        else:  # FUENTE_TASA
            self.cb_depto.config(state="normal")
            self.cb_municipio.config(state="normal")
            self.frame_tasa.pack(fill="x")

    # ------------------------------------------------------------------
    def _crear_panel_resultados(self, padre):
        frame_buscar = tk.Frame(padre, bg=C.SUPERFICIE)
        frame_buscar.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(frame_buscar, text="Ver población en el año:",
                 font=fuente(9, "bold"), bg=C.SUPERFICIE).pack(side="left")
        self.entry_buscar_año = ttk.Entry(frame_buscar, width=8)
        self.entry_buscar_año.pack(side="left", padx=6)
        tk.Button(frame_buscar, text="Buscar", font=fuente(9, "bold"),
                  bg=C.PRIMARIO_SUAVE, fg=C.PRIMARIO, padx=12, pady=4,
                  command=self.buscar_año, cursor="hand2").pack(side="left")
        self.lbl_resultado_busqueda = tk.Label(
            frame_buscar, text="", font=fuente(9, "bold"),
            fg=C.RESULTADO_TEXTO, bg=C.SUPERFICIE,
        )
        self.lbl_resultado_busqueda.pack(side="left", padx=12)

        frame_tabla = tk.Frame(padre)
        frame_tabla.pack(fill="x", padx=20, pady=14)

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical")
        self.tabla = ttk.Treeview(
            frame_tabla, columns=("año", "arit", "geom", "exp", "tipo"), show="headings",
            height=7, yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tabla.yview)

        for col, texto, ancho in [
            ("año", "Año", 65), ("arit", "Aritmético", 100),
            ("geom", "Geométrico", 100), ("exp", "Exponencial", 100),
            ("tipo", "Tipo", 95),
        ]:
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="center")

        self.tabla.pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.figura = Figure(figsize=(6.2, 3.9), dpi=90)
        self.ax = self.figura.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figura, master=padre)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 5))

        btn_exportar = tk.Button(
            padre, text="📷 Exportar gráfica como imagen", font=fuente(9, "bold"),
            bg=C.TEXTO_SECUNDARIO, fg="white", cursor="hand2",
            command=self.exportar_grafica,
        )
        btn_exportar.pack(fill="x", padx=20, pady=(0, 18), ipady=4)

    # ------------------------------------------------------------------
    def _al_cambiar_depto(self, event=None):
        dpnom = self.cb_depto.get()
        municipios = datos_dane.obtener_municipios(dpnom)
        self.cb_municipio["values"] = municipios
        if municipios:
            self.cb_municipio.current(0)

    # ------------------------------------------------------------------
    def _tasas_desde_serie(self, puntos):
        """
        A partir de una serie de datos poblacionales [(año, población), ...]
        (2 o más puntos), calcula la tasa/coeficiente de cada uno de los 3
        métodos de proyección PROMEDIANDO las tasas de cada PAR DE AÑOS
        CONSECUTIVOS — no solo la del primer y el último dato.

        Ejemplo con 2018, 2019, 2020, 2021...: se calcula la tasa entre
        (2018,2019), luego entre (2019,2020), luego entre (2020,2021), etc.,
        y al final se promedian todas esas tasas parciales. Así se usan
        TODOS los datos intermedios, no solo los dos extremos.

        El método exponencial NO calcula su propia tasa por separado: usa
        la MISMA tasa geométrica promediada como exponente directo
        (P = pu·e^(tasa·(t-tu))), igual que en la fuente "censo + tasa".
        Así lo confirmó el usuario con su ejemplo de calculadora.

        Devuelve (r_arit, r_geom, k_exp, pu, tu):
            - r_arit, r_geom: tasas promediadas (redondeadas).
            - k_exp: la misma tasa que r_geom (se usa igual como exponente
              del método exponencial, sin transformación logarítmica).
            - pu, tu: población y año del dato más reciente de la serie,
              que se usa como punto de referencia para proyectar hacia
              adelante (año_inicio, año_inicio+1, ...).
        """
        puntos = sorted(puntos, key=lambda par: par[0])
        if len(puntos) < 2:
            raise ValueError("Se requieren al menos 2 datos para calcular la tasa de crecimiento.")

        tasas_arit, tasas_geom = [], []
        for (t_a, p_a), (t_b, p_b) in zip(puntos, puntos[1:]):
            if t_b == t_a:
                raise ValueError("Los años ingresados deben ser diferentes entre sí.")
            dt = t_b - t_a
            tasas_arit.append((p_b - p_a) / dt)
            tasas_geom.append((p_b / p_a) ** (1 / dt) - 1)

        # Redondeo del promedio final de cada tasa (no de las tasas parciales
        # de cada par de años, sino del promedio ya calculado):
        #   - Aritmético: 0 decimales (incremento de habitantes/año)
        #   - Geométrico: 3 decimales
        # El exponencial reutiliza la tasa geométrica (misma "tasa" en las
        # tres fórmulas del usuario), sin volver a calcularla ni transformarla.
        r_arit = round(sum(tasas_arit) / len(tasas_arit))
        r_geom = round(sum(tasas_geom) / len(tasas_geom), 3)
        k_exp = r_geom

        tu, pu = puntos[-1]
        return r_arit, r_geom, k_exp, pu, tu

    def _tasas_desde_censo_y_tasa(self, pu, tasa):
        """
        A partir de una población base (pu) y una tasa de crecimiento anual
        (tasa, en decimal), deriva la tasa/coeficiente de cada uno de los 3
        métodos de proyección. Usado por la fuente 'Año censal + tasa de
        crecimiento':
            - Geométrico: la tasa tal cual.
            - Aritmético: incremento anual equivalente = Población × tasa.
            - Exponencial: tasa continua equivalente = ln(1 + tasa).
        """
        # A diferencia de _tasas_desde_serie, aquí la tasa geométrica NO se
        # calcula a partir de una serie de datos: la entrega directamente
        # el usuario, así que se usa tal cual, sin redondear, y también se
        # usa tal cual (sin la conversión ln(1+tasa)) como exponente del
        # método exponencial — así lo confirmó el usuario con su ejemplo
        # de calculadora.
        r_geom = tasa
        r_arit = pu * tasa
        k_exp = tasa
        return r_arit, r_geom, k_exp

    # ------------------------------------------------------------------
    def calcular_proyeccion(self):
        fuente = self.cb_fuente.get()

        try:
            año_inicio = int(self.entry_año_inicio.get())
            periodo = int(self.entry_periodo.get())
            if periodo <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Año de inicio y periodo deben ser números enteros válidos.")
            return

        historico = None  # solo se llena para la fuente DANE (datos reales antes del año de inicio)

        try:
            if fuente == FUENTE_DANE:
                dpnom = self.cb_depto.get()
                mpio = self.cb_municipio.get()
                area = self.cb_area.get()
                if not (dpnom and mpio and area):
                    messagebox.showwarning("Faltan datos", "Seleccione departamento, municipio y área.")
                    return

                datos = datos_dane.obtener_datos_municipio(dpnom, mpio, area)
                if datos.empty:
                    messagebox.showerror("Sin datos", "No hay datos DANE para esa combinación.")
                    return

                serie_censo = datos_dane.obtener_serie_censo(datos)
                if len(serie_censo) < 2:
                    messagebox.showerror(
                        "Sin datos suficientes",
                        f"No hay suficientes datos entre {datos_dane.AÑO_CENSO_DESDE} y "
                        f"{datos_dane.AÑO_CENSO_HASTA} para esa combinación.",
                    )
                    return
                puntos = [
                    (int(fila["AÑO"]), int(fila["TOTAL"]))
                    for _, fila in serie_censo.iterrows()
                ]
                r_arit, r_geom, k_exp, pu, tu = self._tasas_desde_serie(puntos)

                # Todos los años con dato real en la BD anteriores al año de inicio:
                # se muestran tal cual (no se proyectan). Solo año_inicio en
                # adelante se calcula con las 3 fórmulas de proyección.
                historico = datos[datos["AÑO"] < año_inicio].sort_values("AÑO")

            elif fuente == FUENTE_MANUAL:
                puntos = []
                for e_año, e_pob in self.entries_manual:
                    texto_año = e_año.get().strip()
                    texto_pob = e_pob.get().strip()
                    if not texto_año and not texto_pob:
                        continue  # fila vacía: se ignora, no es obligatorio llenarla
                    if not texto_año or not texto_pob:
                        raise ValueError(
                            "Cada fila debe tener año y población juntos "
                            "(no puede dejar solo uno de los dos)."
                        )
                    puntos.append((int(texto_año), int(texto_pob)))

                if len(puntos) < 2:
                    raise ValueError("Ingrese al menos 2 datos censales (año y población).")

                if len({a for a, _ in puntos}) != len(puntos):
                    raise ValueError("Los años ingresados deben ser diferentes entre sí.")

                r_arit, r_geom, k_exp, pu, tu = self._tasas_desde_serie(puntos)

            else:  # FUENTE_TASA
                tu = int(self.entry_año_censo.get())
                pu = int(self.entry_pob_censo.get())
                tasa = float(self.entry_tasa.get()) / 100
                r_arit, r_geom, k_exp = self._tasas_desde_censo_y_tasa(pu, tasa)

        except ValueError as e:
            mensaje = str(e) if str(e) else "Revise los datos ingresados: deben ser números válidos."
            messagebox.showwarning("Datos inválidos", mensaje)
            return

        self._generar_proyeccion(pu, tu, r_arit, r_geom, k_exp, año_inicio, periodo, historico=historico)

    # ------------------------------------------------------------------
    def _generar_proyeccion(self, pu, tu, r_arit, r_geom, k_exp, año_inicio, periodo, historico=None):
        """Construye la tabla de proyección.

        Si se entrega 'historico' (DataFrame con columnas AÑO y TOTAL,
        años anteriores al año de inicio tomados directamente de la base
        de datos DANE), esos años se incluyen con su valor REAL —igual en
        las 3 columnas— y se marcan como "Histórico (BD)". Solo los años
        desde año_inicio en adelante se calculan con las 3 fórmulas de
        proyección y se marcan como "Proyectado". Para las fuentes que no
        entregan histórico (manual / tasa) se conserva el comportamiento
        original: toda la tabla es proyectada.
        """
        filas = []

        if historico is not None and not historico.empty:
            for _, fila_h in historico.iterrows():
                año_h = int(fila_h["AÑO"])
                valor_h = round(float(fila_h["TOTAL"]))
                filas.append({
                    "AÑO": año_h,
                    "Aritmético": valor_h,
                    "Geométrico": valor_h,
                    "Exponencial": valor_h,
                    "Tipo": "Histórico (BD)",
                })

        años_proy = list(range(año_inicio, año_inicio + periodo + 1))
        for t in años_proy:
            arit = pu + r_arit * (t - tu)
            geom = pu * (1 + r_geom) ** (t - tu)
            exp_ = pu * math.exp(k_exp * (t - tu))
            filas.append({
                "AÑO": t,
                "Aritmético": round(arit),
                "Geométrico": round(geom),
                "Exponencial": round(exp_),
                "Tipo": "Proyectado",
            })

        self.df_proyeccion = pd.DataFrame(filas)

        # Tabla completa (todos los años, con scroll)
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for f in filas:
            self.tabla.insert(
                "", "end",
                values=(
                    f["AÑO"], f'{f["Aritmético"]:,}', f'{f["Geométrico"]:,}',
                    f'{f["Exponencial"]:,}', f["Tipo"],
                ),
            )

        self.lbl_resultado_busqueda.config(text="")

        # Gráfica
        self._elementos_resaltado = []
        self.ax.clear()
        self.ax.plot(self.df_proyeccion["AÑO"], self.df_proyeccion["Aritmético"], marker="o", markersize=3, label="Aritmético")
        self.ax.plot(self.df_proyeccion["AÑO"], self.df_proyeccion["Geométrico"], marker="s", markersize=3, label="Geométrico")
        self.ax.plot(self.df_proyeccion["AÑO"], self.df_proyeccion["Exponencial"], marker="^", markersize=3, label="Exponencial")

        # Marca la frontera entre el dato real (histórico) y lo proyectado
        if historico is not None and not historico.empty:
            self.ax.axvline(año_inicio, color="#7F8C8D", linestyle=":", linewidth=1.2)
            self.ax.annotate(
                "Inicio del proyecto\n(datos reales → proyección)",
                xy=(año_inicio, self.ax.get_ylim()[0]),
                xytext=(4, 6),
                textcoords="offset points",
                fontsize=7,
                color=C.TEXTO_SECUNDARIO,
            )

        self.ax.set_xlabel("Año")
        self.ax.set_ylabel("Población")
        self.ax.set_title("Proyección poblacional")
        self.ax.legend(fontsize=8)
        self.ax.grid(True, linestyle="--", alpha=0.5)
        self.figura.tight_layout()
        self.canvas.draw()

        self._año_horizonte = años_proy[-1]
        self._poblacion_inicial = pu
        self._actualizar_poblacion_diseño()

    # ------------------------------------------------------------------
    def exportar_grafica(self):
        if self.df_proyeccion is None:
            messagebox.showwarning("Falta calcular", "Primero calcule la proyección poblacional.")
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar gráfica como imagen",
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png"), ("Imagen JPEG", "*.jpg")],
            initialfile="proyeccion_poblacional.png",
        )
        if not ruta:
            return

        self.figura.savefig(ruta, dpi=200, bbox_inches="tight")
        messagebox.showinfo("Gráfica exportada", f"Gráfica guardada en:\n{ruta}")

    # ------------------------------------------------------------------
    def buscar_año(self):
        if self.df_proyeccion is None:
            messagebox.showwarning("Falta calcular", "Primero calcule la proyección poblacional.")
            return

        try:
            año_buscado = int(self.entry_buscar_año.get())
        except ValueError:
            messagebox.showwarning("Año inválido", "Ingrese un año numérico.")
            return

        fila = self.df_proyeccion[self.df_proyeccion["AÑO"] == año_buscado]
        if fila.empty:
            self.lbl_resultado_busqueda.config(
                text=f"Año {año_buscado} fuera del rango proyectado.", fg=C.PELIGRO
            )
            for elem in self._elementos_resaltado:
                elem.remove()
            self._elementos_resaltado = []
            self.canvas.draw()
            return

        arit = fila.iloc[0]["Aritmético"]
        geom = fila.iloc[0]["Geométrico"]
        exp_ = fila.iloc[0]["Exponencial"]
        self.lbl_resultado_busqueda.config(
            text=f"{año_buscado} → Arit: {arit:,.0f} | Geom: {geom:,.0f} | Exp: {exp_:,.0f}",
            fg=C.RESULTADO_TEXTO,
        )

        # Ubicar y seleccionar la fila correspondiente en la tabla
        for item in self.tabla.get_children():
            valores = self.tabla.item(item, "values")
            if str(valores[0]) == str(año_buscado):
                self.tabla.selection_set(item)
                self.tabla.see(item)
                break

        self._resaltar_año_en_grafica(año_buscado, arit, geom, exp_)

    # ------------------------------------------------------------------
    def _resaltar_año_en_grafica(self, año, arit, geom, exp_):
        # Quitar el resaltado anterior
        for elem in self._elementos_resaltado:
            elem.remove()
        self._elementos_resaltado = []

        linea_v = self.ax.axvline(año, color="#7F8C8D", linestyle="--", linewidth=1)
        self._elementos_resaltado.append(linea_v)

        for valor, color in [(arit, "#1F77B4"), (geom, "#FF7F0E"), (exp_, "#2CA02C")]:
            punto, = self.ax.plot(año, valor, marker="o", markersize=10,
                                   markerfacecolor=color, markeredgecolor=C.TEXTO,
                                   markeredgewidth=1.2, zorder=5)
            self._elementos_resaltado.append(punto)

        etiqueta = self.ax.annotate(
            f"{año}",
            xy=(año, geom),
            xytext=(0, 15),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#F9E79F", ec="#B7950B"),
        )
        self._elementos_resaltado.append(etiqueta)

        self.canvas.draw()

    # ------------------------------------------------------------------
    def _actualizar_poblacion_diseño(self, event=None):
        if self.df_proyeccion is None:
            return
        metodo = self.cb_metodo_diseño.get()
        valor = self.df_proyeccion.iloc[-1][metodo]
        self.lbl_poblacion_diseño.config(
            text=f"Población de diseño ({self._año_horizonte}, {metodo}):\n{valor:,.0f} hab."
        )

    # ------------------------------------------------------------------
    def guardar(self):
        if self.df_proyeccion is None:
            messagebox.showwarning("Falta calcular", "Primero calcule la proyección poblacional.")
            return

        metodo = self.cb_metodo_diseño.get()
        fuente = self.cb_fuente.get()

        EstadoProyecto.departamento = self.cb_depto.get()
        EstadoProyecto.municipio = self.cb_municipio.get()
        EstadoProyecto.area_geografica = self.cb_area.get() if fuente == FUENTE_DANE else f"N/A ({fuente})"
        EstadoProyecto.año_inicio = int(self.entry_año_inicio.get())
        EstadoProyecto.periodo_diseño = int(self.entry_periodo.get())
        EstadoProyecto.año_horizonte = self._año_horizonte
        EstadoProyecto.metodo_diseño = metodo
        EstadoProyecto.poblacion_inicial = self._poblacion_inicial
        EstadoProyecto.poblacion_diseño = float(self.df_proyeccion.iloc[-1][metodo])
        EstadoProyecto.tabla_proyeccion = self.df_proyeccion

        messagebox.showinfo("Datos guardados", "Los datos preliminares se guardaron correctamente.\n\n" + EstadoProyecto.resumen())

        if self.al_guardar:
            self.al_guardar()

        self.destroy()
