"""
Interfaz común de las ventanas de cálculo de la PTAR.

Todas las ventanas de la PTAR (caudal de aguas residuales, rejillas,
desarenador, trampa de grasas, UASB, laguna facultativa y lechos de
secado) comparten la misma estructura visual, así que se construyen a
partir de una sola clase base: `VentanaCalculoPTAR`.

Cada ventana concreta solo declara:
    - TITULO / SUBTITULO (artículos de la Res. 0330 que aplica)
    - campos():        datos editables (número o lista de opciones)
    - datos_base():    datos que vienen de EstadoProyecto (caudales, etc.)
    - calcular_resultado(datos): función de ptar_calculos.py
    - ATRIBUTO_ESTADO: dónde se guarda en EstadoProyecto

ESTILO: todos los colores y fuentes están en el diccionario TEMA de
abajo. Para re-estilizar todas las ventanas de la PTAR basta con
cambiar ese diccionario (o reemplazar los métodos `_crear_*` de la
clase base); ninguna ventana concreta define colores propios.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from estado_proyecto import EstadoProyecto
from ui_utils import ajustar_geometria, hacer_scrollable


# Paleta y fuentes — mismas del resto de HydroLab.
TEMA = {
    "fuente": "Arial",
    "fondo": "#F2F4F4",
    "titulo_bg": "#1F4E78",
    "titulo_fg": "white",
    "subtitulo_fg": "#D9E1F2",
    "texto": "black",
    "editable_fg": "#B9770E",
    "editable_bg": "#FEF9E7",
    "editable_borde": "#F1C40F",
    "resultado_bg": "white",
    "resultado_fg": "#1B4F72",
    "nota_fg": "#7B7D7D",
    "seccion_fg": "#1F4E78",
    "ok_fg": "#1E8449",
    "alerta_fg": "#B9770E",
    "final_bg": "#EAFAF1",
    "final_fg": "#1E8449",
    "boton_calcular_bg": "#2E86C1",
    "boton_guardar_bg": "#28B463",
    "boton_fg": "white",
}


class RequisitoFaltante(Exception):
    """Se lanza desde datos_base() cuando falta un paso previo."""


def campo(clave, etiqueta, defecto, nota=None, opciones=None):
    """Describe un dato editable de una ventana de la PTAR."""
    return {
        "clave": clave, "etiqueta": etiqueta, "defecto": defecto,
        "nota": nota, "opciones": opciones,
    }


class VentanaCalculoPTAR(tk.Toplevel):
    TITULO = "PTAR"
    SUBTITULO = ""
    TITULO_FINAL = "✅ RESULTADO"
    ATRIBUTO_ESTADO = None
    ANCHO = 640
    ALTO = 820

    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title(self.TITULO.title())
        self.resizable(False, True)
        ajustar_geometria(self, ancho=self.ANCHO, alto=self.ALTO)
        self.configure(bg=TEMA["fondo"])

        self.al_guardar = al_guardar
        self.entradas = {}
        self._resultado = None
        self._datos = None

        # Quien abre la ventana debe llamar antes a requisito_faltante();
        # si aun así falta un paso previo, aquí se lanza RequisitoFaltante.
        self.base = self.datos_base()

        self._crear_estilos()
        self._crear_widgets()
        self.calcular(silencioso=True)

    # ------------------------------------------------------------------
    # Métodos que redefine cada ventana concreta
    # ------------------------------------------------------------------
    @classmethod
    def datos_base(cls):
        """Datos que vienen de pasos previos (dict). Puede lanzar RequisitoFaltante."""
        return {}

    @classmethod
    def requisito_faltante(cls):
        """Mensaje del paso previo que falta, o None si se puede abrir la ventana."""
        try:
            cls.datos_base()
        except RequisitoFaltante as e:
            return str(e)
        return None

    def info_base(self):
        """Lista de (etiqueta, texto) con los datos de entrada no editables."""
        return []

    def campos(self):
        return []

    def calcular_resultado(self, datos):
        raise NotImplementedError

    def al_cambiar_opcion(self, clave, valor):
        """Se llama cuando el usuario cambia una lista desplegable."""

    def guardar_extra(self, resultado):
        """Para guardar campos adicionales en EstadoProyecto (opcional)."""

    # ------------------------------------------------------------------
    # Utilidades para las ventanas concretas
    # ------------------------------------------------------------------
    def fijar_valor(self, clave, valor):
        widget = self.entradas[clave]
        if isinstance(widget, ttk.Combobox):
            widget.set(valor)
        else:
            widget.delete(0, "end")
            widget.insert(0, str(valor))

    def _valores_guardados(self):
        guardado = getattr(EstadoProyecto, self.ATRIBUTO_ESTADO, None) if self.ATRIBUTO_ESTADO else None
        return (guardado or {}).get("entradas", {})

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_estilos(self):
        estilo = ttk.Style(self)
        estilo.configure(
            "Editable.TEntry", fieldbackground=TEMA["editable_bg"],
            bordercolor=TEMA["editable_borde"], lightcolor=TEMA["editable_borde"],
        )
        estilo.configure("Editable.TCombobox", fieldbackground=TEMA["editable_bg"])
        estilo.map("Editable.TCombobox", fieldbackground=[("readonly", TEMA["editable_bg"])])

    def _crear_widgets(self):
        f = TEMA["fuente"]
        tk.Label(
            self, text=self.TITULO, font=(f, 14, "bold"),
            bg=TEMA["titulo_bg"], fg=TEMA["titulo_fg"], pady=10,
        ).pack(fill="x")
        if self.SUBTITULO:
            tk.Label(
                self, text=self.SUBTITULO, font=(f, 8, "italic"),
                bg=TEMA["titulo_bg"], fg=TEMA["subtitulo_fg"], pady=6,
                wraplength=self.ANCHO - 40,
            ).pack(fill="x")

        contenedor = tk.Frame(self, bg=TEMA["fondo"])
        contenedor.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(contenedor, bg=TEMA["fondo"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        cuerpo_ext = tk.Frame(self.canvas, bg=TEMA["fondo"])
        hacer_scrollable(self.canvas, cuerpo_ext)

        cuerpo = tk.Frame(cuerpo_ext, bg=TEMA["fondo"])
        cuerpo.pack(fill="both", expand=True, padx=20, pady=15)
        self.cuerpo = cuerpo

        info = self.info_base()
        if info:
            self._seccion(cuerpo, "Datos de pasos anteriores")
            for etiqueta, texto in info:
                self._etiqueta(cuerpo, etiqueta)
                self._valor(cuerpo, texto)

        guardados = self._valores_guardados()
        lista_campos = self.campos()
        if lista_campos:
            self._seccion(cuerpo, "Datos de diseño")
        for c in lista_campos:
            self._etiqueta(cuerpo, c["etiqueta"], editable=True)
            valor = guardados.get(c["clave"], c["defecto"])
            if c["opciones"]:
                w = ttk.Combobox(cuerpo, values=c["opciones"], state="readonly",
                                 style="Editable.TCombobox")
                w.set(valor)
                w.bind("<<ComboboxSelected>>",
                       lambda e, k=c["clave"]: self._opcion_cambiada(k))
            else:
                w = ttk.Entry(cuerpo, style="Editable.TEntry")
                w.insert(0, "" if valor is None else str(valor))
                w.bind("<FocusOut>", lambda e: self.calcular(silencioso=True))
                w.bind("<Return>", lambda e: self.calcular())
            w.pack(fill="x")
            self.entradas[c["clave"]] = w
            if c["nota"]:
                self._nota(cuerpo, c["nota"])

        tk.Button(
            cuerpo, text="Calcular", font=(f, 11, "bold"),
            bg=TEMA["boton_calcular_bg"], fg=TEMA["boton_fg"], cursor="hand2",
            command=self.calcular,
        ).pack(fill="x", pady=(15, 10), ipady=6)

        self._seccion(cuerpo, "Resultados")
        self.marco_resultados = tk.Frame(cuerpo, bg=TEMA["fondo"])
        self.marco_resultados.pack(fill="x")

        self._seccion(cuerpo, "Verificación normativa")
        self.marco_verificaciones = tk.Frame(cuerpo, bg=TEMA["fondo"])
        self.marco_verificaciones.pack(fill="x")

        marco_final = tk.Frame(
            cuerpo, bg=TEMA["final_bg"], bd=2, relief="solid",
            highlightbackground=TEMA["final_fg"], highlightthickness=2,
        )
        marco_final.pack(fill="x", pady=(15, 15))
        tk.Label(
            marco_final, text=self.TITULO_FINAL, font=(f, 11, "bold"),
            bg=TEMA["final_bg"], fg=TEMA["final_fg"],
        ).pack(pady=(10, 4))
        self.lbl_final = tk.Label(
            marco_final, text="—", font=(f, 12, "bold"), bg=TEMA["final_bg"],
            fg=TEMA["final_fg"], justify="center", wraplength=self.ANCHO - 80,
        )
        self.lbl_final.pack(pady=(0, 4))
        self.lbl_cumple = tk.Label(
            marco_final, text="", font=(f, 9, "bold"), bg=TEMA["final_bg"],
            fg=TEMA["final_fg"], justify="center",
        )
        self.lbl_cumple.pack(pady=(0, 10))

        tk.Button(
            cuerpo, text="💾 Guardar y continuar", font=(f, 12, "bold"),
            bg=TEMA["boton_guardar_bg"], fg=TEMA["boton_fg"], cursor="hand2",
            command=self.guardar,
        ).pack(fill="x", ipady=8, pady=(0, 20))

        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)

    def _seccion(self, padre, texto):
        tk.Label(
            padre, text=texto.upper(), font=(TEMA["fuente"], 9, "bold"),
            bg=TEMA["fondo"], fg=TEMA["seccion_fg"], anchor="w",
        ).pack(fill="x", pady=(14, 0))
        tk.Frame(padre, bg=TEMA["seccion_fg"], height=1).pack(fill="x", pady=(0, 2))

    def _etiqueta(self, padre, texto, editable=False):
        if editable:
            texto = f"✎ {texto}   (dato editable)"
        tk.Label(
            padre, text=texto, font=(TEMA["fuente"], 10, "bold" if editable else "normal"),
            bg=TEMA["fondo"], fg=TEMA["editable_fg"] if editable else TEMA["texto"],
            anchor="w", justify="left", wraplength=self.ANCHO - 60,
        ).pack(fill="x", pady=(8, 2))

    def _valor(self, padre, texto):
        tk.Label(
            padre, text=texto, font=(TEMA["fuente"], 11, "bold"),
            bg=TEMA["resultado_bg"], fg=TEMA["resultado_fg"], anchor="w",
            relief="solid", bd=1,
        ).pack(fill="x", ipady=4)

    def _nota(self, padre, texto):
        tk.Label(
            padre, text=texto, font=(TEMA["fuente"], 8, "italic"),
            bg=TEMA["fondo"], fg=TEMA["nota_fg"], anchor="w", justify="left",
            wraplength=self.ANCHO - 60,
        ).pack(fill="x", pady=(0, 2))

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------
    def _opcion_cambiada(self, clave):
        self.al_cambiar_opcion(clave, self.entradas[clave].get())
        self.calcular(silencioso=True)

    def _leer_entradas(self):
        valores = {}
        for clave, widget in self.entradas.items():
            texto = widget.get().strip()
            if isinstance(widget, ttk.Combobox):
                valores[clave] = texto
                continue
            try:
                valores[clave] = float(texto.replace(",", "."))
            except ValueError:
                raise ValueError(f"Revise el dato: «{self._etiqueta_de(clave)}».")
        return valores

    def _etiqueta_de(self, clave):
        for c in self.campos():
            if c["clave"] == clave:
                return c["etiqueta"]
        return clave

    def calcular(self, silencioso=False):
        try:
            entradas = self._leer_entradas()
            datos = dict(self.base)
            datos.update(entradas)
            resultado = self.calcular_resultado(datos)
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            self._resultado = None
            self._mostrar_vacio()
            if not silencioso:
                messagebox.showwarning("Datos inválidos", f"Revise los valores ingresados.\n{e}",
                                       parent=self)
            return
        self._resultado = resultado
        self._entradas_usadas = entradas
        self._mostrar(resultado)

    def _limpiar(self):
        for marco in (self.marco_resultados, self.marco_verificaciones):
            for hijo in marco.winfo_children():
                hijo.destroy()

    def _mostrar_vacio(self):
        self._limpiar()
        self._nota(self.marco_resultados, "Complete los datos de diseño y presione Calcular.")
        self.lbl_final.config(text="—")
        self.lbl_cumple.config(text="")

    def _mostrar(self, r):
        self._limpiar()
        for etiqueta, texto in r["filas"]:
            self._etiqueta(self.marco_resultados, etiqueta + ":")
            self._valor(self.marco_resultados, texto)
        for texto, cumple in r["verificaciones"]:
            tk.Label(
                self.marco_verificaciones,
                text=("✔ " if cumple else "⚠ ") + texto,
                font=(TEMA["fuente"], 9, "bold"), bg=TEMA["fondo"],
                fg=TEMA["ok_fg"] if cumple else TEMA["alerta_fg"],
                anchor="w", justify="left", wraplength=self.ANCHO - 60,
            ).pack(fill="x", pady=1)
        self.lbl_final.config(text=r["final"])
        self.lbl_cumple.config(
            text="✔ Cumple los criterios verificados de la Res. 0330 de 2017"
            if r["cumple_todo"] else "⚠ Revise los parámetros marcados arriba",
            fg=TEMA["final_fg"] if r["cumple_todo"] else TEMA["alerta_fg"],
        )

    def guardar(self):
        self.calcular()
        if self._resultado is None:
            return
        r = self._resultado
        if not r["cumple_todo"]:
            seguir = messagebox.askyesno(
                "No cumple todos los criterios",
                "Algunos parámetros no cumplen los criterios de la Res. 0330 de 2017 "
                "(marcados con ⚠).\n\n¿Desea guardar de todas formas?",
                parent=self,
            )
            if not seguir:
                return

        guardado = dict(r)
        guardado["entradas"] = dict(self._entradas_usadas)
        setattr(EstadoProyecto, self.ATRIBUTO_ESTADO, guardado)
        self.guardar_extra(r)

        messagebox.showinfo("Guardado", f"{self.TITULO.title()} guardado correctamente.\n\n"
                            + r["final"], parent=self)
        if self.al_guardar:
            self.al_guardar()
        self.destroy()
