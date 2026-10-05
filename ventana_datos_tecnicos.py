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
from ui_utils import ajustar_geometria


class VentanaDatosTecnicos(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Datos Técnicos de Referencia")
        ajustar_geometria(self, ancho=900, alto=600)
        self.minsize(760, 480)
        self.configure(bg="#F2F4F4")

        self._crear_widgets()
        self._cargar_arbol()

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        titulo = tk.Label(
            self, text="📚 DATOS TÉCNICOS DE REFERENCIA",
            font=("Arial", 14, "bold"), bg="#1F4E78", fg="white", pady=10,
        )
        titulo.pack(fill="x")

        subtitulo = tk.Label(
            self,
            text="Tablas normativas y de catálogo usadas en los cálculos del software, con su fuente.",
            font=("Arial", 9, "italic"), bg="#F2F4F4", fg="#5D6D7E", pady=6,
        )
        subtitulo.pack(fill="x")

        panel = tk.PanedWindow(self, orient="horizontal", bg="#F2F4F4", sashwidth=4)
        panel.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # --- Panel izquierdo: árbol de categorías / tablas ---
        marco_arbol = tk.Frame(panel, bg="#F2F4F4")
        self.arbol = ttk.Treeview(marco_arbol, show="tree", selectmode="browse")
        scroll_arbol = ttk.Scrollbar(marco_arbol, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=scroll_arbol.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        scroll_arbol.pack(side="right", fill="y")
        self.arbol.bind("<<TreeviewSelect>>", self._al_seleccionar)
        panel.add(marco_arbol, width=300)

        # --- Panel derecho: detalle de la tabla seleccionada ---
        marco_detalle_ext = tk.Frame(panel, bg="white")
        panel.add(marco_detalle_ext, width=580)

        canvas = tk.Canvas(marco_detalle_ext, bg="white", highlightthickness=0)
        scroll_detalle = ttk.Scrollbar(marco_detalle_ext, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll_detalle.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_detalle.pack(side="right", fill="y")

        self.marco_detalle = tk.Frame(canvas, bg="white")
        ventana_id = canvas.create_window((0, 0), window=self.marco_detalle, anchor="nw")
        self.marco_detalle.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(ventana_id, width=e.width))

        def _rueda(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _rueda)

        self._mostrar_mensaje_inicial()

    # ------------------------------------------------------------------
    def _cargar_arbol(self):
        self._indice_tablas = {}  # id del nodo -> dict de la tabla
        for categoria in obtener_categorias():
            nodo_cat = self.arbol.insert("", "end", text=categoria, open=True)
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
            font=("Arial", 10, "italic"), bg="white", fg="#7B7D7D",
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

        contenido = tk.Frame(self.marco_detalle, bg="white")
        contenido.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(
            contenido, text=tabla["titulo"], font=("Arial", 13, "bold"),
            bg="white", fg="#1B4F72", anchor="w", wraplength=520, justify="left",
        ).pack(fill="x", pady=(0, 4))

        marco_fuente = tk.Frame(contenido, bg="#EBF5FB", bd=1, relief="solid")
        marco_fuente.pack(fill="x", pady=(0, 12))
        tk.Label(
            marco_fuente, text=f"📖 Fuente: {tabla['fuente']}",
            font=("Arial", 9, "bold"), bg="#EBF5FB", fg="#1B4F72",
            anchor="w", justify="left", wraplength=520,
        ).pack(fill="x", padx=8, pady=6)

        # --- Tabla de datos (grid de labels) ---
        marco_tabla = tk.Frame(contenido, bg="#D5D8DC", bd=1, relief="solid")
        marco_tabla.pack(fill="x")

        columnas = tabla["columnas"]
        for j, col in enumerate(columnas):
            tk.Label(
                marco_tabla, text=col, font=("Arial", 9, "bold"),
                bg="#1F4E78", fg="white", anchor="w", padx=6, pady=5,
                wraplength=150, justify="left",
            ).grid(row=0, column=j, sticky="nsew", padx=1, pady=1)

        for i, fila in enumerate(tabla["filas"], start=1):
            color_fondo = "#F8F9F9" if i % 2 == 0 else "white"
            for j, valor in enumerate(fila):
                tk.Label(
                    marco_tabla, text=valor, font=("Arial", 9),
                    bg=color_fondo, fg="#1B2631", anchor="w", padx=6, pady=4,
                    wraplength=150, justify="left",
                ).grid(row=i, column=j, sticky="nsew", padx=1, pady=1)

        for j in range(len(columnas)):
            marco_tabla.grid_columnconfigure(j, weight=1)

        # --- Notas ---
        if tabla.get("notas"):
            tk.Label(
                contenido, text=f"ℹ {tabla['notas']}",
                font=("Arial", 8, "italic"), bg="white", fg="#7B7D7D",
                anchor="w", justify="left", wraplength=520,
            ).pack(fill="x", pady=(12, 0))
