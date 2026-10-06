"""
Ventana de consulta: Datos Técnicos de Referencia.

Muestra, en un solo lugar, todas las tablas normativas y de catálogo
(RAS 2000 y archivo Excel de referencia del proyecto) que se usan a
lo largo del software, indicando siempre la fuente exacta de cada
tabla. Es una ventana de solo consulta: no depende de que existan
Datos Preliminares ni Caudal de Diseño calculados, así que puede
abrirse en cualquier momento desde el menú principal.
"""

import tkinter as tk
from tkinter import ttk

from datos_tecnicos_referencia import obtener_categorias, obtener_tablas_por_categoria
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria


class VentanaDatosTecnicos(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Datos Técnicos de Referencia")
        ajustar_geometria(self)
        self.minsize(760, 480)
        self.configure(bg=C.FONDO)

        self._crear_widgets()
        self._cargar_arbol()

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        tema.encabezado(
            self, "DATOS TÉCNICOS DE REFERENCIA",
            "Tablas normativas y de catálogo usadas en los cálculos del software, con su fuente.",
            icono="📚",
        )

        panel = tk.PanedWindow(self, orient="horizontal", bg=C.FONDO, sashwidth=12, bd=0)
        panel.pack(fill="both", expand=True, padx=32, pady=24)

        # --- Panel izquierdo: árbol de categorías / tablas ---
        marco_arbol = tema.tarjeta(panel)
        self.arbol = ttk.Treeview(marco_arbol, show="tree", selectmode="browse")
        self.arbol.tag_configure("categoria", font=fuente(10, "bold"))
        scroll_arbol = ttk.Scrollbar(marco_arbol, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=scroll_arbol.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        scroll_arbol.pack(side="right", fill="y")
        self.arbol.bind("<<TreeviewSelect>>", self._al_seleccionar)
        panel.add(marco_arbol, width=440)

        # --- Panel derecho: detalle de la tabla seleccionada ---
        marco_detalle_ext = tema.tarjeta(panel)
        panel.add(marco_detalle_ext, width=1000)

        canvas = tk.Canvas(marco_detalle_ext, bg=C.SUPERFICIE, highlightthickness=0)
        canvas._hydrolab_scroll = True
        scroll_detalle = ttk.Scrollbar(marco_detalle_ext, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll_detalle.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_detalle.pack(side="right", fill="y")

        self.marco_detalle = tk.Frame(canvas, bg=C.SUPERFICIE)
        ventana_id = canvas.create_window((0, 0), window=self.marco_detalle, anchor="nw")
        self.marco_detalle.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(ventana_id, width=e.width))

        self._mostrar_mensaje_inicial()

    # ------------------------------------------------------------------
    def _cargar_arbol(self):
        self._indice_tablas = {}  # id del nodo -> dict de la tabla
        for categoria in obtener_categorias():
            nodo_cat = self.arbol.insert("", "end", text=categoria, open=True, tags=("categoria",))
            for tabla in obtener_tablas_por_categoria(categoria):
                nodo_tabla = self.arbol.insert(nodo_cat, "end", text=tabla["titulo"])
                self._indice_tablas[nodo_tabla] = tabla

    # ------------------------------------------------------------------
    def _mostrar_mensaje_inicial(self):
        for w in self.marco_detalle.winfo_children():
            w.destroy()
        tk.Label(
            self.marco_detalle,
            text="⬅ Selecciona una tabla del panel izquierdo para verla en detalle.",
            font=fuente(10, "italic"), bg=C.SUPERFICIE, fg=C.TEXTO_TENUE,
        ).pack(anchor="w", padx=20, pady=20)

    # ------------------------------------------------------------------
    def _al_seleccionar(self, event=None):
        seleccion = self.arbol.selection()
        if not seleccion:
            return
        nodo = seleccion[0]
        tabla = self._indice_tablas.get(nodo)
        if tabla is None:
            return  # es un nodo de categoría, no de tabla
        self._mostrar_tabla(tabla)

    # ------------------------------------------------------------------
    def _mostrar_tabla(self, tabla):
        for w in self.marco_detalle.winfo_children():
            w.destroy()

        contenido = tk.Frame(self.marco_detalle, bg=C.SUPERFICIE)
        contenido.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(
            contenido, text=tabla["titulo"], font=fuente(13, "bold"),
            bg=C.SUPERFICIE, fg=C.RESULTADO_TEXTO, anchor="w", wraplength=900, justify="left",
        ).pack(fill="x", pady=(0, 4))

        marco_fuente = tk.Frame(contenido, bg=C.INFO_FONDO, bd=1, relief="solid")
        marco_fuente.pack(fill="x", pady=(0, 12))
        tk.Label(
            marco_fuente, text=f"📖 Fuente: {tabla['fuente']}",
            font=fuente(9, "bold"), bg=C.INFO_FONDO, fg=C.RESULTADO_TEXTO,
            anchor="w", justify="left", wraplength=900,
        ).pack(fill="x", padx=8, pady=6)

        # --- Tabla de datos (grid de labels) ---
        marco_tabla = tk.Frame(contenido, bg=C.BORDE, bd=1, relief="solid")
        marco_tabla.pack(fill="x")

        columnas = tabla["columnas"]
        for j, col in enumerate(columnas):
            tk.Label(
                marco_tabla, text=col, font=fuente(9, "bold"),
                bg=C.ENCABEZADO, fg="white", anchor="w", padx=6, pady=5,
                wraplength=220, justify="left",
            ).grid(row=0, column=j, sticky="nsew", padx=1, pady=1)

        for i, fila in enumerate(tabla["filas"], start=1):
            color_fondo = C.FILA_ALTERNA if i % 2 == 0 else "white"
            for j, valor in enumerate(fila):
                tk.Label(
                    marco_tabla, text=valor, font=fuente(9),
                    bg=color_fondo, fg=C.TEXTO, anchor="w", padx=6, pady=4,
                    wraplength=220, justify="left",
                ).grid(row=i, column=j, sticky="nsew", padx=1, pady=1)

        for j in range(len(columnas)):
            marco_tabla.grid_columnconfigure(j, weight=1)

        # --- Notas ---
        if tabla.get("notas"):
            tk.Label(
                contenido, text=f"ℹ {tabla['notas']}",
                font=fuente(8, "italic"), bg=C.SUPERFICIE, fg=C.TEXTO_TENUE,
                anchor="w", justify="left", wraplength=900,
            ).pack(fill="x", pady=(12, 0))
