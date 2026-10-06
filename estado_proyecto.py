"""
Estado compartido del proyecto.

Guarda los Datos Preliminares (población de diseño, periodo de
diseño, etc.) una sola vez, para que las ventanas de cálculo de PTAP
y PTAR puedan consultarlos sin tener que volver a pedirlos.
"""


class EstadoProyecto:
    """Contenedor único (singleton simple) con los datos del proyecto."""

    departamento = None
    municipio = None
    area_geografica = None
    año_inicio = None
    periodo_diseño = None
    año_horizonte = None
    metodo_diseño = None          # "Aritmético" | "Geométrico" | "Exponencial"
    poblacion_inicial = None      # población en año_inicio
    poblacion_diseño = None       # población proyectada al año_horizonte
    tabla_proyeccion = None       # DataFrame completo (AÑO, Aritmético, Geométrico, Exponencial)

    # --- Caudal de diseño — PTAP (Paso 2) ---
    nivel_complejidad = None      # "Bajo" | "Medio" | "Medio Alto" | "Alto"
    dotacion_neta_max = None      # L/hab*día (según nivel de complejidad)
    coef_afectacion = None        # coeficiente por temperatura/clima
    dotacion_neta = None          # L/hab*día
    porc_perdidas = None          # decimal, ej. 0.25
    dotacion_bruta = None         # L/hab*día
    qmd = None                    # caudal medio diario, L/s
    k1 = None
    k2 = None
    q_max_diario = None           # QMD, L/s
    q_max_horario = None          # QMH, L/s
    almacenamiento_en_casa = None  # "SI" | "NO"
    caudal_diseño_Ls = None       # L/s
    caudal_diseño_m3s = None      # m3/s

    # --- Caudal de diseño — PTAR ---
    # Mismos campos que el bloque de PTAP de arriba, pero independientes:
    # el caudal de diseño de una PTAR NO se calcula igual que el de una
    # PTAP (aquí todavía no se han definido las fórmulas propias de PTAR;
    # por ahora el módulo de cálculo es el mismo formulario, solo que
    # guarda sus resultados en este bloque separado).
    ptar_nivel_complejidad = None
    ptar_dotacion_neta_max = None
    ptar_coef_afectacion = None
    ptar_dotacion_neta = None
    ptar_porc_perdidas = None
    ptar_dotacion_bruta = None
    ptar_qmd = None
    ptar_k1 = None
    ptar_k2 = None
    ptar_q_max_diario = None
    ptar_q_max_horario = None
    ptar_almacenamiento_en_casa = None
    ptar_caudal_diseño_Ls = None
    ptar_caudal_diseño_m3s = None

    # --- Captación: Bocatoma con Rejilla (Paso 3 - PTAP) ---
    vf = None                     # velocidad efectiva del flujo, m/s
    tipo_inclinacion = None       # "Verticales" | "Inclinadas"
    angulo_inclinacion = None     # grados
    tipo_grava = None             # "Finas" | "Medias" | "Gruesas"
    valor_z = None                # separación entre barrotes, m
    forma_barrote = None          # "C1".."C7"
    coef_forma_barrote = None     # coeficiente de pérdidas (Kirschmer)
    diametro_barrote_in = None    # pulgadas
    s_barrote = None              # espesor del barrote, m
    borde_libre = None            # m
    hrh = None                    # altura de la rejilla en área húmeda, m
    longitud_barrotes = None      # m (valor de referencia/catálogo)
    longitud_sumergida = None     # Lrh, m
    longitud_total_barrote = None  # Lrt, m
    area_captacion = None         # Ac, m2
    area_captacion_efectiva = None  # m2
    num_espacios = None           # n+1
    num_barrotes = None           # n
    area_rejilla = None           # Ar, m2
    ancho_rejilla = None          # Br, m
    perdidas_rejilla = None       # Δh, m

    # --- Desarenador (Paso 4 - PTAP) ---
    desarenador_num_unidades = None      # unidades en paralelo
    desarenador_q_unidad = None          # m³/s, caudal por unidad
    desarenador_temperatura = None       # °C
    desarenador_viscosidad = None        # Pa·s
    desarenador_densidad_agua = None     # kg/m³
    desarenador_d_particula_mm = None    # mm
    desarenador_peso_especifico = None   # g/cm³
    desarenador_vs = None                # m/s (Ley de Stokes)
    desarenador_reynolds = None          # adimensional
    desarenador_vh = None                # m/s
    desarenador_relacion_vh_vs = None    # adimensional (Art. 55, máx. 20)
    desarenador_ancho = None             # m
    desarenador_area_superficial = None  # m²
    desarenador_longitud = None          # m
    desarenador_profundidad = None       # m
    desarenador_t_retencion_min = None   # minutos (Art. 55, mín. 20)
    desarenador_pendiente = None         # % (Art. 55, mín. 10%)
    desarenador_relacion_bh = None       # relación constructiva B/H
    desarenador_vs_requerida = None      # m/s, H/t (verificación de asentamiento)
    desarenador_cumple_asentamiento = None  # bool
    desarenador_num_tramos = None        # tramos del serpentín
    desarenador_longitud_total = None    # m, longitud desarrollada total (todos los tramos)
    desarenador_ancho_total_estructura = None  # m, ancho de toda la estructura plegada

    # --- Relleno sanitario (DORS): cálculo poblacional ---
    # Independiente de los Datos Preliminares de PTAP/PTAR (ver
    # relleno_sanitario.py para las fórmulas).
    rs_departamento = None
    rs_municipio = None
    rs_area = None
    rs_parametros = None          # dict: metodo (1|2|3) + tu,t1,pu,p1 ó t0,p0,r
    rs_año_inicio = None          # primer año de la proyección
    rs_datos_censales = None      # [(año, población), ...] (solo método 2)
    rs_tabla_proyeccion = None    # DataFrame (AÑO, Aritmético, Geométrico, Exponencial), 50 años
    rs_metodo_adoptado = None     # "Aritmético" | "Geométrico" | "Exponencial"
    rs_año_horizonte = None       # último año de la proyección
    rs_poblacion_diseño = None    # hab, en rs_año_horizonte con el método adoptado

    @classmethod
    def esta_definido(cls):
        return cls.poblacion_diseño is not None

    @classmethod
    def caudal_definido(cls):
        return cls.caudal_diseño_Ls is not None

    @classmethod
    def caudal_definido_ptar(cls):
        return cls.ptar_caudal_diseño_Ls is not None

    @classmethod
    def rejilla_definida(cls):
        return cls.area_rejilla is not None

    @classmethod
    def desarenador_definido(cls):
        return cls.desarenador_longitud is not None

    @classmethod
    def relleno_definido(cls):
        return cls.rs_tabla_proyeccion is not None

    @classmethod
    def resumen(cls):
        if not cls.esta_definido():
            return "Datos preliminares aún no definidos."
        return (
            f"{cls.municipio} ({cls.departamento}) — Área: {cls.area_geografica}\n"
            f"Periodo de diseño: {cls.año_inicio} a {cls.año_horizonte} "
            f"({cls.periodo_diseño} años)\n"
            f"Método de diseño: {cls.metodo_diseño}\n"
            f"Población de diseño: {cls.poblacion_diseño:,.0f} hab."
        )

    @classmethod
    def resumen_caudal(cls):
        if not cls.caudal_definido():
            return "Caudal de diseño aún no calculado."
        return (
            f"Nivel de complejidad: {cls.nivel_complejidad}\n"
            f"Qmd: {cls.qmd:,.2f} L/s   QMD: {cls.q_max_diario:,.2f} L/s   "
            f"QMH: {cls.q_max_horario:,.2f} L/s\n"
            f"Caudal de diseño: {cls.caudal_diseño_Ls:,.2f} L/s "
            f"({cls.caudal_diseño_m3s:,.5f} m³/s)"
        )

    @classmethod
    def resumen_caudal_ptar(cls):
        if not cls.caudal_definido_ptar():
            return "Caudal de diseño (PTAR) aún no calculado."
        return (
            f"Nivel de complejidad: {cls.ptar_nivel_complejidad}\n"
            f"Qmd: {cls.ptar_qmd:,.2f} L/s   QMD: {cls.ptar_q_max_diario:,.2f} L/s   "
            f"QMH: {cls.ptar_q_max_horario:,.2f} L/s\n"
            f"Caudal de diseño: {cls.ptar_caudal_diseño_Ls:,.2f} L/s "
            f"({cls.ptar_caudal_diseño_m3s:,.5f} m³/s)"
        )

    @classmethod
    def resumen_rejilla(cls):
        if not cls.rejilla_definida():
            return "Bocatoma con rejilla aún no calculada."
        return (
            f"Área de captación: {cls.area_captacion:,.3f} m²\n"
            f"N° de barrotes: {cls.num_barrotes:,.0f}   "
            f"N° de espacios: {cls.num_espacios:,.0f}\n"
            f"Área de la rejilla: {cls.area_rejilla:,.3f} m²   "
            f"Ancho: {cls.ancho_rejilla:,.3f} m\n"
            f"Pérdidas en la rejilla (Δh): {cls.perdidas_rejilla:,.4f} m"
        )

    @classmethod
    def resumen_desarenador(cls):
        if not cls.desarenador_definido():
            return "Desarenador aún no calculado."
        texto_tramos = (
            f" (en {cls.desarenador_num_tramos} tramos en serpentín, "
            f"L total: {cls.desarenador_longitud_total:,.1f} m)"
            if cls.desarenador_num_tramos and cls.desarenador_num_tramos > 1
            else ""
        )
        return (
            f"{cls.desarenador_num_unidades} unidad(es) — "
            f"Q por unidad: {cls.desarenador_q_unidad:,.5f} m³/s\n"
            f"Dimensiones por tramo (L×B×H): {cls.desarenador_longitud:,.2f} × "
            f"{cls.desarenador_ancho:,.2f} × {cls.desarenador_profundidad:,.2f} m{texto_tramos}\n"
            f"Vs: {cls.desarenador_vs:,.5f} m/s   Vh: {cls.desarenador_vh:,.3f} m/s   "
            f"Tiempo de retención: {cls.desarenador_t_retencion_min:,.1f} min"
        )

    @classmethod
    def resumen_relleno(cls):
        if not cls.relleno_definido():
            return "Cálculo poblacional del relleno sanitario aún no realizado."
        ubicacion = (
            f"{cls.rs_municipio} ({cls.rs_departamento}) — Área: {cls.rs_area}\n"
            if cls.rs_municipio else ""
        )
        return (
            f"{ubicacion}"
            f"Proyección: {cls.rs_año_inicio} a {cls.rs_año_horizonte}\n"
            f"Método adoptado: {cls.rs_metodo_adoptado}\n"
            f"Población en {cls.rs_año_horizonte}: {cls.rs_poblacion_diseño:,.0f} hab."
        )
