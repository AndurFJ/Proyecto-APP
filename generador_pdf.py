"""
Generador de Informe PDF.

Recopila todo lo que está guardado en EstadoProyecto (Datos
Preliminares, Caudal de Diseño, y cada proceso de PTAP/PTAR que ya
se haya calculado y guardado) y arma un informe PDF con tablas y
gráficas.

Cada vez que se implemente un proceso nuevo (desarenador, floculador,
etc.), basta con agregar aquí una función "_seccion_<proceso>" que
siga el mismo patrón, y añadirla en generar_informe_pdf() dentro del
"if EstadoProyecto.<proceso>_definido():".
"""

import os
import tempfile
from datetime import datetime
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from estado_proyecto import EstadoProyecto
from ptar_calculos import ESTRUCTURAS_PTAR

# ----------------------------------------------------------------------
# Fuente Unicode (Helvetica NO incluye ², ³, Δ, etc. y los deja en blanco).
# Se registra desde la carpeta local "fuentes/" para que funcione en
# cualquier equipo, sin depender de qué fuentes tenga instaladas Windows.
CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
CARPETA_FUENTES = os.path.join(CARPETA_SCRIPT, "fuentes")

FUENTE_NORMAL = "Helvetica"
FUENTE_NEGRITA = "Helvetica-Bold"

# Se busca en "fuentes/" y, si no está ahí, junto a este archivo (que es
# donde vienen los .ttf en el repositorio).
for _carpeta in (CARPETA_FUENTES, CARPETA_SCRIPT):
    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", os.path.join(_carpeta, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", os.path.join(_carpeta, "DejaVuSans-Bold.ttf")))
        FUENTE_NORMAL = "DejaVuSans"
        FUENTE_NEGRITA = "DejaVuSans-Bold"
        break
    except Exception:
        pass  # si no se encuentra la fuente, se sigue con Helvetica (símbolos especiales pueden fallar)

AZUL = colors.HexColor("#1F4E78")
VERDE = colors.HexColor("#1E8449")
VERDE_CLARO = colors.HexColor("#EAFAF1")
GRIS = colors.HexColor("#5D6D7E")
FONDO_TABLA = colors.HexColor("#EBF5FB")
BORDE_TABLA = colors.HexColor("#D5D8DC")


# ----------------------------------------------------------------------
def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "titulo", parent=base["Title"], textColor=AZUL, fontSize=20,
            fontName=FUENTE_NEGRITA,
        ),
        "seccion": ParagraphStyle(
            "seccion", parent=base["Heading1"], textColor=colors.white,
            backColor=AZUL, fontSize=13, spaceBefore=14, spaceAfter=10,
            leftIndent=6, borderPadding=6, fontName=FUENTE_NEGRITA,
        ),
        "subseccion": ParagraphStyle(
            "subseccion", parent=base["Heading2"], textColor=AZUL,
            fontSize=11, spaceBefore=10, spaceAfter=4, fontName=FUENTE_NEGRITA,
        ),
        "normal": ParagraphStyle("normal", parent=base["Normal"], fontName=FUENTE_NORMAL),
        "nota": ParagraphStyle(
            "nota", parent=base["Normal"], fontSize=8, textColor=GRIS,
            fontName=FUENTE_NORMAL,
        ),
    }


def _tabla_datos(pares, estilos, ancho_izq=7.5 * cm, ancho_der=7.5 * cm):
    """pares: lista de (etiqueta, valor) -> Table de dos columnas."""
    estilo_etq = ParagraphStyle("etq", parent=estilos["normal"], fontName=FUENTE_NEGRITA, fontSize=9)
    estilo_val = ParagraphStyle("val", parent=estilos["normal"], fontSize=9)
    filas = [[Paragraph(str(etiqueta), estilo_etq), Paragraph(str(valor), estilo_val)]
             for etiqueta, valor in pares]
    t = Table(filas, colWidths=[ancho_izq, ancho_der])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), FONDO_TABLA),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDE_TABLA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _marco_resultado_final(texto, estilos, ancho=16 * cm):
    estilo_marco = ParagraphStyle(
        "marco", parent=estilos["normal"], fontName=FUENTE_NEGRITA,
        fontSize=12, textColor=VERDE, alignment=1, leading=16,
    )
    contenido = Paragraph(texto, estilo_marco)
    t = Table([[contenido]], colWidths=[ancho])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), VERDE_CLARO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 1.3, VERDE),
    ]))
    return t


