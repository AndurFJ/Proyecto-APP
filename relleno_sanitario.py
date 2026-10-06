"""
Cálculos del módulo de Diseño de Operación de Relleno Sanitario (DORS).

Replica, fórmula por fórmula, la hoja de cálculo DORS (hojas "Menu" y
"Proyección Poblacional"): cálculo poblacional para el diseño de un
relleno sanitario, con 3 métodos de cálculo para obtener los datos base
y 3 métodos de proyección (aritmético, geométrico y exponencial) a 50
años.

Métodos de cálculo (celda "Método de cálculo" del Excel):

1. Base de datos DANE: toma dos datos de la base DANE (2018-2042) del
   municipio/área elegidos:
       Tu = 2042 si el año de inicio < 2022; si no, min(año de inicio, 2042)
       T1 = 2038 si el año de inicio < 2022; si no, Tu - 4
   y Pu, P1 = población DANE en Tu y T1.
2. Ingreso manual de datos censales (mínimo 2): Tu = año más reciente,
   T1 = año más antiguo, Pu y P1 sus poblaciones.
3. Un dato de censo + una tasa de crecimiento: T0, P0 y r (decimal).

La proyección empieza en el año de inicio (métodos 1 y 2) o en el año
base del censo (método 3) y cubre 50 años. Fórmulas (métodos 1 y 2):

    Aritmético:  P = Pu + (Pu - P1)/(Tu - T1) · (t - Tu)
    Geométrico:  P = Pu · (Pu/P1)^((t - Tu)/(Tu - T1))
    Exponencial: P = Pu · e^((ln Pu - ln P1)·(t - Tu)/(Tu - T1))

Método 3:

    Aritmético:  P = P0 · (1 + r·(t - T0))
    Geométrico:  P = P0 · (1 + r)^(t - T0)
    Exponencial: P = P0 · e^(ln(1 + r)·(t - T0))

Cada valor se redondea a 0 decimales igual que ROUND() de Excel (la
mitad se aleja de cero; el round() de Python redondea al par).

Este archivo no depende de tkinter: se puede probar o reutilizar sin
abrir ninguna ventana.
"""

import math

import pandas as pd

import datos_dane


METODO_DANE = 1
METODO_MANUAL = 2
METODO_TASA = 3

NOMBRES_METODO = {
    METODO_DANE: "Base de datos DANE",
    METODO_MANUAL: "Ingreso manual de datos censales (mínimo 2)",
    METODO_TASA: "Un dato de censo + una tasa de crecimiento",
}

AÑOS_PROYECCION = 50
AÑO_DANE_MIN = 2018
AÑO_DANE_MAX = 2042

COLUMNAS_PROYECCION = ["Aritmético", "Geométrico", "Exponencial"]


def redondear_excel(valor):
    """ROUND(valor, 0) de Excel: la mitad se redondea alejándose de cero."""
    if valor >= 0:
        return int(math.floor(valor + 0.5))
    return -int(math.floor(-valor + 0.5))


# ----------------------------------------------------------------------
def años_base_dane(año_inicio):
    """
    Años (Tu, T1) que el método 1 toma de la base DANE, tal como las
    celdas "Año reciente usado" y "Año antiguo usado" del Excel.
    """
    if año_inicio < 2022:
        return AÑO_DANE_MAX, AÑO_DANE_MAX - 4
    tu = min(año_inicio, AÑO_DANE_MAX)
    return tu, tu - 4


def aviso_metodo_dane(año_inicio):
    """Texto de aviso cuando el año de inicio obliga a usar 2038-2042."""
    if año_inicio < 2022 or año_inicio > AÑO_DANE_MAX:
        tu, t1 = años_base_dane(año_inicio)
        return (
            f"Aviso: con el año de inicio {año_inicio} no hay 5 datos DANE "
            f"anteriores dentro del rango {AÑO_DANE_MIN}-{AÑO_DANE_MAX}. "
            f"Se usan los datos {t1}-{tu} para calcular las tasas."
        )
    return ""


