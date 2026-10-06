"""
Tema visual de HydroLab.

Reúne en UN SOLO LUGAR todo lo que define el aspecto del software:
paleta de colores, tipografía, estilo de los widgets ttk y los
bloques de interfaz que se repiten en todas las ventanas
(encabezado, tarjetas, botones, área con scroll y el diseño
"formulario + panel de resultados" de las ventanas de cálculo).

Cualquier ventana nueva solo necesita:

    import tema
    from tema import C, fuente

    class MiVentana(tk.Toplevel):
        def __init__(self, master):
            super().__init__(master)
            self.title("Mi proceso")
            tema.maximizar(self)
            self.configure(bg=C.FONDO)
            cuerpo, lateral = tema.layout_formulario(
                self, "MI PROCESO", "Art. XX, Resolución 0330 de 2017",
            )
            # ... campos en `cuerpo`, botones y resultado final en `lateral`

`aplicar_tema(root)` se llama una sola vez, al crear la ventana
principal (ver main.py).
"""

import sys
import tkinter as tk
from tkinter import ttk, font as tkfont


# ----------------------------------------------------------------------
# Paleta de colores
# ----------------------------------------------------------------------
class C:
    """Colores del software. Usar siempre estos nombres, nunca hex sueltos."""

    # Estructura
    FONDO = "#EEF2F6"              # fondo general de las ventanas
    SUPERFICIE = "#FFFFFF"         # tarjetas / paneles
    BORDE = "#D8E0EA"              # bordes suaves de tarjetas y campos
    FILA_ALTERNA = "#F6F8FB"       # filas pares de tablas

    # Barra lateral y encabezados (azul profundo)
    ENCABEZADO = "#0B2545"
    ENCABEZADO_2 = "#13315C"       # hover / bloques dentro del encabezado
    ENCABEZADO_SUBTEXTO = "#A9BCD6"

    # Marca (azul agua)
    PRIMARIO = "#0B6BCB"
    PRIMARIO_SUAVE = "#E3EFFB"
    ACENTO = "#14B8C4"             # turquesa: detalles, línea bajo el título

    # Texto
    TEXTO = "#16202C"
    TEXTO_SECUNDARIO = "#4A5A6E"
    TEXTO_TENUE = "#7D8B9C"

    # Valores calculados (solo lectura)
    RESULTADO_TEXTO = "#0B3D6E"
    RESULTADO_FONDO = "#F6F8FB"

    # Datos que el usuario puede editar
    EDITABLE_FONDO = "#FFF8E6"
    EDITABLE_BORDE = "#F2B233"
    EDITABLE_TEXTO = "#A15C00"

    # Estados
    EXITO = "#13795B"
    EXITO_FONDO = "#E7F6EF"
    EXITO_BOTON = "#16A06D"
    ADVERTENCIA = "#B26A00"
    ADVERTENCIA_FONDO = "#FFF4E0"
    PELIGRO = "#C2372F"
    INFO_FONDO = "#E8F1FB"

    # Módulos
    PTAP = "#0B6BCB"
    PTAR = "#0E9F6E"
    RELLENO = "#A04000"
    INFORME = "#6E4BD8"


# ----------------------------------------------------------------------
# Tipografía
# ----------------------------------------------------------------------
_FUENTES_PREFERIDAS = (
    "Segoe UI",          # Windows
    "SF Pro Text",       # macOS reciente
    "Helvetica Neue",    # macOS
    "Inter",
    "Ubuntu",
    "Noto Sans",
    "Cantarell",
    "DejaVu Sans",       # casi cualquier Linux
    "Arial",
)

FUENTE = "Arial"  # se reemplaza en aplicar_tema() por la mejor disponible

# Todo el texto se ve un punto más grande que el tamaño pedido, porque
# las ventanas ahora abren a pantalla completa y hay espacio de sobra.
_INCREMENTO = 1


def fuente(tamano, *estilo):
    """Tupla de fuente con la tipografía del tema: fuente(11, "bold")."""
    return (FUENTE, tamano + _INCREMENTO, *estilo)


def _elegir_fuente(root):
    disponibles = set(tkfont.families(root))
    for nombre in _FUENTES_PREFERIDAS:
        if nombre in disponibles:
            return nombre
    return "TkDefaultFont"


# ----------------------------------------------------------------------
# Utilidades de color
# ----------------------------------------------------------------------
def _a_rgb(widget, color):
    r, g, b = widget.winfo_rgb(color)
    return r // 256, g // 256, b // 256