# ----------------------------------------------------------------------
def _grafica_proyeccion_png():
    """Genera un PNG temporal con la gráfica de proyección poblacional."""
    df = EstadoProyecto.tabla_proyeccion
    fig = Figure(figsize=(6.6, 3.6), dpi=150)
    ax = fig.add_subplot(111)
    ax.plot(df["AÑO"], df["Aritmético"], marker="o", markersize=2, label="Aritmético")
    ax.plot(df["AÑO"], df["Geométrico"], marker="s", markersize=2, label="Geométrico")
    ax.plot(df["AÑO"], df["Exponencial"], marker="^", markersize=2, label="Exponencial")
    ax.set_xlabel("Año")
    ax.set_ylabel("Población (hab)")
    ax.set_title("Proyección poblacional")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()

    ruta = os.path.join(tempfile.gettempdir(), "grafica_proyeccion_informe_ptap.png")
    fig.savefig(ruta, dpi=150)
    return ruta


# ----------------------------------------------------------------------
def _seccion_datos_preliminares(story, estilos):
    story.append(Paragraph("1. Datos Preliminares", estilos["seccion"]))

    pares = [
        ("Departamento", EstadoProyecto.departamento),
        ("Municipio", EstadoProyecto.municipio),
        ("Área geográfica", EstadoProyecto.area_geografica),
        ("Año de inicio del proyecto", EstadoProyecto.año_inicio),
        ("Periodo de diseño (años)", EstadoProyecto.periodo_diseño),
        ("Año horizonte", EstadoProyecto.año_horizonte),
        ("Método de diseño", EstadoProyecto.metodo_diseño),
        ("Población de diseño (hab)", f"{EstadoProyecto.poblacion_diseño:,.0f}"),
    ]
    story.append(_tabla_datos(pares, estilos))
    story.append(Spacer(1, 12))

    try:
        ruta_grafica = _grafica_proyeccion_png()
        story.append(Image(ruta_grafica, width=16 * cm, height=16 * cm * 3.6 / 6.6))
        story.append(Spacer(1, 10))
    except Exception:
        pass

    story.append(Paragraph("Proyección poblacional completa", estilos["subseccion"]))

    df = EstadoProyecto.tabla_proyeccion
    encabezado = ["Año", "Aritmético", "Geométrico", "Exponencial"]
    filas = [encabezado]
    for _, fila in df.iterrows():
        filas.append([
            str(int(fila["AÑO"])),
            f'{fila["Aritmético"]:,.0f}',
            f'{fila["Geométrico"]:,.0f}',
            f'{fila["Exponencial"]:,.0f}',
        ])
    tabla = Table(filas, colWidths=[3 * cm, 4.33 * cm, 4.33 * cm, 4.33 * cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FUENTE_NEGRITA),
        ("FONTNAME", (0, 1), (-1, -1), FUENTE_NORMAL),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDE_TABLA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9F9")]),
    ]))
    story.append(tabla)
    story.append(PageBreak())


