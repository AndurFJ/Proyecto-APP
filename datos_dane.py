"""
Carga y consulta de la base de datos poblacional municipal del DANE
(2018-2042), usada por el módulo de Datos Preliminares.
"""

import os
import pandas as pd

CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(CARPETA_SCRIPT, "pob_municipal.csv")

_df_cache = None


def cargar_datos():
    """Carga (una sola vez) y retorna el DataFrame completo del DANE."""
    global _df_cache
    if _df_cache is None:
        df = pd.read_csv(RUTA_CSV, dtype={"DP": str, "MPIO": str})
        df = df.dropna(subset=["AÑO", "TOTAL"]).reset_index(drop=True)
        df["AÑO"] = df["AÑO"].astype(int)
        df["TOTAL"] = df["TOTAL"].astype(int)
        _df_cache = df
    return _df_cache


def obtener_departamentos():
    """Retorna lista de nombres de departamento, ordenada alfabéticamente."""
    df = cargar_datos()
    return sorted(df["DPNOM"].unique().tolist())


def obtener_municipios(dpnom):
    """Retorna lista de nombres de municipio para un departamento dado."""
    df = cargar_datos()
    return sorted(df.loc[df["DPNOM"] == dpnom, "DPMP"].unique().tolist())


def obtener_datos_municipio(dpnom, mpio_nombre, area):
    """
    Retorna un DataFrame (AÑO, TOTAL) para el municipio y área dados,
    ordenado por año.
    """
    df = cargar_datos()
    filtro = (
        (df["DPNOM"] == dpnom)
        & (df["DPMP"] == mpio_nombre)
        & (df["ÁREA GEOGRÁFICA"] == area)
    )
    return df.loc[filtro, ["AÑO", "TOTAL"]].sort_values("AÑO").reset_index(drop=True)


AÑO_CENSO_DESDE = 2018
AÑO_CENSO_HASTA = 2025


def obtener_serie_censo(datos):
    """
    Retorna, del DataFrame (AÑO, TOTAL) de un municipio/área, únicamente
    los datos entre AÑO_CENSO_DESDE (2018) y AÑO_CENSO_HASTA (2025)
    inclusive — el rango fijo que pide el profesor para calcular la tasa
    de crecimiento (independiente del año de inicio del proyecto).
    """
    subset = datos[
        (datos["AÑO"] >= AÑO_CENSO_DESDE) & (datos["AÑO"] <= AÑO_CENSO_HASTA)
    ].sort_values("AÑO")
    return subset.reset_index(drop=True)
