"""
Ventana de Diseño de Operación de Relleno Sanitario (DORS).

Primer paso del diseño de un relleno sanitario: el cálculo poblacional
a 50 años, igual que la hoja de cálculo DORS (ver relleno_sanitario.py
para las fórmulas). Es independiente de los Datos Preliminares de
PTAP/PTAR: guarda sus resultados en los campos rs_* de EstadoProyecto.

Los colores y fuentes salen del tema del software (tema.py); solo los
colores de las series de la gráfica están aquí, en COLORES_SERIE.
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
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria


# Colores de las líneas de la gráfica (los mismos de Datos Preliminares)
COLORES_SERIE = {"Aritmético": "#1F77B4", "Geométrico": "#FF7F0E", "Exponencial": "#2CA02C"}

AREAS = ["Cabecera Municipal", "Centros Poblados y Rural Disperso", "Total"]
FILAS_MANUALES_INICIALES = 5

# Ancho (px) del panel de datos de entrada y de sus textos
ANCHO_PANEL = 430
ANCHO_TEXTO = 360


class VentanaRellenoSanitario(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Relleno Sanitario — Cálculo poblacional (DORS)")
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)

        self.al_guardar = al_guardar
        self.params = None
        self.df_proyeccion = None
        self.filas_manual = []  # [(entry_año, entry_pob, lbl_dane), ...]

        self._crear_widgets()
        self._precargar()

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        tema.encabezado(
            self, "RELLENO SANITARIO — Cálculo poblacional",
            "Diseño de Operación de Relleno Sanitario (DORS) — proyección a "
            f"{rs.AÑOS_PROYECCION} años por los métodos aritmético, geométrico y exponencial",
        )

        cuerpo = tk.Frame(self, bg=C.FONDO)
        cuerpo.pack(fill="both", expand=True, padx=32, pady=24)

        # Panel izquierdo con scroll (entradas)
        izq = tema.tarjeta(cuerpo)
        izq.configure(width=ANCHO_PANEL)
        izq.pack(side="left", fill="y", padx=(0, 24))
        izq.pack_propagate(False)
        marco = tema.area_desplazable(izq, bg=C.SUPERFICIE)
        panel_entradas = tk.Frame(marco, bg=C.SUPERFICIE)
        panel_entradas.pack(fill="both", expand=True, padx=(22, 14), pady=(6, 10))

        der = tema.tarjeta(cuerpo)
        der.pack(side="right", fill="both", expand=True)

        self._crear_panel_entradas(panel_entradas)
        self._crear_panel_resultados(der)

    # ------------------------------------------------------------------
    def _etiqueta(self, padre, texto, editable=False):
        tk.Label(
            padre, text=f"✎ {texto}" if editable else texto,
            font=fuente(10, "bold"), bg=C.SUPERFICIE,
            fg=C.EDITABLE_TEXTO if editable else C.TEXTO,
            anchor="w", justify="left", wraplength=ANCHO_TEXTO,
        ).pack(fill="x", pady=(12, 3))

    def _nota(self, padre, texto, color=None):
        lbl = tk.Label(
            padre, text=texto, font=fuente(8, "italic"), bg=C.SUPERFICIE,
            fg=color or C.TEXTO_TENUE, anchor="w", justify="left", wraplength=ANCHO_TEXTO,
        )
        lbl.pack(fill="x", pady=(2, 0))
        return lbl

    def _boton(self, padre, texto, color, comando, fuente_boton=None, fg="white"):
        return tk.Button(
            padre, text=texto, font=fuente_boton or fuente(11, "bold"), bg=color, fg=fg,
            activebackground=color, activeforeground=fg, bd=0, cursor="hand2",
            padx=10, command=comando,
        )

    # ------------------------------------------------------------------
    def _crear_panel_entradas(self, padre):
        self._etiqueta(padre, "1. Método de cálculo:", editable=True)
        self.var_metodo = tk.IntVar(value=rs.METODO_DANE)
        for numero, nombre in rs.NOMBRES_METODO.items():
            tk.Radiobutton(
                padre, text=f"{numero} · {nombre}", variable=self.var_metodo, value=numero,
                font=fuente(10), bg=C.SUPERFICIE, fg=C.TEXTO, anchor="w", justify="left",
                wraplength=ANCHO_TEXTO - 30,
                activebackground=C.SUPERFICIE, selectcolor=C.SUPERFICIE,
                command=self._cambiar_metodo,
            ).pack(fill="x", pady=1)

        self._etiqueta(padre, "2. Departamento:", editable=True)
        self.cb_depto = ttk.Combobox(padre, values=datos_dane.obtener_departamentos(),
                                     state="readonly", style="Editable.TCombobox")
        self.cb_depto.pack(fill="x")
        self.cb_depto.bind("<<ComboboxSelected>>", self._al_cambiar_depto)

        self._etiqueta(padre, "3. Municipio:", editable=True)
        self.cb_municipio = ttk.Combobox(padre, values=[], state="readonly",
                                         style="Editable.TCombobox")
        self.cb_municipio.pack(fill="x")
        self.cb_municipio.bind("<<ComboboxSelected>>", lambda e: self._actualizar_referencias_dane())

        self._etiqueta(padre, "4. Área geográfica:", editable=True)
        self.cb_area = ttk.Combobox(padre, values=AREAS, state="readonly",
                                    style="Editable.TCombobox")
        self.cb_area.current(2)
        self.cb_area.pack(fill="x")
        self.cb_area.bind("<<ComboboxSelected>>", lambda e: self._actualizar_referencias_dane())

        # --- Año de inicio (métodos 1 y 2) ---
        self.frame_año_inicio = tk.Frame(padre, bg=C.SUPERFICIE)
        self._etiqueta(self.frame_año_inicio, "5a. Año de inicio del proyecto:", editable=True)
        self.entry_año_inicio = ttk.Entry(self.frame_año_inicio, style="Editable.TEntry")
        self.entry_año_inicio.insert(0, "2030")
        self.entry_año_inicio.pack(fill="x")
        self.entry_año_inicio.bind("<FocusOut>", lambda e: self._actualizar_aviso())

        self.contenedor_metodo = tk.Frame(padre, bg=C.SUPERFICIE)
        self._crear_panel_manual(self.contenedor_metodo)
        self._crear_panel_tasa(self.contenedor_metodo)

        self.lbl_aviso = self._nota(padre, "", color=C.PELIGRO)

        self._boton(padre, "Calcular proyección", C.PRIMARIO,
                    self.calcular).pack(fill="x", pady=(18, 8), ipady=6)

        self._etiqueta(padre, "Método adoptado para el diseño:", editable=True)
        self.cb_metodo_adoptado = ttk.Combobox(padre, values=rs.COLUMNAS_PROYECCION,
                                               state="readonly", style="Editable.TCombobox")
        self.cb_metodo_adoptado.current(1)
        self.cb_metodo_adoptado.pack(fill="x")
        self.cb_metodo_adoptado.bind("<<ComboboxSelected>>", lambda e: self._actualizar_resultado())

        self.marco_resultado = tk.Frame(
            padre, bg=C.EXITO_FONDO, highlightbackground=C.EXITO,
            highlightcolor=C.EXITO, highlightthickness=1, bd=0,
        )
        self.marco_resultado.pack(fill="x", pady=(14, 0))
        self.lbl_resultado = tk.Label(
            self.marco_resultado, text="Población al final del horizonte: —",
            font=fuente(12, "bold"), bg=C.EXITO_FONDO, fg=C.EXITO,
            justify="center", wraplength=ANCHO_TEXTO - 20, pady=10,
        )
        self.lbl_resultado.pack(fill="x", padx=10)

        self._boton(padre, "💾 Guardar y continuar", C.EXITO_BOTON, self.guardar,
                    fuente(12, "bold")).pack(fill="x", pady=(16, 16), ipady=8)

        self._cambiar_metodo()

    # ------------------------------------------------------------------
    def _crear_panel_manual(self, padre):
        self.frame_manual = tk.Frame(padre, bg=C.SUPERFICIE)
        self._etiqueta(self.frame_manual, "6. Datos censales (mínimo 2, sin máximo):", editable=True)
        self._nota(self.frame_manual,
                   "Se usan el dato más reciente (Tu, Pu) y el más antiguo (T1, P1). "
                   "La columna DANE es solo referencia del municipio y área elegidos.")

        cabecera = tk.Frame(self.frame_manual, bg=C.SUPERFICIE)
        cabecera.pack(fill="x", pady=(6, 0))

        self.frame_filas = tk.Frame(self.frame_manual, bg=C.SUPERFICIE)
        self.frame_filas.pack(fill="x")
        for _ in range(FILAS_MANUALES_INICIALES):
            self._agregar_fila()

        # Títulos de columna con el mismo ancho (px) que los campos de la fila
        primera = self.filas_manual[0]
        for texto, widget, separacion in [("Año", primera[0], 4), ("Población", primera[1], 4),
                                          ("DANE (ref.)", primera[2], 0)]:
            celda = tk.Frame(cabecera, bg=C.SUPERFICIE, height=24,
                             width=widget.winfo_reqwidth() + separacion)
            celda.pack(side="left")
            celda.pack_propagate(False)
            tk.Label(celda, text=texto, font=fuente(9, "bold"), bg=C.SUPERFICIE,
                     fg=C.TEXTO_SECUNDARIO, anchor="w").pack(fill="both", expand=True)

        botones = tk.Frame(self.frame_manual, bg=C.SUPERFICIE)
        botones.pack(fill="x", pady=(6, 0))
        self._boton(botones, "+ Agregar dato", C.PRIMARIO,
                    self._agregar_fila, fuente(9, "bold")).pack(side="left", ipadx=4, ipady=2)
        self._boton(botones, "− Quitar última fila", C.TEXTO_TENUE,
                    self._quitar_fila, fuente(9)).pack(side="left", padx=6, ipadx=4, ipady=2)

    def _agregar_fila(self):
        fila = tk.Frame(self.frame_filas, bg=C.SUPERFICIE)
        fila.pack(fill="x", pady=2)
        e_año = ttk.Entry(fila, width=9, style="Editable.TEntry")
        e_año.pack(side="left", padx=(0, 4))
        e_pob = ttk.Entry(fila, width=13, style="Editable.TEntry")
        e_pob.pack(side="left", padx=(0, 4))
        lbl = tk.Label(fila, text="", width=12, font=fuente(9),
                       bg=C.SUPERFICIE, fg=C.TEXTO_TENUE, anchor="w")
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
        self.frame_tasa = tk.Frame(padre, bg=C.SUPERFICIE)
        self._etiqueta(self.frame_tasa, "5b. Año base del censo:", editable=True)
        self.entry_año_base = ttk.Entry(self.frame_tasa, style="Editable.TEntry")
        self.entry_año_base.pack(fill="x")
        self._etiqueta(self.frame_tasa, "5c. Tasa de crecimiento anual (%):", editable=True)
        self.entry_tasa = ttk.Entry(self.frame_tasa, style="Editable.TEntry")
        self.entry_tasa.pack(fill="x")
        self._etiqueta(self.frame_tasa, "5d. Población en el año base (hab):", editable=True)
        self.entry_pob_base = ttk.Entry(self.frame_tasa, style="Editable.TEntry")
        self.entry_pob_base.pack(fill="x")
        self._nota(self.frame_tasa, "Con este método la proyección empieza en el año base del censo.")

    # ------------------------------------------------------------------
    def _crear_panel_resultados(self, padre):
        tk.Label(padre, text="CÁLCULOS INTERNOS", font=fuente(9, "bold"),
                 bg=C.SUPERFICIE, fg=C.TEXTO_TENUE, anchor="w").pack(fill="x", padx=20, pady=(18, 4))
        self.lbl_parametros = tk.Label(
            padre, text="Calcule la proyección para ver los datos base usados.",
            font=fuente(10), bg=C.RESULTADO_FONDO, fg=C.RESULTADO_TEXTO,
            anchor="w", justify="left", relief="flat", bd=0,
            highlightthickness=1, highlightbackground=C.BORDE, padx=8, pady=6,
        )
        self.lbl_parametros.pack(fill="x", padx=20, pady=(2, 10))
        tema.ajustar_al_ancho(self.lbl_parametros, margen=60)

        marco_tabla = tk.Frame(padre, bg=C.SUPERFICIE)
        marco_tabla.pack(fill="x", padx=20)
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
        self._boton(padre, "📷 Exportar gráfica como imagen", C.TEXTO_SECUNDARIO,
                    self.exportar_grafica, fuente(9, "bold")).pack(
                        side="bottom", fill="x", padx=20, pady=(0, 18), ipady=4)

        self.figura = Figure(figsize=(6.4, 3.6), dpi=90)
        self.ax = self.figura.add_subplot(111)
        self._dibujar_grafica()
        self.canvas_grafica = FigureCanvasTkAgg(self.figura, master=padre)
        self.canvas_grafica.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(10, 6))

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
                             label=col, color=COLORES_SERIE[col])
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
