"""
Utilidades de interfaz gráfica compartidas.

Centraliza el ajuste de tamaño y posición de las ventanas (Tk y
Toplevel) para que todas se comporten de forma UNIFORME y, sobre
todo, para que ninguna se salga de la pantalla en portátiles más
pequeños (p. ej. 15", con una altura útil real de 700-750 px una vez
descontada la barra de título del sistema operativo y la barra de
tareas/dock).

Uso típico dentro de cualquier ventana (Tk o Toplevel):

    from ui_utils import ajustar_geometria

    class MiVentana(tk.Toplevel):
        def __init__(self, master):
            super().__init__(master)
            self.title("Mi ventana")
            self.resizable(False, True)
            ajustar_geometria(self, ancho=620, alto=780)
            ...

`ajustar_geometria` nunca hace la ventana más grande de lo pedido:
si el tamaño solicitado cabe en la pantalla, se respeta tal cual: si
no cabe, se reduce (nunca por debajo de `alto_minimo`/`ancho_minimo`)
y la ventana queda centrada. Como casi todas las ventanas del
software ya tienen su propio Canvas + Scrollbar interno para el
contenido que más crece, reducir el alto no oculta información: solo
aparece la barra de scroll donde antes no hacía falta.
"""

# Espacio que se reserva SIEMPRE, para que la ventana no choque con
# la barra de título del sistema operativo (arriba) ni con la barra
# de tareas / dock (abajo).
MARGEN_SUPERIOR = 60
MARGEN_INFERIOR = 90


def ajustar_geometria(ventana, ancho, alto, ancho_minimo=360, alto_minimo=420, centrar=True):
    """
    Ajusta el tamaño de `ventana` (Tk o Toplevel) para que quepa en la
    pantalla disponible y la centra horizontal y verticalmente.

    Retorna (ancho_final, alto_final) por si la ventana que llama
    necesita conocer el alto real que le quedó disponible.
    """
    ventana.update_idletasks()

    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    alto_util = max(alto_minimo, pantalla_alto - MARGEN_SUPERIOR - MARGEN_INFERIOR)
    ancho_util = max(ancho_minimo, pantalla_ancho - 60)

    ancho_final = min(ancho, ancho_util)
    alto_final = min(alto, alto_util)

    if centrar:
        x = max(0, (pantalla_ancho - ancho_final) // 2)
        y = max(MARGEN_SUPERIOR // 2, (pantalla_alto - alto_final) // 2 - 10)
        ventana.geometry(f"{ancho_final}x{alto_final}+{x}+{y}")
    else:
        ventana.geometry(f"{ancho_final}x{alto_final}")

    return ancho_final, alto_final


def hacer_scrollable(canvas, marco_contenido):
    """
    Enlaza un Canvas con el Frame que contiene sus widgets para que el
    scrollregion se actualice solo y el Frame ocupe todo el ancho del
    Canvas. Evita repetir este mismo bloque en cada ventana.

    No crea el Canvas ni el Frame (eso lo sigue haciendo cada ventana,
    porque cada una decide su propio color de fondo), solo conecta el
    comportamiento de scroll + resize + rueda del mouse.
    """
    ventana_id = canvas.create_window((0, 0), window=marco_contenido, anchor="nw")

    marco_contenido.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.bind(
        "<Configure>",
        lambda e: canvas.itemconfig(ventana_id, width=e.width),
    )

    def _rueda(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _rueda)
