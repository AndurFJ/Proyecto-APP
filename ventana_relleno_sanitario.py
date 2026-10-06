"""
Ventana de Diseño de Operación de Relleno Sanitario (DORS).

Primer paso del diseño de un relleno sanitario: el cálculo poblacional
a 50 años, igual que la hoja de cálculo DORS (ver relleno_sanitario.py
para las fórmulas). Es independiente de los Datos Preliminares de
PTAP/PTAR: guarda sus resultados en los campos rs_* de EstadoProyecto.

Todos los colores y fuentes están en COLORES y FUENTES, al inicio del
archivo, para poder cambiar el estilo de la ventana en un solo lugar.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import datos_dane
import relleno_sanitario as rs
from estado_proyecto import EstadoProyecto
from ui_utils import ajustar_geometria, hacer_scrollable


COLORES = {
    "fondo": "#F2F4F4",
    "panel": "white",
    "encabezado": "#1F4E78",
    "encabezado_texto": "white",
    "encabezado_sub": "#D9E1F2",
    "editable": "#B9770E",
    "texto": "#1B2631",
    "texto_suave": "#5D6D7E",
    "resultado": "#1B4F72",
    "aviso": "#C0392B",
    "boton_calcular": "#2E86C1",
    "boton_guardar": "#28B463",
    "boton_secundario": "#5D6D7E",
    "boton_suave": "#AAB7C4",
    "ok_fondo": "#EAFAF1",
    "ok_texto": "#1E8449",
    "serie": {"Aritmético": "#1F77B4", "Geométrico": "#FF7F0E", "Exponencial": "#2CA02C"},
}

FUENTES = {
    "titulo": ("Arial", 14, "bold"),
    "subtitulo": ("Arial", 8, "italic"),
    "seccion": ("Arial", 10, "bold"),
    "normal": ("Arial", 9),
    "negrita": ("Arial", 9, "bold"),
    "nota": ("Arial", 8, "italic"),
    "boton": ("Arial", 11, "bold"),
    "resultado": ("Arial", 12, "bold"),
}

AREAS = ["Cabecera Municipal", "Centros Poblados y Rural Disperso", "Total"]
FILAS_MANUALES_INICIALES = 5


class VentanaRellenoSanitario(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Relleno Sanitario — Cálculo poblacional (DORS)")
        self.resizable(True, True)
        ajustar_geometria(self, ancho=1120, alto=780)
        self.configure(bg=COLORES["fondo"])

        self.al_guardar = al_guardar
        self.params = None
        self.df_proyeccion = None
        self.filas_manual = []  # [(entry_año, entry_pob, lbl_dane), ...]

        self._crear_widgets()
        self._precargar()

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        tk.Label(
            self, text="RELLENO SANITARIO — Cálculo poblacional",
            font=FUENTES["titulo"], bg=COLORES["encabezado"],
            fg=COLORES["encabezado_texto"], pady=10,
        ).pack(fill="x")
        tk.Label(
            self, text="Diseño de Operación de Relleno Sanitario (DORS) — proyección a "
                       f"{rs.AÑOS_PROYECCION} años por los métodos aritmético, geométrico y exponencial",
            font=FUENTES["subtitulo"], bg=COLORES["encabezado"],
            fg=COLORES["encabezado_sub"], pady=4,
        ).pack(fill="x")

        cuerpo = tk.Frame(self, bg=COLORES["fondo"])
        cuerpo.pack(fill="both", expand=True, padx=15, pady=10)

        # Panel izquierdo con scroll (entradas)
        izq = tk.Frame(cuerpo, bg=COLORES["fondo"], width=360)
        izq.pack(side="left", fill="y", padx=(0, 15))
        izq.pack_propagate(False)

        canvas = tk.Canvas(izq, bg=COLORES["fondo"], highlightthickness=0)
        barra = ttk.Scrollbar(izq, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=barra.set)
        canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        panel_entradas = tk.Frame(canvas, bg=COLORES["fondo"])
        hacer_scrollable(canvas, panel_entradas)

        der = tk.Frame(cuerpo, bg=COLORES["panel"], bd=1, relief="solid")
        der.pack(side="right", fill="both", expand=True)

        self._crear_panel_entradas(panel_entradas)
        self._crear_panel_resultados(der)

    # ------------------------------------------------------------------
    def _etiqueta(self, padre, texto, editable=False):
        tk.Label(
            padre, text=f"✎ {texto}" if editable else texto,
            font=FUENTES["seccion"], bg=COLORES["fondo"],
            fg=COLORES["editable"] if editable else COLORES["texto"],
            anchor="w", justify="left", wraplength=320,
        ).pack(fill="x", pady=(10, 2), padx=(0, 8))

    def _nota(self, padre, texto, color=None):
        lbl = tk.Label(
            padre, text=texto, font=FUENTES["nota"], bg=COLORES["fondo"],
            fg=color or COLORES["texto_suave"], anchor="w", justify="left", wraplength=320,
        )
        lbl.pack(fill="x", pady=(2, 0), padx=(0, 8))
        return lbl

    def _boton(self, padre, texto, color, comando, fuente=None):
        return tk.Button(
            padre, text=texto, font=fuente or FUENTES["boton"], bg=color, fg="white",
            activebackground=color, bd=0, cursor="hand2", command=comando,
        )

    # ------------------------------------------------------------------
    def _crear_panel_entradas(self, padre):
        self._etiqueta(padre, "1. Método de cálculo:", editable=True)
        self.var_metodo = tk.IntVar(value=rs.METODO_DANE)
        for numero, nombre in rs.NOMBRES_METODO.items():
            tk.Radiobutton(
                padre, text=f"{numero} · {nombre}", variable=self.var_metodo, value=numero,
                font=FUENTES["normal"], bg=COLORES["fondo"], anchor="w",
                activebackground=COLORES["fondo"], command=self._cambiar_metodo,
            ).pack(fill="x")

        self._etiqueta(padre, "2. Departamento:", editable=True)
        self.cb_depto = ttk.Combobox(padre, values=datos_dane.obtener_departamentos(), state="readonly")
        self.cb_depto.pack(fill="x", padx=(0, 8))
        self.cb_depto.bind("<<ComboboxSelected>>", self._al_cambiar_depto)

        self._etiqueta(padre, "3. Municipio:", editable=True)
        self.cb_municipio = ttk.Combobox(padre, values=[], state="readonly")
        self.cb_municipio.pack(fill="x", padx=(0, 8))
        self.cb_municipio.bind("<<ComboboxSelected>>", lambda e: self._actualizar_referencias_dane())

        self._etiqueta(padre, "4. Área geográfica:", editable=True)
        self.cb_area = ttk.Combobox(padre, values=AREAS, state="readonly")
        self.cb_area.current(2)
        self.cb_area.pack(fill="x", padx=(0, 8))
        self.cb_area.bind("<<ComboboxSelected>>", lambda e: self._actualizar_referencias_dane())

        # --- Año de inicio (métodos 1 y 2) ---
        self.frame_año_inicio = tk.Frame(padre, bg=COLORES["fondo"])
        self._etiqueta(self.frame_año_inicio, "5a. Año de inicio del proyecto:", editable=True)
        self.entry_año_inicio = ttk.Entry(self.frame_año_inicio)
        self.entry_año_inicio.insert(0, "2030")
        self.entry_año_inicio.pack(fill="x", padx=(0, 8))
        self.entry_año_inicio.bind("<FocusOut>", lambda e: self._actualizar_aviso())

        self.contenedor_metodo = tk.Frame(padre, bg=COLORES["fondo"])
        self._crear_panel_manual(self.contenedor_metodo)
        self._crear_panel_tasa(self.contenedor_metodo)

        self.lbl_aviso = self._nota(padre, "", color=COLORES["aviso"])

        self._boton(padre, "Calcular proyección", COLORES["boton_calcular"],
                    self.calcular).pack(fill="x", pady=(16, 8), padx=(0, 8), ipady=6)

        self._etiqueta(padre, "Método adoptado para el diseño:", editable=True)
        self.cb_metodo_adoptado = ttk.Combobox(padre, values=rs.COLUMNAS_PROYECCION, state="readonly")
        self.cb_metodo_adoptado.current(1)
        self.cb_metodo_adoptado.pack(fill="x", padx=(0, 8))
        self.cb_metodo_adoptado.bind("<<ComboboxSelected>>", lambda e: self._actualizar_resultado())

        self.marco_resultado = tk.Frame(
            padre, bg=COLORES["ok_fondo"], highlightbackground=COLORES["ok_texto"],
            highlightthickness=2,
        )
        self.marco_resultado.pack(fill="x", pady=(12, 0), padx=(0, 8))
        self.lbl_resultado = tk.Label(
            self.marco_resultado, text="Población al final del horizonte: —",
            font=FUENTES["resultado"], bg=COLORES["ok_fondo"], fg=COLORES["ok_texto"],
            justify="center", wraplength=320, pady=8,
        )
        self.lbl_resultado.pack(fill="x")

        self._boton(padre, "Guardar y continuar", COLORES["boton_guardar"],
                    self.guardar).pack(fill="x", pady=(16, 16), padx=(0, 8), ipady=6)

        self._cambiar_metodo()

    # ------------------------------------------------------------------
    def _crear_panel_manual(self, padre):
        self.frame_manual = tk.Frame(padre, bg=COLORES["fondo"])
        self._etiqueta(self.frame_manual, "6. Datos censales (mínimo 2, sin máximo):", editable=True)
        self._nota(self.frame_manual,
                   "Se usan el dato más reciente (Tu, Pu) y el más antiguo (T1, P1). "
                   "La columna DANE es solo referencia del municipio y área elegidos.")

        cabecera = tk.Frame(self.frame_manual, bg=COLORES["fondo"])
        cabecera.pack(fill="x", pady=(6, 0))
        for texto, ancho in [("Año", 9), ("Población", 13), ("DANE (ref.)", 12)]:
            tk.Label(cabecera, text=texto, width=ancho, font=FUENTES["negrita"],
                     bg=COLORES["fondo"], anchor="w").pack(side="left")

        self.frame_filas = tk.Frame(self.frame_manual, bg=COLORES["fondo"])
        self.frame_filas.pack(fill="x")
        for _ in range(FILAS_MANUALES_INICIALES):
            self._agregar_fila()

        botones = tk.Frame(self.frame_manual, bg=COLORES["fondo"])
        botones.pack(fill="x", pady=(6, 0))
        self._boton(botones, "+ Agregar dato", COLORES["boton_calcular"],
                    self._agregar_fila, FUENTES["negrita"]).pack(side="left", ipadx=4)
        self._boton(botones, "− Quitar última fila", COLORES["boton_suave"],
                    self._quitar_fila, FUENTES["normal"]).pack(side="left", padx=6, ipadx=4)

    def _agregar_fila(self):
        fila = tk.Frame(self.frame_filas, bg=COLORES["fondo"])
        fila.pack(fill="x", pady=2)
        e_año = ttk.Entry(fila, width=9)
        e_año.pack(side="left", padx=(0, 4))
        e_pob = ttk.Entry(fila, width=13)
        e_pob.pack(side="left", padx=(0, 4))
        lbl = tk.Label(fila, text="", width=12, font=FUENTES["normal"],
                       bg=COLORES["fondo"], fg=COLORES["texto_suave"], anchor="w")
        lbl.pack(side="left")
        e_año.bind("<FocusOut>", lambda e: self._actualizar_referencias_dane())
        self.filas_manual.append((e_año, e_pob, lbl))

    def _quitar_fila(self):
        if len(self.filas_manual) <= 2:
            return
        e_año, _, _ = self.filas_manual.pop()
        e_año.master.destroy()

    # ------------------------------------------------------------------
    def _crear_panel_tasa(self, padre):
        self.frame_tasa = tk.Frame(padre, bg=COLORES["fondo"])
        self._etiqueta(self.frame_tasa, "5b. Año base del censo:", editable=True)
        self.entry_año_base = ttk.Entry(self.frame_tasa)
        self.entry_año_base.pack(fill="x", padx=(0, 8))
        self._etiqueta(self.frame_tasa, "5c. Tasa de crecimiento anual (%):", editable=True)
        self.entry_tasa = ttk.Entry(self.frame_tasa)
        self.entry_tasa.pack(fill="x", padx=(0, 8))
        self._etiqueta(self.frame_tasa, "5d. Población en el año base (hab):", editable=True)
        self.entry_pob_base = ttk.Entry(self.frame_tasa)
        self.entry_pob_base.pack(fill="x", padx=(0, 8))
        self._nota(self.frame_tasa, "Con este método la proyección empieza en el año base del censo.")

    # ------------------------------------------------------------------
    def _crear_panel_resultados(self, padre):
        tk.Label(padre, text="Cálculos internos", font=FUENTES["seccion"],
                 bg=COLORES["panel"], fg=COLORES["texto"], anchor="w").pack(fill="x", padx=10, pady=(10, 0))
        self.lbl_parametros = tk.Label(
            padre, text="Calcule la proyección para ver los datos base usados.",
            font=FUENTES["normal"], bg=COLORES["panel"], fg=COLORES["resultado"],
            anchor="w", justify="left",
        )
        self.lbl_parametros.pack(fill="x", padx=10, pady=(2, 6))

        marco_tabla = tk.Frame(padre, bg=COLORES["panel"])
        marco_tabla.pack(fill="x", padx=10)
        barra = ttk.Scrollbar(marco_tabla, orient="vertical")
        self.tabla = ttk.Treeview(
            marco_tabla, columns=("año", "arit", "geom", "exp"), show="headings",
            height=8, yscrollcommand=barra.set,
        )
        barra.config(command=self.tabla.yview)
        for col, texto in [("año", "Año"), ("arit", "Aritmético"),
                           ("geom", "Geométrico"), ("exp", "Exponencial")]:
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=110, anchor="center")
        self.tabla.pack(side="left", fill="x", expand=True)
        barra.pack(side="right", fill="y")

        # El botón se empaca antes que la gráfica para que esta no lo tape.
        self._boton(padre, "📷 Exportar gráfica como imagen", COLORES["boton_secundario"],
                    self.exportar_grafica, FUENTES["negrita"]).pack(
                        side="bottom", fill="x", padx=10, pady=(0, 10), ipady=3)

        self.figura = Figure(figsize=(6.4, 3.6), dpi=90)
        self.ax = self.figura.add_subplot(111)
        self._dibujar_grafica()
        self.canvas_grafica = FigureCanvasTkAgg(self.figura, master=padre)
        self.canvas_grafica.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(8, 4))

    # ------------------------------------------------------------------
    def _cambiar_metodo(self):
        metodo = self.var_metodo.get()
        self.frame_año_inicio.pack_forget()
        self.frame_manual.pack_forget()
        self.frame_tasa.pack_forget()
        self.contenedor_metodo.pack_forget()

        if metodo in (rs.METODO_DANE, rs.METODO_MANUAL):
            self.frame_año_inicio.pack(fill="x", before=self.lbl_aviso)
        # Un Frame vacío conserva su último tamaño en Tk: solo se empaca
        # cuando va a contener el panel del método 2 o del 3.
        if metodo != rs.METODO_DANE:
            self.contenedor_metodo.pack(fill="x", before=self.lbl_aviso)
        if metodo == rs.METODO_MANUAL:
            self.frame_manual.pack(fill="x")
            self._actualizar_referencias_dane()
        elif metodo == rs.METODO_TASA:
            self.frame_tasa.pack(fill="x")
        self._actualizar_aviso()

    def _al_cambiar_depto(self, event=None):
        municipios = datos_dane.obtener_municipios(self.cb_depto.get())
        self.cb_municipio["values"] = municipios
        if municipios:
            self.cb_municipio.current(0)
        self._actualizar_referencias_dane()

    def _actualizar_aviso(self):
        texto = ""
        if self.var_metodo.get() == rs.METODO_DANE:
            try:
                texto = rs.aviso_metodo_dane(int(self.entry_año_inicio.get()))
            except ValueError:
                texto = ""
        self.lbl_aviso.config(text=texto)

    def _actualizar_referencias_dane(self):
        """Columna 'DANE (ref.)' del método 2, como la columna D del Excel."""
        dpnom, mpio, area = self.cb_depto.get(), self.cb_municipio.get(), self.cb_area.get()
        por_año = {}
        if dpnom and mpio and area:
            datos = datos_dane.obtener_datos_municipio(dpnom, mpio, area)
            por_año = dict(zip(datos["AÑO"].astype(int), datos["TOTAL"].astype(int)))
        for e_año, _, lbl in self.filas_manual:
            try:
                valor = por_año.get(int(e_año.get()))
            except ValueError:
                valor = None
            lbl.config(text=f"{valor:,}" if valor is not None else "")

    # ------------------------------------------------------------------
    def _leer_puntos_manuales(self):
        puntos = []
        for e_año, e_pob, _ in self.filas_manual:
            texto_año, texto_pob = e_año.get().strip(), e_pob.get().strip()
            if not texto_año and not texto_pob:
                continue
            if not texto_año or not texto_pob:
                raise ValueError("Cada fila debe tener año y población juntos.")
            puntos.append((int(texto_año), int(float(texto_pob))))
        return puntos

    def calcular(self):
        metodo = self.var_metodo.get()
        try:
            if metodo == rs.METODO_DANE:
                año_inicio = int(self.entry_año_inicio.get())
                dpnom, mpio, area = self.cb_depto.get(), self.cb_municipio.get(), self.cb_area.get()
                if not (dpnom and mpio and area):
                    raise ValueError("Seleccione departamento, municipio y área geográfica.")
                params = rs.parametros_metodo_dane(dpnom, mpio, area, año_inicio)
            elif metodo == rs.METODO_MANUAL:
                año_inicio = int(self.entry_año_inicio.get())
                params = rs.parametros_metodo_manual(self._leer_puntos_manuales())
            else:
                año_base = int(self.entry_año_base.get())
                params = rs.parametros_metodo_tasa(
                    año_base, float(self.entry_tasa.get()), int(float(self.entry_pob_base.get())),
                )
                año_inicio = año_base
        except ValueError as e:
            mensaje = str(e)
            if "invalid literal" in mensaje or "could not convert" in mensaje:
                mensaje = "Revise los datos ingresados: deben ser números válidos."
            messagebox.showwarning("Datos inválidos", mensaje, parent=self)
            return

        self.params = params
        self.df_proyeccion = rs.proyectar(params, rs.año_inicial_proyeccion(params, año_inicio))
        self._actualizar_aviso()
        self._mostrar_resultados()

    # ------------------------------------------------------------------
    def _mostrar_resultados(self):
        df = self.df_proyeccion
        partes = [f"{etq}: {val}" for etq, val in rs.descripcion_parametros(self.params)]
        self.lbl_parametros.config(
            text=f"Método {self.params['metodo']} · {rs.NOMBRES_METODO[self.params['metodo']]}\n"
                 + "   ".join(partes)
        )

        self.tabla.delete(*self.tabla.get_children())
        for _, fila in df.iterrows():
            self.tabla.insert("", "end", values=(
                int(fila["AÑO"]), f'{fila["Aritmético"]:,}',
                f'{fila["Geométrico"]:,}', f'{fila["Exponencial"]:,}',
            ))

        self._dibujar_grafica()
        self.canvas_grafica.draw()
        self._actualizar_resultado()

    def _dibujar_grafica(self):
        self.ax.clear()
        if self.df_proyeccion is not None:
            df = self.df_proyeccion
            # Con las fórmulas del DORS el geométrico y el exponencial dan
            # el mismo valor: el exponencial va punteado para que se vean ambos.
            for col, marcador, linea in zip(rs.COLUMNAS_PROYECCION, ["o", "s", "^"], ["-", "-", "--"]):
                self.ax.plot(df["AÑO"], df[col], marker=marcador, markersize=3, linestyle=linea,
                             label=col, color=COLORES["serie"][col])
            self.ax.legend(fontsize=8)
        self.ax.set_title("Proyección poblacional — comparación de métodos", fontsize=10)
        self.ax.set_xlabel("Año")
        self.ax.set_ylabel("Población proyectada (hab)")
        self.ax.grid(True, linestyle="--", alpha=0.5)
        self.figura.tight_layout()

    def _actualizar_resultado(self):
        if self.df_proyeccion is None:
            return
        metodo = self.cb_metodo_adoptado.get()
        inicio, final = self.df_proyeccion.iloc[0], self.df_proyeccion.iloc[-1]
        self.lbl_resultado.config(
            text=f"Población {int(inicio['AÑO'])}: {inicio[metodo]:,.0f} hab\n"
                 f"Población {int(final['AÑO'])}: {final[metodo]:,.0f} hab\n({metodo})"
        )

    # ------------------------------------------------------------------
    def exportar_grafica(self):
        if self.df_proyeccion is None:
            messagebox.showwarning("Falta calcular", "Primero calcule la proyección.", parent=self)
            return
        ruta = filedialog.asksaveasfilename(
            parent=self, title="Guardar gráfica como imagen", defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png"), ("Imagen JPEG", "*.jpg")],
            initialfile="proyeccion_relleno_sanitario.png",
        )
        if ruta:
            self.figura.savefig(ruta, dpi=200, bbox_inches="tight")
            messagebox.showinfo("Gráfica exportada", f"Gráfica guardada en:\n{ruta}", parent=self)

    # ------------------------------------------------------------------
    def _precargar(self):
        """Repone lo guardado antes; si no hay, toma la ubicación de los Datos Preliminares."""
        depto = EstadoProyecto.rs_departamento or EstadoProyecto.departamento
        mpio = EstadoProyecto.rs_municipio or EstadoProyecto.municipio
        if depto in self.cb_depto["values"]:
            self.cb_depto.set(depto)
            self._al_cambiar_depto()
            if mpio in self.cb_municipio["values"]:
                self.cb_municipio.set(mpio)
        if EstadoProyecto.rs_area in AREAS:
            self.cb_area.set(EstadoProyecto.rs_area)

        if not EstadoProyecto.relleno_definido():
            self._actualizar_referencias_dane()
            return

        params = EstadoProyecto.rs_parametros
        self.var_metodo.set(params["metodo"])
        if params["metodo"] == rs.METODO_TASA:
            self.entry_año_base.insert(0, str(params["t0"]))
            self.entry_tasa.insert(0, f"{params['r'] * 100:g}")
            self.entry_pob_base.insert(0, str(params["p0"]))
        else:
            self.entry_año_inicio.delete(0, "end")
            self.entry_año_inicio.insert(0, str(EstadoProyecto.rs_año_inicio))
        if params["metodo"] == rs.METODO_MANUAL:
            puntos = EstadoProyecto.rs_datos_censales or []
            while len(self.filas_manual) < len(puntos):
                self._agregar_fila()
            for (e_año, e_pob, _), (año, pob) in zip(self.filas_manual, puntos):
                e_año.insert(0, str(año))
                e_pob.insert(0, str(pob))
        self.cb_metodo_adoptado.set(EstadoProyecto.rs_metodo_adoptado)
        self._cambiar_metodo()

        self.params = params
        self.df_proyeccion = EstadoProyecto.rs_tabla_proyeccion
        self._mostrar_resultados()

    def guardar(self):
        if self.df_proyeccion is None:
            messagebox.showwarning("Falta calcular", "Primero calcule la proyección.", parent=self)
            return

        metodo = self.params["metodo"]
        final = self.df_proyeccion.iloc[-1]
        adoptado = self.cb_metodo_adoptado.get()

        if EstadoProyecto.relleno_diseno_definido():
            EstadoProyecto.borrar_relleno_diseno()
        EstadoProyecto.rs_departamento = self.cb_depto.get() or None
        EstadoProyecto.rs_municipio = self.cb_municipio.get() or None
        EstadoProyecto.rs_area = self.cb_area.get() or None
        EstadoProyecto.rs_parametros = dict(self.params)
        EstadoProyecto.rs_año_inicio = int(self.df_proyeccion.iloc[0]["AÑO"])
        EstadoProyecto.rs_datos_censales = (
            self._leer_puntos_manuales() if metodo == rs.METODO_MANUAL else None
        )
        EstadoProyecto.rs_tabla_proyeccion = self.df_proyeccion
        EstadoProyecto.rs_metodo_adoptado = adoptado
        EstadoProyecto.rs_año_horizonte = int(final["AÑO"])
        EstadoProyecto.rs_poblacion_diseño = float(final[adoptado])

        messagebox.showinfo(
            "Datos guardados",
            "El cálculo poblacional del relleno sanitario se guardó correctamente.\n\n"
            + EstadoProyecto.resumen_relleno(),
            parent=self,
        )
        if self.al_guardar:
            self.al_guardar()
        self.destroy()
