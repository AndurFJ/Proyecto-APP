"""
Utilidades de interfaz gráfica compartidas.

- `ajustar_geometria(ventana, ...)`: abre cualquier ventana (Tk o
  Toplevel) maximizada a pantalla completa. Se mantiene el nombre y la
  firma antiguos para que todas las ventanas sigan llamándola igual.
- `hacer_scrollable(canvas, marco)`: conecta un Canvas con el Frame de
  su contenido para que tenga scroll.

El aspecto visual (colores, fuentes, encabezados, tarjetas) vive en
tema.py.
"""

import tema


def ajustar_geometria(ventana, ancho=None, alto=None, ancho_minimo=None, alto_minimo=None, centrar=True):
    """
    Abre `ventana` (Tk o Toplevel) maximizada, a pantalla completa.

    Se conserva la firma anterior (ancho, alto, ...) para que las
    ventanas existentes y las nuevas sigan llamándola igual; los
    tamaños ya no se usan porque todas las ventanas del software abren
    ocupando toda la pantalla (ver tema.maximizar).

    Retorna (ancho, alto) de la pantalla.
    """
    tema.maximizar(ventana)
    return ventana.winfo_screenwidth(), ventana.winfo_screenheight()


def hacer_scrollable(canvas, marco_contenido):
    """
    Enlaza un Canvas con el Frame que contiene sus widgets para que el
    scrollregion se actualice solo y el Frame ocupe todo el ancho del
    Canvas. Evita repetir este mismo bloque en cada ventana.

    No crea el Canvas ni el Frame (eso lo sigue haciendo cada ventana,
    porque cada una decide su propio color de fondo), solo conecta el
    comportamiento de scroll + resize + rueda del mouse.
    """
    canvas._hydrolab_scroll = True  # la rueda del mouse la maneja tema.py
    ventana_id = canvas.create_window((0, 0), window=marco_contenido, anchor="nw")

    marco_contenido.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.bind(
        "<Configure>",
        lambda e: canvas.itemconfig(ventana_id, width=e.width),
    )
