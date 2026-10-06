"""
Criterios normativos del módulo PTAR (Planta de Tratamiento de Aguas
Residuales).

Todos los rangos y valores por defecto que usan los cálculos de PTAR
están aquí como constantes, cada uno con el artículo de donde sale,
para poder revisarlos o actualizarlos en un solo lugar sin tocar las
fórmulas ni las ventanas.

Fuente principal: Resolución 0330 de 2017 (RAS), modificada por la
Resolución 799 de 2021 — Título 2, Capítulo de alcantarillado
(Art. 134) y Capítulo de sistemas de tratamiento de aguas residuales
(Arts. 166 a 211).

Cuando la resolución NO fija un valor (p. ej. aportes comerciales,
eficiencia típica de un UASB), se indica explícitamente que el valor
es "típico de literatura" o "tomado del Excel PTAR del proyecto", y
siempre queda como dato editable en la ventana correspondiente.
"""

# ----------------------------------------------------------------------
# CAUDAL DE AGUAS RESIDUALES — Res. 0330/2017, Art. 134 y Art. 166
# ----------------------------------------------------------------------
COEF_RETORNO_DEFECTO = 0.85              # Art. 134: sin datos de campo, CR = 0,85
INFILTRACION_DEFECTO_LS_HA = 0.1         # Art. 134: sin información, 0,1 L/s·ha
CONEXIONES_ERRADAS_MAX_LS_HA = 0.2       # Art. 134: valor máximo 0,2 L/s·ha
FACTOR_MAYORACION_MIN = 1.4              # Art. 134: F entre 1,4 y 3,8
FACTOR_MAYORACION_MAX = 3.8

# Art. 43 (Tabla de dotación neta máxima según altura sobre el nivel
# del mar). Se usa solo si aún no se ha calculado el caudal de la PTAP;
# si ya existe, se toma la dotación neta de la PTAP.
DOTACION_NETA_POR_ALTITUD = {
    "> 2000 m.s.n.m.": 120,
    "1000 - 2000 m.s.n.m.": 130,
    "< 1000 m.s.n.m.": 140,
}

# Aportes unitarios no domésticos. La Res. 0330 pide estimarlos con
# información de la localidad; estos valores son los del Excel PTAR del
# proyecto (RAS 2000, Título D, D.3.3) y quedan editables.
APORTE_INDUSTRIAL_LS_HA = 1.0
APORTE_COMERCIAL_LS_HA = 0.15
APORTE_INSTITUCIONAL_LS_HA = 0.5
PORC_AREA_INDUSTRIAL = 0.05
PORC_AREA_COMERCIAL = 0.12
PORC_AREA_INSTITUCIONAL = 0.06
PORC_AREA_URBANA = 0.94

# Art. 166: plantas con caudal de diseño ≤ 30 L/s (excepto lagunas) se
# proyectan con 3 veces el caudal medio de tiempo seco, sin sumar
# infiltración ni conexiones erradas.
LIMITE_PLANTA_PEQUEÑA_LS = 30.0
FACTOR_PLANTA_PEQUEÑA = 3.0

# Caudal mínimo (para verificar velocidades mínimas en canales). La
# Res. 0330 no fija este factor; 0,5·Qmed es un criterio usual.
FACTOR_CAUDAL_MINIMO = 0.5


# ----------------------------------------------------------------------
# REJILLAS — Art. 186
# ----------------------------------------------------------------------
SEPARACION_REJA_GRUESA_CM = (4.0, 10.0)  # Art. 186
SEPARACION_REJA_MEDIA_CM = (2.0, 4.0)    # Art. 186
SEPARACION_REJA_FINA_CM = (1.0, 2.0)     # Art. 186
VEL_MAX_REJILLA_QMAX = 1.2               # Art. 186: 1,2 m/s para caudal máximo
VEL_MIN_REJILLA_QMIN = 0.3               # Art. 186: 0,3 m/s para caudal mínimo
CAUDAL_LIMPIEZA_MECANICA_LS = 100.0      # Art. 186: Qmed ≥ 100 L/s → limpieza mecánica
# Valores de diseño típicos (literatura), editables en la ventana:
SEPARACION_REJILLA_DEFECTO_CM = 2.5
ESPESOR_BARRA_DEFECTO_CM = 1.0
ANGULO_REJILLA_DEFECTO = 60.0            # limpieza manual: 45° a 60°
PENDIENTE_CANAL_DEFECTO = 0.001          # m/m
MANNING_CONCRETO = 0.013
BETA_KIRSCHMER_DEFECTO = 2.42            # barra rectangular


# ----------------------------------------------------------------------
# DESARENADOR (aguas residuales) — Art. 188
# ----------------------------------------------------------------------
DIAMETRO_PARTICULA_DESARENADOR_MM = 0.3  # Art. 188: diámetro mínimo 0,3 mm
VS_DESARENADOR_MS = 0.03                 # Art. 188: velocidad de decantación 0,03 m/s
VH_DESARENADOR_MS = 0.3                  # Art. 188: 0,3 m/s (velocidad constante)
TOLERANCIA_VH_DESARENADOR = 0.05         # criterio de este software (±)
UNIDADES_MIN_DESARENADOR = 2             # Art. 188: mínimo dos unidades
FACTOR_SEGURIDAD_LONGITUD = 1.5          # típico de literatura (turbulencia)
RELACION_BH_DESARENADOR = 1.0
ARENA_RETENIDA_L_M3 = 0.03               # típico: 0,004-0,037 L de arena por m³
DIAS_LIMPIEZA_DESARENADOR = 7