# ----------------------------------------------------------------------
def _seccion_caudal_diseno(story, estilos):
    story.append(Paragraph("2. Caudal de Diseño", estilos["seccion"]))

    pares = [
        ("Nivel de complejidad", EstadoProyecto.nivel_complejidad),
        ("Dotación neta máxima (L/hab·día)", f"{EstadoProyecto.dotacion_neta_max:,.0f}"),
        ("Coeficiente de afectación", f"{EstadoProyecto.coef_afectacion:,.2f}"),
        ("Dotación neta (L/hab·día)", f"{EstadoProyecto.dotacion_neta:,.1f}"),
        ("% Pérdidas técnicas", f"{EstadoProyecto.porc_perdidas * 100:,.1f}%"),
        ("Dotación bruta (L/hab·día)", f"{EstadoProyecto.dotacion_bruta:,.1f}"),
        ("Caudal medio diario — Qmd (L/s)", f"{EstadoProyecto.qmd:,.2f}"),
        ("K1 (coef. día máximo)", f"{EstadoProyecto.k1:,.2f}"),
        ("K2 (coef. hora máxima)", f"{EstadoProyecto.k2:,.2f}"),
        ("Caudal máximo diario — QMD (L/s)", f"{EstadoProyecto.q_max_diario:,.2f}"),
        ("Caudal máximo horario — QMH (L/s)", f"{EstadoProyecto.q_max_horario:,.2f}"),
        ("¿Almacenamiento en casa?", EstadoProyecto.almacenamiento_en_casa),
    ]
    story.append(_tabla_datos(pares, estilos))
    story.append(Spacer(1, 12))

    story.append(_marco_resultado_final(
        f"CAUDAL DE DISEÑO: {EstadoProyecto.caudal_diseño_Ls:,.2f} L/s   "
        f"({EstadoProyecto.caudal_diseño_m3s:,.5f} m³/s)",
        estilos,
    ))
    story.append(PageBreak())


# ----------------------------------------------------------------------
def _seccion_bocatoma_rejilla(story, estilos):
    story.append(Paragraph("3. Captación — Bocatoma con Rejilla", estilos["seccion"]))

    pares = [
        ("Caudal de diseño (m³/s)", f"{EstadoProyecto.caudal_diseño_m3s:,.5f}"),
        ("Velocidad efectiva del flujo — Vf (m/s)", f"{EstadoProyecto.vf:,.3f}"),
        ("Área de captación — Ac (m²)", f"{EstadoProyecto.area_captacion:,.4f}"),
        ("Área de captación efectiva (m²)", f"{EstadoProyecto.area_captacion_efectiva:,.4f}"),
        ("Tipo de inclinación", EstadoProyecto.tipo_inclinacion),
        ("Ángulo de inclinación (°)", f"{EstadoProyecto.angulo_inclinacion:,.1f}"),
        ("Tipo de grava", EstadoProyecto.tipo_grava),
        ("Separación entre barrotes — z (m)", f"{EstadoProyecto.valor_z:,.3f}"),
        ("Forma del barrote", EstadoProyecto.forma_barrote),
        ("Coeficiente de pérdidas (Kirschmer)", f"{EstadoProyecto.coef_forma_barrote:,.3f}"),
        ("Diámetro del barrote (in)", f"{EstadoProyecto.diametro_barrote_in:,.2f}"),
        ("Espesor del barrote — s (m)", f"{EstadoProyecto.s_barrote:,.4f}"),
        ("Borde libre (m)", f"{EstadoProyecto.borde_libre:,.3f}"),
        ("Altura húmeda de la rejilla — Hrh (m)", f"{EstadoProyecto.hrh:,.3f}"),
        ("N° de espacios (n+1)", f"{EstadoProyecto.num_espacios:,.2f}"),
        ("N° de barrotes (n)", f"{EstadoProyecto.num_barrotes:,.2f}"),
        ("Longitud sumergida — Lrh (m)", f"{EstadoProyecto.longitud_sumergida:,.3f}"),
        ("Longitud total del barrote — Lrt (m)", f"{EstadoProyecto.longitud_total_barrote:,.1f}"),
    ]
    story.append(_tabla_datos(pares, estilos))
    story.append(Spacer(1, 12))

    story.append(_marco_resultado_final(
        f"Área de la rejilla: {EstadoProyecto.area_rejilla:,.3f} m²  —  "
        f"Ancho: {EstadoProyecto.ancho_rejilla:,.3f} m<br/>"
        f"Pérdidas en la rejilla (Δh): {EstadoProyecto.perdidas_rejilla:,.4f} m",
        estilos,
    ))
    story.append(PageBreak())