def parametros_metodo_dane(dpnom, municipio, area, año_inicio):
    """Método 1. Retorna dict con tu, t1, pu, p1 tomados de la base DANE."""
    tu, t1 = años_base_dane(año_inicio)
    datos = datos_dane.obtener_datos_municipio(dpnom, municipio, area)
    if datos.empty:
        raise ValueError("No hay datos DANE para ese departamento, municipio y área.")
    por_año = dict(zip(datos["AÑO"].astype(int), datos["TOTAL"].astype(int)))
    if tu not in por_año or t1 not in por_año:
        raise ValueError(f"La base DANE no tiene datos para {t1} y {tu} en ese municipio.")
    return {
        "metodo": METODO_DANE,
        "tu": tu, "t1": t1,
        "pu": por_año[tu], "p1": por_año[t1],
    }


def parametros_metodo_manual(puntos):
    """
    Método 2. `puntos` es una lista de (año, población) ya completos.
    Usa solo el dato más reciente (Tu, Pu) y el más antiguo (T1, P1).
    """
    if len(puntos) < 2:
        raise ValueError("Ingrese al menos 2 datos (año y población) para el método 2.")
    años = [a for a, _ in puntos]
    if len(set(años)) != len(años):
        raise ValueError("Hay años repetidos en la tabla; deben ser todos diferentes.")
    if any(p <= 0 for _, p in puntos):
        raise ValueError("Las poblaciones deben ser mayores que cero.")
    por_año = dict(puntos)
    tu, t1 = max(años), min(años)
    return {
        "metodo": METODO_MANUAL,
        "tu": tu, "t1": t1,
        "pu": por_año[tu], "p1": por_año[t1],
    }


def parametros_metodo_tasa(año_base, tasa_porcentaje, poblacion_base):
    """Método 3. Un dato de censo + tasa de crecimiento anual en %."""
    if poblacion_base <= 0:
        raise ValueError("La población del año base debe ser mayor que cero.")
    if tasa_porcentaje <= -100:
        raise ValueError("La tasa de crecimiento debe ser mayor que -100 %.")
    return {
        "metodo": METODO_TASA,
        "t0": año_base, "p0": poblacion_base,
        "r": tasa_porcentaje / 100,
    }


# ----------------------------------------------------------------------
def poblacion_en(params, t):
    """(aritmético, geométrico, exponencial) sin redondear para el año t."""
    if params["metodo"] == METODO_TASA:
        p0, r, dt = params["p0"], params["r"], t - params["t0"]
        return (
            p0 * (1 + r * dt),
            p0 * (1 + r) ** dt,
            p0 * math.exp(math.log(1 + r) * dt),
        )

    pu, p1, tu, t1 = params["pu"], params["p1"], params["tu"], params["t1"]
    n = tu - t1
    return (
        pu + (pu - p1) / n * (t - tu),
        pu * (pu / p1) ** ((t - tu) / n),
        pu * math.exp((math.log(pu) - math.log(p1)) * (t - tu) / n),
    )


def año_inicial_proyeccion(params, año_inicio):
    """Métodos 1 y 2 empiezan en el año de inicio; el 3, en el año base."""
    return params["t0"] if params["metodo"] == METODO_TASA else año_inicio


def proyectar(params, año_inicial, años=AÑOS_PROYECCION):
    """DataFrame (AÑO, Aritmético, Geométrico, Exponencial) de `años` filas."""
    filas = []
    for t in range(año_inicial, año_inicial + años):
        arit, geom, expo = poblacion_en(params, t)
        filas.append({
            "AÑO": t,
            "Aritmético": redondear_excel(arit),
            "Geométrico": redondear_excel(geom),
            "Exponencial": redondear_excel(expo),
        })
    return pd.DataFrame(filas)


def descripcion_parametros(params):
    """Lista de (etiqueta, valor) con los 'cálculos internos' del Excel."""
    if params["metodo"] == METODO_TASA:
        return [
            ("Año base, T0", f"{params['t0']}"),
            ("Población base, P0", f"{params['p0']:,.0f} hab"),
            ("Tasa de crecimiento, r", f"{params['r'] * 100:,.3f} %"),
        ]
    return [
        ("Año reciente, Tu", f"{params['tu']}"),
        ("Población reciente, Pu", f"{params['pu']:,.0f} hab"),
        ("Año antiguo, T1", f"{params['t1']}"),
        ("Población antigua, P1", f"{params['p1']:,.0f} hab"),
    ]