def oscurecer(widget, color, factor=0.12):
    """Devuelve `color` oscurecido un `factor` (0-1). Sirve para el hover."""
    try:
        r, g, b = _a_rgb(widget, color)
    except tk.TclError:
        return color
    # Para colores muy claros (tarjetas blancas) se oscurece un poco
    # menos, para que el hover sea sutil.
    if (r + g + b) / 3 > 235:
        factor = 0.05
    r, g, b = (int(c * (1 - factor)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


# ----------------------------------------------------------------------
# Tema global
# ----------------------------------------------------------------------
def aplicar_tema(root):
    """Configura tipografía, estilos ttk y comportamiento de los botones."""
    global FUENTE
    FUENTE = _elegir_fuente(root)

    for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        try:
            tkfont.nametofont(nombre).configure(family=FUENTE, size=10 + _INCREMENTO)
        except tk.TclError:
            pass

    # Valores por defecto de los widgets clásicos de Tk
    root.option_add("*Font", fuente(10))
    root.option_add("*Button.relief", "flat")
    root.option_add("*Button.borderWidth", 0)
    root.option_add("*Button.highlightThickness", 0)
    root.option_add("*Button.cursor", "hand2")
    root.option_add("*Radiobutton.highlightThickness", 0)
    root.option_add("*Checkbutton.highlightThickness", 0)
    root.option_add("*TCombobox*Listbox.font", fuente(10))
    root.option_add("*TCombobox*Listbox.selectBackground", C.PRIMARIO)
    root.option_add("*TCombobox*Listbox.selectForeground", "white")

    _configurar_ttk(root)
    _activar_hover(root)
    _activar_rueda_mouse(root)


def _configurar_ttk(root):
    estilo = ttk.Style(root)
    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass

    estilo.configure(".", font=fuente(10), background=C.FONDO, foreground=C.TEXTO)

    campo = dict(
        fieldbackground=C.SUPERFICIE, background=C.SUPERFICIE,
        bordercolor=C.BORDE, lightcolor=C.BORDE, darkcolor=C.BORDE,
        foreground=C.TEXTO, padding=(8, 6), insertcolor=C.TEXTO,
        arrowcolor=C.TEXTO_SECUNDARIO,
    )
    estilo.configure("TEntry", **campo)
    estilo.configure("TCombobox", **campo)
    estilo.map(
        "TEntry",
        bordercolor=[("focus", C.PRIMARIO)], lightcolor=[("focus", C.PRIMARIO)],
    )
    estilo.map(
        "TCombobox",
        fieldbackground=[("readonly", C.SUPERFICIE)],
        selectbackground=[("readonly", C.SUPERFICIE)],
        selectforeground=[("readonly", C.TEXTO)],
        bordercolor=[("focus", C.PRIMARIO)], lightcolor=[("focus", C.PRIMARIO)],
        background=[("active", C.PRIMARIO_SUAVE), ("readonly", C.SUPERFICIE)],
    )

    # Campos que el usuario puede modificar (fondo ámbar suave)
    editable = dict(
        campo, fieldbackground=C.EDITABLE_FONDO, background=C.EDITABLE_FONDO,
        bordercolor=C.EDITABLE_BORDE, lightcolor=C.EDITABLE_BORDE,
        darkcolor=C.EDITABLE_BORDE,
    )
    estilo.configure("Editable.TEntry", **editable)
    estilo.configure("Editable.TCombobox", **editable)
    estilo.map(
        "Editable.TCombobox",
        fieldbackground=[("readonly", C.EDITABLE_FONDO)],
        selectbackground=[("readonly", C.EDITABLE_FONDO)],
        selectforeground=[("readonly", C.TEXTO)],
    )

    estilo.configure(
        "Vertical.TScrollbar", gripcount=0, background="#C5CFDB",
        troughcolor=C.FONDO, bordercolor=C.FONDO, lightcolor="#C5CFDB",
        darkcolor="#C5CFDB", arrowcolor=C.TEXTO_SECUNDARIO, arrowsize=14,
    )
    estilo.map("Vertical.TScrollbar", background=[("active", "#A9B6C6")])
    estilo.configure(
        "Horizontal.TScrollbar", gripcount=0, background="#C5CFDB",
        troughcolor=C.FONDO, bordercolor=C.FONDO, lightcolor="#C5CFDB",
        darkcolor="#C5CFDB", arrowcolor=C.TEXTO_SECUNDARIO, arrowsize=14,
    )

    estilo.configure(
        "Treeview", background=C.SUPERFICIE, fieldbackground=C.SUPERFICIE,
        foreground=C.TEXTO, rowheight=30, bordercolor=C.BORDE,
        lightcolor=C.BORDE, darkcolor=C.BORDE, font=fuente(10),
    )
    estilo.map(
        "Treeview",
        background=[("selected", C.PRIMARIO)], foreground=[("selected", "white")],
    )
    estilo.configure(
        "Treeview.Heading", background=C.ENCABEZADO, foreground="white",
        font=fuente(10, "bold"), relief="flat", padding=(6, 8),
        bordercolor=C.ENCABEZADO, lightcolor=C.ENCABEZADO, darkcolor=C.ENCABEZADO,
    )
    estilo.map("Treeview.Heading", background=[("active", C.ENCABEZADO_2)])

    estilo.configure("TRadiobutton", background=C.FONDO, font=fuente(10))
    estilo.configure("TCheckbutton", background=C.FONDO, font=fuente(10))
    estilo.configure("TPanedwindow", background=C.FONDO)
    estilo.configure("TNotebook", background=C.FONDO, bordercolor=C.BORDE)
    estilo.configure("TNotebook.Tab", padding=(14, 8), font=fuente(10, "bold"))


def _activar_hover(root):
    """Todos los tk.Button se oscurecen un poco al pasar el mouse."""

    def entrar(event):
        b = event.widget
        try:
            if str(b.cget("state")) == "disabled":
                return
            base = b.cget("bg")
            hover = oscurecer(b, base)
            b._color_base = base
            b._color_hover = hover
            b.configure(bg=hover, activebackground=hover, activeforeground=b.cget("fg"))
        except tk.TclError:
            pass

    def salir(event):
        b = event.widget
        try:
            # Solo se restaura si nadie cambió el color mientras tanto
            # (p. ej. un botón que se marca como "completado").
            if getattr(b, "_color_hover", None) == b.cget("bg"):
                b.configure(bg=b._color_base)
        except tk.TclError:
            pass

    root.bind_class("Button", "<Enter>", entrar, add="+")
    root.bind_class("Button", "<Leave>", salir, add="+")


# ----------------------------------------------------------------------
# Rueda del mouse: desplaza el área con scroll que está bajo el puntero
# ----------------------------------------------------------------------
_CANVAS_ACTIVOS = []


def _activar_rueda_mouse(root):
    def canvas_bajo_puntero(event):
        try:
            w = event.widget.winfo_containing(event.x_root, event.y_root)
        except (tk.TclError, KeyError, AttributeError):
            return None
        while w is not None:
            if getattr(w, "_hydrolab_scroll", False):
                return w
            w = w.master
        return None

    def rueda(event):
        canvas = canvas_bajo_puntero(event)
        if canvas is None:
            return
        if getattr(event, "num", None) == 4:
            pasos = -1
        elif getattr(event, "num", None) == 5:
            pasos = 1
        elif sys.platform == "darwin":
            pasos = -int(event.delta)
        else:
            pasos = -int(event.delta / 120)
        if pasos:
            canvas.yview_scroll(pasos, "units")

    root.bind_all("<MouseWheel>", rueda, add="+")
    root.bind_all("<Button-4>", rueda, add="+")
    root.bind_all("<Button-5>", rueda, add="+")


# ----------------------------------------------------------------------
# Pantalla completa
# ----------------------------------------------------------------------
def maximizar(ventana):
    """
    Abre `ventana` (Tk o Toplevel) maximizada, ocupando toda la
    pantalla (conserva la barra de título para poder cerrarla).

    F11 alterna a pantalla completa "real" (sin barra de título) y
    Esc vuelve al modo maximizado.
    """
    ventana.resizable(True, True)
    ventana.update_idletasks()
    ancho = ventana.winfo_screenwidth()
    alto = ventana.winfo_screenheight()
    ventana.minsize(min(900, ancho), min(600, alto))
    # Tamaño "restaurado" (si el usuario sale del modo maximizado)
    ventana.geometry(f"{int(ancho * 0.85)}x{int(alto * 0.85)}+{int(ancho * 0.075)}+{int(alto * 0.05)}")

    try:
        ventana.state("zoomed")                 # Windows y macOS
    except tk.TclError:
        try:
            ventana.attributes("-zoomed", True)  # Linux (X11)
        except tk.TclError:
            pass
    if sys.platform.startswith("linux"):
        # Por si el gestor de ventanas ignora -zoomed
        ventana.geometry(f"{ancho}x{alto}+0+0")

    def alternar(event=None):
        actual = bool(ventana.attributes("-fullscreen"))
        ventana.attributes("-fullscreen", not actual)
        return "break"

    def salir_completa(event=None):
        if bool(ventana.attributes("-fullscreen")):
            ventana.attributes("-fullscreen", False)
            return "break"
        return None

    ventana.bind("<F11>", alternar)
    ventana.bind("<Escape>", salir_completa, add="+")


# ----------------------------------------------------------------------
# Bloques de interfaz reutilizables
# ----------------------------------------------------------------------
def encabezado(ventana, titulo, subtitulo=None, al_cerrar=None, icono=None):
    """
    Barra superior oscura con el título de la ventana, un subtítulo
    opcional (p. ej. el artículo de la norma) y un botón "Cerrar".
    """
    barra = tk.Frame(ventana, bg=C.ENCABEZADO)
    barra.pack(fill="x", side="top")

    interior = tk.Frame(barra, bg=C.ENCABEZADO)
    interior.pack(fill="x", padx=32, pady=(18, 16))

    textos = tk.Frame(interior, bg=C.ENCABEZADO)
    textos.pack(side="left", fill="x", expand=True)

    tk.Label(
        textos, text="HYDROLAB", font=fuente(8, "bold"),
        bg=C.ENCABEZADO, fg=C.ACENTO, anchor="w",
    ).pack(fill="x")
    texto_titulo = f"{icono}  {titulo}" if icono else titulo
    tk.Label(
        textos, text=texto_titulo, font=fuente(18, "bold"),
        bg=C.ENCABEZADO, fg="white", anchor="w",
    ).pack(fill="x")
    if subtitulo:
        tk.Label(
            textos, text=subtitulo, font=fuente(9),
            bg=C.ENCABEZADO, fg=C.ENCABEZADO_SUBTEXTO, anchor="w",
        ).pack(fill="x", pady=(2, 0))

    comando = al_cerrar or ventana.destroy
    tk.Button(
        interior, text="✕  Cerrar", font=fuente(10, "bold"),
        bg=C.ENCABEZADO_2, fg="white", padx=16, pady=6,
        command=comando,
    ).pack(side="right", anchor="center")

    # Línea de acento bajo el encabezado
    tk.Frame(ventana, bg=C.ACENTO, height=3).pack(fill="x", side="top")
    return barra


def tarjeta(padre, bg=None, borde=None, **pack):
    """Frame blanco con borde suave de 1 px (look de "card")."""
    marco = tk.Frame(
        padre, bg=bg or C.SUPERFICIE,
        highlightbackground=borde or C.BORDE, highlightcolor=borde or C.BORDE,
        highlightthickness=1, bd=0,
    )
    if pack:
        marco.pack(**pack)
    return marco


_TIPOS_BOTON = {
    "primario": (C.PRIMARIO, "white"),
    "exito": (C.EXITO_BOTON, "white"),
    "peligro": (C.PELIGRO, "white"),
    "secundario": (C.PRIMARIO_SUAVE, C.PRIMARIO),
    "oscuro": (C.ENCABEZADO_2, "white"),
    "informe": (C.INFORME, "white"),
}


def boton(padre, texto, comando, tipo="primario", tamano=11, **kw):
    """Botón plano con los colores del tema."""
    bg, fg = _TIPOS_BOTON.get(tipo, _TIPOS_BOTON["primario"])
    opciones = dict(
        text=texto, command=comando, font=fuente(tamano, "bold"),
        bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
        relief="flat", bd=0, cursor="hand2", padx=14, pady=8,
    )
    opciones.update(kw)
    return tk.Button(padre, **opciones)


def titulo_seccion(padre, texto, bg=None):
    """Título pequeño en mayúsculas para separar grupos de campos."""
    tk.Label(
        padre, text=texto.upper(), font=fuente(9, "bold"),
        bg=bg or padre.cget("bg"), fg=C.TEXTO_TENUE, anchor="w",
    ).pack(fill="x", pady=(14, 4))


def area_desplazable(padre, bg=None, ancho_max=None, padx=0):
    """
    Crea un área con scroll vertical dentro de `padre` y devuelve el
    Frame donde se ponen los widgets.

    Si se da `ancho_max`, el contenido no se estira más allá de ese
    ancho y queda centrado (así los formularios se ven bien aunque la
    ventana esté a pantalla completa).
    """
    bg = bg or C.FONDO
    contenedor = tk.Frame(padre, bg=bg)
    contenedor.pack(fill="both", expand=True)

    canvas = tk.Canvas(contenedor, bg=bg, highlightthickness=0, bd=0)
    canvas._hydrolab_scroll = True
    scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    marco = tk.Frame(canvas, bg=bg)
    ventana_id = canvas.create_window((0, 0), window=marco, anchor="n")

    def ajustar(event=None):
        ancho = canvas.winfo_width()
        util = ancho - 2 * padx
        if ancho_max:
            util = min(util, ancho_max)
        canvas.itemconfig(ventana_id, width=max(util, 200))
        canvas.coords(ventana_id, ancho // 2, 0)

    def region(event=None):
        # Región de scroll desde x=0 (no desde el borde del contenido
        # centrado) para que el centrado no se desplace.
        canvas.configure(scrollregion=(0, 0, canvas.winfo_width(), marco.winfo_reqheight()))

    def ajustar_todo(event=None):
        ajustar()
        region()

    marco.bind("<Configure>", region)
    canvas.bind("<Configure>", ajustar_todo)
    marco.canvas = canvas
    return marco


def layout_formulario(ventana, titulo, subtitulo=None, ancho_lateral=420, ancho_form=860):
    """
    Diseño estándar de las ventanas de cálculo:

        ┌──────────────── encabezado ────────────────┐
        │  formulario (con scroll)   │ panel lateral  │
        │  datos y valores calculados│ Calcular,      │
        │                            │ resultado final│
        │                            │ y Guardar      │
        └────────────────────────────┴────────────────┘

    Devuelve (cuerpo, lateral). Los campos van en `cuerpo`; el botón
    Calcular, el recuadro del resultado final y el botón Guardar van
    en `lateral`, que queda siempre visible.
    """
    encabezado(ventana, titulo, subtitulo)

    principal = tk.Frame(ventana, bg=C.FONDO)
    principal.pack(fill="both", expand=True)

    lateral_ext = tk.Frame(principal, bg=C.FONDO, width=ancho_lateral)
    lateral_ext.pack(side="right", fill="y", padx=(0, 32), pady=24)
    lateral_ext.pack_propagate(False)
    lateral = tarjeta(lateral_ext, fill="both", expand=True)
    lateral_interior = tk.Frame(lateral, bg=C.SUPERFICIE)
    lateral_interior.pack(fill="both", expand=True, padx=22, pady=20)
    tk.Label(
        lateral_interior, text="RESULTADOS", font=fuente(9, "bold"),
        bg=C.SUPERFICIE, fg=C.TEXTO_TENUE, anchor="w",
    ).pack(fill="x", pady=(0, 8))

    zona_form = tk.Frame(principal, bg=C.FONDO)
    zona_form.pack(side="left", fill="both", expand=True, padx=(32, 24), pady=24)
    marco = area_desplazable(zona_form, bg=C.FONDO, ancho_max=ancho_form)
    hoja = tarjeta(marco, fill="x", expand=True, pady=(0, 8))
    cuerpo = tk.Frame(hoja, bg=C.SUPERFICIE)
    cuerpo.pack(fill="both", expand=True, padx=28, pady=20)
    cuerpo.canvas = marco.canvas

    # Cuando la ventana termine de construirse, los textos del panel
    # lateral que no tengan ancho de línea se ajustan a su ancho.
    ventana.after_idle(lambda: _envolver_textos(lateral_interior, ANCHO_TEXTO_LATERAL))
    return cuerpo, lateral_interior


def _envolver_textos(contenedor, ancho):
    try:
        hijos = contenedor.winfo_children()
    except tk.TclError:
        return
    for w in hijos:
        if w.winfo_class() == "Label":
            if not int(w.cget("wraplength") or 0):
                w.configure(wraplength=ancho, justify="center")
            # Los resultados que venían lado a lado (p. ej. "Área" y
            # "Ancho") se apilan, porque el panel lateral es angosto.
            try:
                if w.pack_info().get("side") == "left":
                    w.pack_configure(side="top")
            except tk.TclError:
                pass
        _envolver_textos(w, ancho)


def ajustar_al_ancho(etiqueta, margen=0):
    """Hace que el texto de `etiqueta` se parta según el ancho de su contenedor."""
    def ajustar(event):
        etiqueta.configure(wraplength=max(event.width - margen, 80))
    etiqueta.master.bind("<Configure>", ajustar, add="+")
    return etiqueta


def marco_resultado(padre, titulo):
    """Recuadro verde del resultado final. Devuelve el Frame interior."""
    marco = tk.Frame(
        padre, bg=C.EXITO_FONDO, highlightbackground=C.EXITO,
        highlightcolor=C.EXITO, highlightthickness=1, bd=0,
    )
    marco.pack(fill="x", pady=(10, 15))
    tk.Label(
        marco, text=titulo, font=fuente(10, "bold"),
        bg=C.EXITO_FONDO, fg=C.EXITO, wraplength=ANCHO_TEXTO_LATERAL, justify="center",
    ).pack(pady=(12, 4), padx=10)
    return marco


# Ancho útil (px) para textos largos dentro del panel lateral
ANCHO_TEXTO_LATERAL = 340