# ----------------------------------------------------------------------
def _seccion_desarenador(story, estilos):
    story.append(Paragraph("4. Desarenador", estilos["seccion"]))
    story.append(Paragraph(
        "Diseño por velocidad controlada (L = Vh·t, Ac = Q/Vh); Vs se usa solo como "
        "verificación de asentamiento, no para dimensionar directamente.",
        estilos["nota"],
    ))
    story.append(Spacer(1, 6))

    pares = [
        ("Número de unidades en paralelo", f"{EstadoProyecto.desarenador_num_unidades:,.0f}"),
        ("Caudal por unidad (m³/s)", f"{EstadoProyecto.desarenador_q_unidad:,.5f}"),
        ("Temperatura del agua (°C)", f"{EstadoProyecto.desarenador_temperatura:,.1f}"),
        ("Viscosidad dinámica — μ (Pa·s)", f"{EstadoProyecto.desarenador_viscosidad:,.6f}"),
        ("Densidad del agua (kg/m³)", f"{EstadoProyecto.desarenador_densidad_agua:,.1f}"),
        ("Diámetro de partícula a remover (mm)", f"{EstadoProyecto.desarenador_d_particula_mm:,.2f}"),
        ("Peso específico de la arena (g/cm³)", f"{EstadoProyecto.desarenador_peso_especifico:,.2f}"),
        ("Velocidad de asentamiento — Vs (m/s)", f"{EstadoProyecto.desarenador_vs:,.5f}"),
        ("Número de Reynolds de la partícula", f"{EstadoProyecto.desarenador_reynolds:,.3f}"),
        ("Velocidad horizontal — Vh (m/s)", f"{EstadoProyecto.desarenador_vh:,.3f}"),
        ("Relación Vh / Vs", f"{EstadoProyecto.desarenador_relacion_vh_vs:,.1f}"),
        ("Tiempo de retención de diseño (min)", f"{EstadoProyecto.desarenador_t_retencion_min:,.1f}"),
        ("Relación constructiva B/H", f"{EstadoProyecto.desarenador_relacion_bh:,.2f}"),
        ("Área de referencia ideal — As=Q/Vs, informativa (m²)", f"{EstadoProyecto.desarenador_area_superficial:,.3f}"),
        ("Vs requerida para asentar — H/t (m/s)", f"{EstadoProyecto.desarenador_vs_requerida:,.5f}"),
        ("¿Cumple asentamiento? (Vs real ≥ Vs requerida)",
         "Sí" if EstadoProyecto.desarenador_cumple_asentamiento else "No"),
        ("Número de tramos en serpentín", f"{EstadoProyecto.desarenador_num_tramos:,.0f}"),
        ("Longitud desarrollada total — todos los tramos (m)", f"{EstadoProyecto.desarenador_longitud_total:,.2f}"),
        ("Ancho total de la estructura plegada (m)", f"{EstadoProyecto.desarenador_ancho_total_estructura:,.3f}"),
        ("Pendiente de evacuación de arenas (%)", f"{EstadoProyecto.desarenador_pendiente:,.1f}"),
    ]
    story.append(_tabla_datos(pares, estilos))
    story.append(Spacer(1, 12))

    story.append(_marco_resultado_final(
        f"DIMENSIONES POR TRAMO: {EstadoProyecto.desarenador_longitud:,.2f} × "
        f"{EstadoProyecto.desarenador_ancho:,.2f} × "
        f"{EstadoProyecto.desarenador_profundidad:,.2f} m (L×B×H)",
        estilos,
    ))
    story.append(PageBreak())


