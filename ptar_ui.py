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

ESTILO: los colores, fuentes y bloques de interfaz (encabezado,
tarjeta del formulario, panel lateral de resultados) vienen de tema.py,
igual que en el resto de HydroLab; ninguna ventana concreta define
colores propios.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import tema
from tema import C, fuente
from estado_proyecto import EstadoProyecto
from ui_utils import ajustar_geometria


# Ancho (px) de los textos largos dentro de la tarjeta del formulario.
ANCHO_TEXTO = 760


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

    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title(self.TITULO.title())
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)

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
        """Los estilos Editable.TEntry / Editable.TCombobox los define tema.py."""

    def _crear_widgets(self):
        cuerpo, lateral = tema.layout_formulario(self, self.TITULO, self.SUBTITULO or None)
        self.canvas = cuerpo.canvas
        self.cuerpo = cuerpo
        self.lateral = lateral

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

        self._seccion(cuerpo, "Resultados")
        self.marco_resultados = tk.Frame(cuerpo, bg=C.SUPERFICIE)
        self.marco_resultados.pack(fill="x")

        self._seccion(cuerpo, "Verificación normativa")
        self.marco_verificaciones = tk.Frame(cuerpo, bg=C.SUPERFICIE)
        self.marco_verificaciones.pack(fill="x", pady=(0, 8))

        # --- Panel lateral: Calcular, resultado final y Guardar ---
        tk.Button(
            lateral, text="Calcular", font=fuente(11, "bold"),
            bg=C.PRIMARIO, fg="white", cursor="hand2",
            command=self.calcular,
        ).pack(fill="x", pady=(15, 10), ipady=6)

        marco_final = tk.Frame(
            lateral, bg=C.EXITO_FONDO, bd=0,
            highlightbackground=C.EXITO, highlightthickness=1,
        )
        marco_final.pack(fill="x", pady=(10, 15))
        self.marco_final = marco_final
        tk.Label(
            marco_final, text=self.TITULO_FINAL, font=fuente(11, "bold"),
            bg=C.EXITO_FONDO, fg=C.EXITO,
            justify="center", wraplength=tema.ANCHO_TEXTO_LATERAL,
        ).pack(pady=(10, 4), padx=10)
        self.lbl_final = tk.Label(
            marco_final, text="—", font=fuente(12, "bold"), bg=C.EXITO_FONDO,
            fg=C.EXITO, justify="center", wraplength=tema.ANCHO_TEXTO_LATERAL,
        )
        self.lbl_final.pack(pady=(0, 4), padx=10)
        self.lbl_cumple = tk.Label(
            marco_final, text="", font=fuente(9, "bold"), bg=C.EXITO_FONDO,
            fg=C.EXITO, justify="center", wraplength=tema.ANCHO_TEXTO_LATERAL,
        )
        self.lbl_cumple.pack(pady=(0, 10), padx=10)

        tk.Button(
            lateral, text="💾 Guardar y continuar", font=fuente(12, "bold"),
            bg=C.EXITO_BOTON, fg="white", cursor="hand2",
            command=self.guardar,
        ).pack(fill="x", ipady=8, pady=(0, 20))

        self.update_idletasks()
        self.canvas.yview_moveto(0)

    def _seccion(self, padre, texto):
        tk.Label(
            padre, text=texto.upper(), font=fuente(9, "bold"),
            bg=C.SUPERFICIE, fg=C.TEXTO_TENUE, anchor="w",
        ).pack(fill="x", pady=(16, 2))
        tk.Frame(padre, bg=C.BORDE, height=1).pack(fill="x", pady=(0, 2))

    def _etiqueta(self, padre, texto, editable=False):
        if editable:
            texto = f"✎ {texto}   (dato editable)"
        tk.Label(
            padre, text=texto, font=fuente(10, "bold" if editable else "normal"),
            bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO if editable else C.TEXTO,
            anchor="w", justify="left", wraplength=ANCHO_TEXTO,
        ).pack(fill="x", pady=(8, 2))

    def _valor(self, padre, texto):
        tk.Label(
            padre, text=texto, font=fuente(11, "bold"),
            bg=C.RESULTADO_FONDO, fg=C.RESULTADO_TEXTO, anchor="w",
            relief="flat", bd=0, highlightthickness=1, highlightbackground=C.BORDE, padx=8,
        ).pack(fill="x", ipady=4)

    def _nota(self, padre, texto):
        tk.Label(
            padre, text=texto, font=fuente(8, "italic"),
            bg=C.SUPERFICIE, fg=C.TEXTO_TENUE, anchor="w", justify="left",
            wraplength=ANCHO_TEXTO,
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
                font=fuente(9, "bold"), bg=C.SUPERFICIE,
                fg=C.EXITO if cumple else C.ADVERTENCIA,
                anchor="w", justify="left", wraplength=ANCHO_TEXTO,
            ).pack(fill="x", pady=1)
        self.lbl_final.config(text=r["final"])
        self.lbl_cumple.config(
            text="✔ Cumple los criterios verificados de la Res. 0330 de 2017"
            if r["cumple_todo"] else "⚠ Revise los parámetros marcados con ⚠ en la verificación normativa",
            fg=C.EXITO if r["cumple_todo"] else C.ADVERTENCIA,
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