# ----------------------------------------------------------------------
# TRAMPA DE GRASAS — Art. 185 (sistemas centralizados) y Art. 172
# ----------------------------------------------------------------------
TR_MIN_TRAMPA_GRASAS_MIN = 2.5           # Art. 172: retención mínima 2,5 min
RELACION_LB_TRAMPA = (1.0, 3.0)          # Art. 172: L:B entre 1:1 y 3:1
PROFUNDIDAD_MIN_TRAMPA_M = 0.35          # Art. 172: profundidad útil mínima 0,35 m
CAUDAL_DESENGRASADOR_AIREADO_LS = 100.0  # Art. 185: ≥100 L/s puede usarse desengrasador aireado
TR_TRAMPA_DEFECTO_MIN = 3.0
PROFUNDIDAD_TRAMPA_DEFECTO_M = 1.0


# ----------------------------------------------------------------------
# REACTOR UASB — Art. 191 (Tablas 31, 32 y 33)
# ----------------------------------------------------------------------
# Tabla 31: tiempo de retención hidráulica (h) según temperatura (°C)
TRH_UASB_POR_TEMPERATURA = [
    # (T mínima, T máxima, TRH mínimo, TRH máximo)
    (16.0, 19.99, 10.0, 14.0),
    (20.0, 26.0, 6.0, 9.0),
    (26.01, 99.0, 6.0, None),            # > 26 °C: TRH > 6 h
]
# Tabla 32: velocidad ascensional (m/h)
VASC_UASB_MEDIA = (0.5, 0.7)
VASC_UASB_MAXIMA = (0.9, 1.1)
VASC_UASB_PICO_MAX = 1.5
PROFUNDIDAD_UASB = (4.5, 6.0)            # Art. 191: entre 4,5 y 6 m
ALTURA_SGSL_M = 2.5                      # Art. 191: separador GSL de 2,5 m, placas a 45°
# Tabla 33: área de influencia por distribuidor, entre 0,5 y 5,0 m²
AREA_DISTRIBUIDOR_RANGO_M2 = (0.5, 5.0)
AREA_DISTRIBUIDOR_DEFECTO_M2 = 2.0
# Valores típicos de literatura (Art. 184/Tabla 29 en imagen), editables:
DBO_AFLUENTE_DEFECTO_MGL = 250.0
DQO_AFLUENTE_DEFECTO_MGL = 500.0
EFICIENCIA_DBO_UASB = 0.65
COEF_PRODUCCION_LODO_UASB = 0.18         # kg SST / kg DQO aplicada
TEMPERATURA_DEFECTO_C = 24.0


# ----------------------------------------------------------------------
# LAGUNA FACULTATIVA — Art. 199 y Art. 201
# ----------------------------------------------------------------------
TRH_LAGUNA_FACULTATIVA_D = (5.0, 30.0)   # Art. 199
PROFUNDIDAD_LAGUNA_FACULTATIVA = (1.5, 2.5)  # Art. 199
CARGA_SUPERFICIAL_FACULTATIVA = (100.0, 350.0)  # Art. 199, kg DBO5/ha·día
BORDE_LIBRE_LAGUNA = (0.3, 0.5)          # Art. 201 (0,51-0,8 m con alta turbulencia)
# Constante de remoción de primer orden (mezcla completa) — literatura:
K_LAGUNA_20C = 0.3                       # d⁻¹
THETA_LAGUNA = 1.05
RELACION_LB_LAGUNA_DEFECTO = 3.0


# ----------------------------------------------------------------------
# LECHOS DE SECADO — Art. 211, Tabla 44
# ----------------------------------------------------------------------
# tipo: (área m²/hab mín., máx., carga kg SS/m²·año mín., máx.)
LECHOS_SECADO_TABLA_44 = {
    "Primario digerido": (0.10, 0.10, 120.0, 150.0),
    "Filtro percolador digerido": (0.12, 0.16, 90.0, 120.0),
    "Lodos activados digeridos": (0.16, 0.24, 60.0, 100.0),
}
FACTOR_LECHO_CUBIERTO = 0.75             # Tabla 44: se puede reducir al 75% si se cubren
ANCHO_LECHO_DEFECTO_M = 6.0


def trh_uasb_recomendado(temperatura):
    """Rango de TRH (h) de la Tabla 31 (Art. 191) para la temperatura dada.

    Retorna (TRH mín., TRH máx. o None). Por debajo de 16 °C la tabla no
    aplica y se retorna el rango más exigente (16-19 °C).
    """
    for t_min, t_max, trh_min, trh_max in TRH_UASB_POR_TEMPERATURA:
        if t_min <= temperatura <= t_max:
            return trh_min, trh_max
    return TRH_UASB_POR_TEMPERATURA[0][2], TRH_UASB_POR_TEMPERATURA[0][3]