# ----------------------------------------------------------------------
# PTAR — todas las estructuras guardan el mismo formato (ver
# ptar_calculos.py), así que una sola función escribe cualquiera de ellas.
def _tabla_verificaciones(verificaciones, estilos):
    estilo = ParagraphStyle("verif", parent=estilos["normal"], fontSize=8.5)
    filas = []
    for texto, cumple in verificaciones:
        marca = "Cumple" if cumple else "No cumple"
        color = "#1E8449" if cumple else "#B9770E"
        filas.append([Paragraph(escape(str(texto)), estilo),
                      Paragraph(f'<font color="{color}"><b>{marca}</b></font>', estilo)])
    t = Table(filas, colWidths=[12.5 * cm, 2.5 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDE_TABLA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _seccion_ptar(numero, atributo, titulo):
    def escribir(story, estilos):
        guardado = getattr(EstadoProyecto, atributo)
        story.append(Paragraph(f"PTAR {numero}. {titulo}", estilos["seccion"]))
        pares = [(escape(etq), escape(str(val))) for etq, val in guardado["filas"]]
        story.append(_tabla_datos(pares, estilos))
        if guardado["verificaciones"]:
            story.append(Paragraph("Verificación — Res. 0330 de 2017 (mod. Res. 799 de 2021)",
                                   estilos["subseccion"]))
            story.append(_tabla_verificaciones(guardado["verificaciones"], estilos))
        story.append(Spacer(1, 12))
        story.append(_marco_resultado_final(
            escape(guardado["final"]).replace("\n", "<br/>"), estilos))
        story.append(PageBreak())
    return escribir


def _secciones_ptar():
    return [
        (lambda a=atributo: EstadoProyecto.ptar_definido(a), _seccion_ptar(i, atributo, titulo))
        for i, (atributo, titulo) in enumerate(ESTRUCTURAS_PTAR, start=1)
    ]


# ----------------------------------------------------------------------
# Mapa: (¿está definida esta sección?) -> función que la escribe.
# Para agregar un proceso nuevo, solo se añade una tupla aquí.
SECCIONES = [
    (lambda: EstadoProyecto.esta_definido(), _seccion_datos_preliminares),
    (lambda: EstadoProyecto.caudal_definido(), _seccion_caudal_diseno),
    (lambda: EstadoProyecto.rejilla_definida(), _seccion_bocatoma_rejilla),
    (lambda: EstadoProyecto.desarenador_definido(), _seccion_desarenador),
] + _secciones_ptar()


def generar_informe_pdf(ruta_salida):
    """
    Genera el informe PDF con todos los resultados guardados hasta el
    momento en EstadoProyecto. Retorna la ruta del archivo generado.
    """
    if not EstadoProyecto.esta_definido():
        raise ValueError(
            "No hay datos preliminares definidos todavía. "
            "Complete al menos el Paso ① antes de exportar el informe."
        )

    doc = SimpleDocTemplate(
        ruta_salida, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    estilos = _estilos()
    story = []

    story.append(Paragraph("INFORME DE DISEÑO", estilos["titulo"]))
    hay_ptar = any(EstadoProyecto.ptar_definido(a) for a, _ in ESTRUCTURAS_PTAR)
    hay_ptap = EstadoProyecto.caudal_definido()
    if hay_ptar and hay_ptap:
        subtitulo = "Planta de Tratamiento de Agua Potable (PTAP) y de Aguas Residuales (PTAR)"
    elif hay_ptar:
        subtitulo = "Planta de Tratamiento de Aguas Residuales (PTAR)"
    else:
        subtitulo = "Planta de Tratamiento de Agua Potable (PTAP)"
    story.append(Paragraph(subtitulo, estilos["subseccion"]))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilos["nota"],
    ))
    story.append(Spacer(1, 14))

    for condicion, funcion_seccion in SECCIONES:
        if condicion():
            funcion_seccion(story, estilos)

    if story and isinstance(story[-1], PageBreak):
        story.pop()  # evitar una última página en blanco

    doc.build(story)
    return ruta_salida
