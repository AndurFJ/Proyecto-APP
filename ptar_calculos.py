"""
Cálculos del módulo PTAR (sin interfaz gráfica).

Cada estructura tiene una función `calcular_<estructura>(datos)` que
recibe un diccionario con los datos de entrada (números o textos) y
retorna un diccionario con:

    "valores":        resultados numéricos (para otros procesos y el PDF)
    "filas":          lista de (etiqueta, texto formateado) para mostrar
    "verificaciones": lista de (texto, cumple: bool) frente al RAS
    "final":          texto del resultado principal (marco verde)

Al no depender de Tkinter, estas funciones se pueden probar o reutilizar
desde cualquier otra ventana o desde el generador del PDF.

Tren de tratamiento adoptado (Res. 0330 de 2017, mod. Res. 799 de 2021):

    Caudal de aguas residuales (Art. 134, 166)
    → Rejillas (Art. 186)
    → Desarenador de velocidad constante (Art. 188)
    → Trampa de grasas (Art. 185, criterios del Art. 172)
    → Reactor UASB (Art. 191)
    → Laguna facultativa de pulimento (Art. 199, 201)
    → Lechos de secado de lodos (Art. 211, Tabla 44)
"""

import math

import ptar_criterios as C

G = 9.81  # m/s²


def _resultado(valores, filas, verificaciones, final):
    return {
        "valores": valores,
        "filas": filas,
        "verificaciones": verificaciones,
        "final": final,
        "cumple_todo": all(c for _, c in verificaciones),
    }


def _positivo(datos, *claves):
    for clave in claves:
        if datos[clave] is None or datos[clave] <= 0:
            raise ValueError(f"El dato '{clave}' debe ser mayor que cero.")


def _en_rango(valor, rango):
    minimo, maximo = rango
    if minimo is not None and valor < minimo:
        return False
    if maximo is not None and valor > maximo:
        return False
    return True


def _texto_rango(rango, unidad=""):
    minimo, maximo = rango
    if maximo is None:
        return f"> {minimo:g} {unidad}".strip()
    return f"{minimo:g} – {maximo:g} {unidad}".strip()


# ======================================================================
# 1. CAUDAL DE AGUAS RESIDUALES — Art. 134 y Art. 166
# ======================================================================
def calcular_caudal_ar(datos):
    """
    Qd   = CR · P · DN / 86400                         (Art. 134, por población)
    QI, QC, QIns = área · aporte unitario
    QmAR = Qd + QI + QC + QIns                          (caudal medio, tiempo seco)
    F    = 3,5 / P^0,1  (Flores, P en miles), 1,4 ≤ F ≤ 3,8 (Art. 134)
    QMH  = F · QmAR
    Qinf = área urbana · aporte de infiltración         (Art. 134)
    QCE  = área urbana · aporte por conexiones erradas  (Art. 134)
    QMAX = QMH + Qinf + QCE
    Caudal de diseño de la PTAR (Art. 166):
        si QMAX ≤ 30 L/s → 3 · QmAR (sin infiltración ni conexiones erradas)
        si no            → QMAX
    """
    _positivo(datos, "poblacion", "dotacion_neta", "coef_retorno", "area_total")
    p = datos["poblacion"]
    area = datos["area_total"]

    qd = datos["coef_retorno"] * p * datos["dotacion_neta"] / 86400
    area_ind = area * datos["porc_industrial"]
    area_com = area * datos["porc_comercial"]
    area_ins = area * datos["porc_institucional"]
    area_urb = area * datos["porc_urbana"]
    qi = area_ind * datos["aporte_industrial"]
    qc = area_com * datos["aporte_comercial"]
    qins = area_ins * datos["aporte_institucional"]
    q_medio = qd + qi + qc + qins

    f_flores = 3.5 / ((p / 1000) ** 0.1)
    f = min(C.FACTOR_MAYORACION_MAX, max(C.FACTOR_MAYORACION_MIN, f_flores))
    qmh = f * q_medio
    qinf = area_urb * datos["aporte_infiltracion"]
    qce = area_urb * datos["aporte_conexiones_erradas"]
    q_max = qmh + qinf + qce

    planta_pequeña = q_max <= C.LIMITE_PLANTA_PEQUEÑA_LS
    if planta_pequeña:
        q_diseño = C.FACTOR_PLANTA_PEQUEÑA * q_medio
        criterio = f"Art. 166: Q ≤ {C.LIMITE_PLANTA_PEQUEÑA_LS:g} L/s → 3 × QmAR"
    else:
        q_diseño = q_max
        criterio = f"Art. 166: Q > {C.LIMITE_PLANTA_PEQUEÑA_LS:g} L/s → QMH + Qinf + QCE"
    q_min = C.FACTOR_CAUDAL_MINIMO * q_medio

    valores = dict(
        poblacion=p, dotacion_neta=datos["dotacion_neta"],
        coef_retorno=datos["coef_retorno"], area_total=area, area_urbana=area_urb,
        q_domestico=qd, q_industrial=qi, q_comercial=qc, q_institucional=qins,
        q_medio=q_medio, f_flores=f_flores, f=f, q_max_horario=qmh,
        q_infiltracion=qinf, q_conexiones_erradas=qce, q_max=q_max,
        q_diseño=q_diseño, q_min=q_min, planta_pequeña=planta_pequeña,
        criterio_diseño=criterio,
    )
    filas = [
        ("Población de diseño (hab)", f"{p:,.0f}"),
        ("Dotación neta — DN (L/hab·día)", f"{datos['dotacion_neta']:,.1f}"),
        ("Coeficiente de retorno — CR", f"{datos['coef_retorno']:,.2f}"),
        ("Caudal doméstico — Qd = CR·P·DN/86400 (L/s)", f"{qd:,.2f}"),
        ("Área industrial (ha) / Caudal industrial QI (L/s)", f"{area_ind:,.2f} ha  →  {qi:,.2f} L/s"),
        ("Área comercial (ha) / Caudal comercial QC (L/s)", f"{area_com:,.2f} ha  →  {qc:,.2f} L/s"),
        ("Área institucional (ha) / Caudal institucional QIns (L/s)", f"{area_ins:,.2f} ha  →  {qins:,.2f} L/s"),
        ("Caudal medio de tiempo seco — QmAR (L/s)", f"{q_medio:,.2f}"),
        ("Factor de Flores — F = 3,5 / P^0,1 (P en miles)", f"{f_flores:,.3f}"),
        ("Factor de mayoración aplicado (1,4 ≤ F ≤ 3,8)", f"{f:,.3f}"),
        ("Caudal máximo horario — QMH = F·QmAR (L/s)", f"{qmh:,.2f}"),
        ("Área urbana (ha)", f"{area_urb:,.2f}"),
        ("Caudal de infiltración — Qinf (L/s)", f"{qinf:,.2f}"),
        ("Caudal por conexiones erradas — QCE (L/s)", f"{qce:,.2f}"),
        ("Caudal máximo — QMAX = QMH + Qinf + QCE (L/s)", f"{q_max:,.2f}"),
        ("Caudal mínimo de referencia — 0,5·QmAR (L/s)", f"{q_min:,.2f}"),
        ("Criterio para el caudal de diseño", criterio),
    ]
    verificaciones = [
        (f"CR = {datos['coef_retorno']:.2f} (Art. 134: 0,85 sin datos de campo)",
         0 < datos["coef_retorno"] <= 1),
        (f"Factor de mayoración F = {f:.2f} — exigido: 1,4 – 3,8 (Art. 134)",
         C.FACTOR_MAYORACION_MIN <= f <= C.FACTOR_MAYORACION_MAX),
        (f"Conexiones erradas {datos['aporte_conexiones_erradas']:.2f} L/s·ha "
         f"≤ {C.CONEXIONES_ERRADAS_MAX_LS_HA} L/s·ha (Art. 134)",
         datos["aporte_conexiones_erradas"] <= C.CONEXIONES_ERRADAS_MAX_LS_HA + 1e-9),
    ]
    final = (
        f"Caudal de diseño PTAR: {q_diseño:,.2f} L/s   ({q_diseño / 1000:,.5f} m³/s)\n"
        f"Caudal medio QmAR: {q_medio:,.2f} L/s"
    )
    return _resultado(valores, filas, verificaciones, final)


# ======================================================================
# 2. REJILLAS — Art. 186
# ======================================================================
def _tirante_manning(q, b, s, n):
    """Tirante normal (m) en canal rectangular por Manning (bisección)."""
    def q_de(y):
        a = b * y
        r = a / (b + 2 * y)
        return a * r ** (2 / 3) * math.sqrt(s) / n

    bajo, alto = 1e-6, 20.0
    for _ in range(200):
        medio = (bajo + alto) / 2
        if q_de(medio) < q:
            bajo = medio
        else:
            alto = medio
    return (bajo + alto) / 2


def clasificar_rejilla(separacion_cm):
    if separacion_cm >= C.SEPARACION_REJA_GRUESA_CM[0]:
        return "Gruesa"
    if separacion_cm >= C.SEPARACION_REJA_MEDIA_CM[0]:
        return "Media"
    if separacion_cm >= C.SEPARACION_REJA_FINA_CM[0]:
        return "Fina"
    return "Fuera de rango"


def calcular_rejillas(datos):
    """
    Canal rectangular de aproximación (Manning) con rejilla de barras.

    y   = tirante normal para Qmax y Qmin (Manning)
    Va  = Q / (B·y)                              velocidad de aproximación
    Vb  = Va · (b + t) / b                       velocidad entre barras
    Art. 186: Vb ≤ 1,2 m/s con Qmax ; Va ≥ 0,3 m/s con Qmin
    n   = B / (b + t) − 1                        número de barras
    hf  = β·(t/b)^(4/3)·(Va²/2g)·sen θ           pérdida (Kirschmer)
    """
    _positivo(datos, "q_max_ls", "q_min_ls", "ancho_canal", "pendiente", "manning",
              "separacion_cm", "espesor_cm", "angulo", "beta")
    q_max = datos["q_max_ls"] / 1000
    q_min = datos["q_min_ls"] / 1000
    b_canal = datos["ancho_canal"]
    sep = datos["separacion_cm"] / 100
    esp = datos["espesor_cm"] / 100
    theta = math.radians(datos["angulo"])

    y_max = _tirante_manning(q_max, b_canal, datos["pendiente"], datos["manning"])
    y_min = _tirante_manning(q_min, b_canal, datos["pendiente"], datos["manning"])
    va_max = q_max / (b_canal * y_max)
    va_min = q_min / (b_canal * y_min)
    factor_obstruccion = (sep + esp) / sep
    vb_max = va_max * factor_obstruccion
    vb_min = va_min * factor_obstruccion

    num_barras = max(1, math.ceil(b_canal / (sep + esp) - 1))
    num_espacios = num_barras + 1
    hf = datos["beta"] * (esp / sep) ** (4 / 3) * va_max ** 2 / (2 * G) * math.sin(theta)
    hf_50 = datos["beta"] * (esp / sep) ** (4 / 3) * (2 * va_max) ** 2 / (2 * G) * math.sin(theta)
    altura_canal = y_max + datos["borde_libre"]
    longitud_barras = altura_canal / math.sin(theta)
    proyeccion_horizontal = altura_canal / math.tan(theta)
    tipo = clasificar_rejilla(datos["separacion_cm"])
    limpieza = ("Mecánica" if datos.get("q_medio_ls", 0) >= C.CAUDAL_LIMPIEZA_MECANICA_LS
                else "Manual")

    valores = dict(
        q_max_ls=datos["q_max_ls"], q_min_ls=datos["q_min_ls"], ancho_canal=b_canal,
        pendiente=datos["pendiente"], manning=datos["manning"],
        separacion_cm=datos["separacion_cm"], espesor_cm=datos["espesor_cm"],
        angulo=datos["angulo"], beta=datos["beta"], borde_libre=datos["borde_libre"],
        tirante_max=y_max, tirante_min=y_min, va_max=va_max, va_min=va_min,
        vb_max=vb_max, vb_min=vb_min, num_barras=num_barras, num_espacios=num_espacios,
        perdida_limpia=hf, perdida_50=hf_50, altura_canal=altura_canal,
        longitud_barras=longitud_barras, proyeccion_horizontal=proyeccion_horizontal,
        tipo_reja=tipo, limpieza=limpieza,
    )
    filas = [
        ("Caudal máximo / mínimo (L/s)", f"{datos['q_max_ls']:,.2f} / {datos['q_min_ls']:,.2f}"),
        ("Tipo de reja según separación (Art. 186)", f"{tipo} ({datos['separacion_cm']:g} cm)"),
        ("Tipo de limpieza (Art. 186: mecánica si Qmed ≥ 100 L/s)", limpieza),
        ("Tirante con Qmax / Qmin — Manning (m)", f"{y_max:,.3f} / {y_min:,.3f}"),
        ("Velocidad de aproximación con Qmax / Qmin (m/s)", f"{va_max:,.3f} / {va_min:,.3f}"),
        ("Velocidad entre barras con Qmax / Qmin (m/s)", f"{vb_max:,.3f} / {vb_min:,.3f}"),
        ("Número de barras / espacios", f"{num_barras} / {num_espacios}"),
        ("Altura del canal (tirante máx. + borde libre) (m)", f"{altura_canal:,.3f}"),
        ("Longitud de las barras inclinadas (m)", f"{longitud_barras:,.3f}"),
        ("Proyección horizontal de la rejilla (m)", f"{proyeccion_horizontal:,.3f}"),
        ("Pérdida de carga, rejilla limpia — Kirschmer (m)", f"{hf:,.4f}"),
        ("Pérdida de carga, 50% obstruida (m)", f"{hf_50:,.4f}"),
    ]
    verificaciones = [
        (f"Velocidad entre barras con Qmax = {vb_max:.2f} m/s — máximo: "
         f"{C.VEL_MAX_REJILLA_QMAX} m/s (Art. 186)", vb_max <= C.VEL_MAX_REJILLA_QMAX),
        (f"Velocidad de aproximación con Qmin = {va_min:.2f} m/s — mínimo: "
         f"{C.VEL_MIN_REJILLA_QMIN} m/s (Art. 186)", va_min >= C.VEL_MIN_REJILLA_QMIN),
        (f"Separación entre barras {datos['separacion_cm']:g} cm — exigido: 1 – 10 cm (Art. 186)",
         C.SEPARACION_REJA_FINA_CM[0] <= datos["separacion_cm"] <= C.SEPARACION_REJA_GRUESA_CM[1]),
    ]
    final = (
        f"Canal B = {b_canal:,.2f} m  ×  H = {altura_canal:,.2f} m — "
        f"{num_barras} barras a {datos['angulo']:g}°\n"
        f"Pérdida de carga (limpia / 50% obstruida): {hf:,.3f} / {hf_50:,.3f} m"
    )
    return _resultado(valores, filas, verificaciones, final)


# ======================================================================
# 3. DESARENADOR — Art. 188
# ======================================================================
def calcular_desarenador(datos):
    """
    Desarenador de flujo horizontal y velocidad constante (Art. 188).

    Qu  = Qmax / N
    At  = Qu / Vh                     área transversal
    H   = √(At / (B/H)) ; B = (B/H)·H
    ts  = H / Vs                      tiempo para que la partícula llegue al fondo
    L   = FS · Vh · ts                longitud (con factor de seguridad)
    Cs  = Qu / (B·L)                  carga superficial
    Arena: Vol = Q·(L/m³)·días de limpieza → profundidad de la tolva
    """
    _positivo(datos, "q_max_ls", "num_unidades", "vh", "vs", "relacion_bh",
              "factor_seguridad")
    n = int(round(datos["num_unidades"]))
    q_u = datos["q_max_ls"] / 1000 / n
    area_t = q_u / datos["vh"]
    h = math.sqrt(area_t / datos["relacion_bh"])
    b = datos["relacion_bh"] * h
    t_sed = h / datos["vs"]
    largo = datos["factor_seguridad"] * datos["vh"] * t_sed
    t_ret = largo / datos["vh"]
    carga_sup = q_u * 86400 / (b * largo)
    q_medio_m3d = datos.get("q_medio_ls", datos["q_max_ls"]) / 1000 * 86400
    arena_m3_dia = q_medio_m3d * datos["arena_l_m3"] / 1000
    vol_arena_unidad = arena_m3_dia * datos["dias_limpieza"] / n
    prof_tolva = vol_arena_unidad / (b * largo)

    valores = dict(
        q_max_ls=datos["q_max_ls"], num_unidades=n, q_unidad=q_u, vh=datos["vh"],
        vs=datos["vs"], relacion_bh=datos["relacion_bh"],
        factor_seguridad=datos["factor_seguridad"], area_transversal=area_t,
        profundidad=h, ancho=b, t_sedimentacion=t_sed, longitud=largo,
        t_retencion=t_ret, carga_superficial=carga_sup, arena_m3_dia=arena_m3_dia,
        dias_limpieza=datos["dias_limpieza"], vol_arena_unidad=vol_arena_unidad,
        profundidad_tolva=prof_tolva,
    )
    filas = [
        ("Número de unidades / caudal por unidad (m³/s)", f"{n} / {q_u:,.5f}"),
        ("Velocidad horizontal — Vh (m/s)", f"{datos['vh']:,.3f}"),
        ("Velocidad de sedimentación — Vs (m/s)", f"{datos['vs']:,.3f}"),
        ("Área transversal — At = Qu/Vh (m²)", f"{area_t:,.4f}"),
        ("Profundidad útil — H (m)", f"{h:,.3f}"),
        ("Ancho — B (m)", f"{b:,.3f}"),
        ("Tiempo de sedimentación — ts = H/Vs (s)", f"{t_sed:,.1f}"),
        ("Longitud — L = FS·Vh·ts (m)", f"{largo:,.2f}"),
        ("Tiempo de retención — L/Vh (s)", f"{t_ret:,.1f}"),
        ("Carga superficial (m³/m²·día)", f"{carga_sup:,.0f}"),
        ("Arena retenida — toda la planta (m³/día)", f"{arena_m3_dia:,.3f}"),
        ("Volumen de arena por unidad entre limpiezas (m³)", f"{vol_arena_unidad:,.3f}"),
        ("Profundidad adicional de la tolva de arenas (m)", f"{prof_tolva:,.3f}"),
    ]
    verificaciones = [
        (f"Número de unidades = {n} — mínimo: {C.UNIDADES_MIN_DESARENADOR} (Art. 188)",
         n >= C.UNIDADES_MIN_DESARENADOR),
        (f"Vh = {datos['vh']:.2f} m/s — exigido: {C.VH_DESARENADOR_MS} m/s (Art. 188, "
         f"tolerancia ±{C.TOLERANCIA_VH_DESARENADOR})",
         abs(datos["vh"] - C.VH_DESARENADOR_MS) <= C.TOLERANCIA_VH_DESARENADOR + 1e-9),
        (f"Vs = {datos['vs']:.3f} m/s — máximo: {C.VS_DESARENADOR_MS} m/s, partícula ≥ "
         f"{C.DIAMETRO_PARTICULA_DESARENADOR_MM} mm (Art. 188)",
         datos["vs"] <= C.VS_DESARENADOR_MS + 1e-9),
    ]
    final = (
        f"{n} unidades de  L = {largo:,.2f} m  ×  B = {b:,.2f} m  ×  H = {h:,.2f} m\n"
        f"(+ tolva de arenas de {prof_tolva:,.2f} m)"
    )
    return _resultado(valores, filas, verificaciones, final)


# ======================================================================
# 4. TRAMPA DE GRASAS — Art. 185 (criterios dimensionales del Art. 172)
# ======================================================================
def calcular_trampa_grasas(datos):
    """
    V = Qu · TR ; A = V / H ; B = √(A / (L/B)) ; L = (L/B) · B
    """
    _positivo(datos, "q_max_ls", "num_unidades", "tr_min", "profundidad", "relacion_lb")
    n = int(round(datos["num_unidades"]))
    q_u = datos["q_max_ls"] / 1000 / n
    vol = q_u * datos["tr_min"] * 60
    area = vol / datos["profundidad"]
    ancho = math.sqrt(area / datos["relacion_lb"])
    largo = datos["relacion_lb"] * ancho
    carga_sup = q_u * 86400 / area
    altura_total = datos["profundidad"] + datos["borde_libre"]
    aireado = datos.get("q_medio_ls", 0) >= C.CAUDAL_DESENGRASADOR_AIREADO_LS

    valores = dict(
        q_max_ls=datos["q_max_ls"], num_unidades=n, q_unidad=q_u, tr_min=datos["tr_min"],
        profundidad=datos["profundidad"], relacion_lb=datos["relacion_lb"],
        borde_libre=datos["borde_libre"], volumen=vol, area=area, ancho=ancho,
        longitud=largo, carga_superficial=carga_sup, altura_total=altura_total,
        sugiere_aireado=aireado,
    )
    filas = [
        ("Número de unidades / caudal por unidad (m³/s)", f"{n} / {q_u:,.5f}"),
        ("Volumen útil por unidad — V = Qu·TR (m³)", f"{vol:,.2f}"),
        ("Área superficial — A = V/H (m²)", f"{area:,.2f}"),
        ("Ancho — B (m)", f"{ancho:,.2f}"),
        ("Longitud — L (m)", f"{largo:,.2f}"),
        ("Altura total con borde libre (m)", f"{altura_total:,.2f}"),
        ("Carga superficial (m³/m²·día)", f"{carga_sup:,.0f}"),
        ("Desengrasador aireado (Art. 185, Qmed ≥ 100 L/s)",
         "Se puede considerar" if aireado else "No requerido"),
    ]
    verificaciones = [
        (f"Tiempo de retención = {datos['tr_min']:.1f} min — mínimo: {C.TR_MIN_TRAMPA_GRASAS_MIN} min (Art. 172)",
         datos["tr_min"] >= C.TR_MIN_TRAMPA_GRASAS_MIN),
        (f"Relación L/B = {datos['relacion_lb']:.1f} — exigido: 1 – 3 (Art. 172)",
         _en_rango(datos["relacion_lb"], C.RELACION_LB_TRAMPA)),
        (f"Profundidad útil = {datos['profundidad']:.2f} m — mínimo: {C.PROFUNDIDAD_MIN_TRAMPA_M} m (Art. 172)",
         datos["profundidad"] >= C.PROFUNDIDAD_MIN_TRAMPA_M),
    ]
    final = (
        f"{n} unidades de  L = {largo:,.2f} m  ×  B = {ancho:,.2f} m  ×  "
        f"H = {altura_total:,.2f} m (con borde libre)"
    )
    return _resultado(valores, filas, verificaciones, final)


# ======================================================================
# 5. REACTOR UASB — Art. 191 (Tablas 31, 32, 33)
# ======================================================================
def calcular_uasb(datos):
    """
    V    = Qmed · TRH ; A = V / H
    Vasc = Q / A  (con Qmed y con el caudal de diseño / pico)
    COV  = Qmed · DQO / V          (kg DQO/m³·día)
    DBO efluente = DBO · (1 − E)
    Lodo = Y · carga de DQO        (kg SST/día)
    N° de distribuidores = A / área de influencia
    """
    _positivo(datos, "q_medio_ls", "q_pico_ls", "trh", "profundidad", "num_modulos",
              "dbo", "dqo", "area_distribuidor")
    n = int(round(datos["num_modulos"]))
    q_med_m3h = datos["q_medio_ls"] * 3.6
    q_pico_m3h = datos["q_pico_ls"] * 3.6
    vol = q_med_m3h * datos["trh"]
    area = vol / datos["profundidad"]
    area_mod = area / n
    lado = math.sqrt(area_mod)
    vasc_med = q_med_m3h / area
    vasc_pico = q_pico_m3h / area
    q_med_m3d = q_med_m3h * 24
    carga_dqo = q_med_m3d * datos["dqo"] / 1000            # kg/d
    carga_dbo = q_med_m3d * datos["dbo"] / 1000
    cov = carga_dqo / vol
    dbo_ef = datos["dbo"] * (1 - datos["eficiencia_dbo"])
    lodo = datos["coef_lodo"] * carga_dqo
    n_dist = math.ceil(area_mod / datos["area_distribuidor"])
    trh_min, trh_max = C.trh_uasb_recomendado(datos["temperatura"])

    valores = dict(
        q_medio_ls=datos["q_medio_ls"], q_pico_ls=datos["q_pico_ls"],
        temperatura=datos["temperatura"], trh=datos["trh"], profundidad=datos["profundidad"],
        num_modulos=n, dbo=datos["dbo"], dqo=datos["dqo"],
        eficiencia_dbo=datos["eficiencia_dbo"], volumen=vol, area=area,
        area_modulo=area_mod, lado_modulo=lado, vasc_media=vasc_med, vasc_pico=vasc_pico,
        carga_dqo=carga_dqo, carga_dbo=carga_dbo, cov=cov, dbo_efluente=dbo_ef,
        lodo_kg_dia=lodo, distribuidores_modulo=n_dist,
        area_distribuidor=datos["area_distribuidor"],
    )
    filas = [
        ("Caudal medio / de diseño (m³/h)", f"{q_med_m3h:,.1f} / {q_pico_m3h:,.1f}"),
        ("TRH recomendado para la temperatura (Tabla 31)",
         _texto_rango((trh_min, trh_max), "h")),
        ("Volumen total — V = Qmed·TRH (m³)", f"{vol:,.1f}"),
        ("Área total — A = V/H (m²)", f"{area:,.1f}"),
        ("Área por módulo (m²) / lado de módulo cuadrado (m)", f"{area_mod:,.1f} / {lado:,.2f}"),
        ("Velocidad ascensional con Qmed (m/h)", f"{vasc_med:,.3f}"),
        ("Velocidad ascensional con Q de diseño (m/h)", f"{vasc_pico:,.3f}"),
        ("Carga de DQO / DBO aplicada (kg/día)", f"{carga_dqo:,.0f} / {carga_dbo:,.0f}"),
        ("Carga orgánica volumétrica (kg DQO/m³·día)", f"{cov:,.2f}"),
        ("DBO₅ del efluente estimada (mg/L)", f"{dbo_ef:,.0f}"),
        ("Producción de lodo (kg SST/día)", f"{lodo:,.0f}"),
        ("Distribuidores de entrada por módulo (Tabla 33)", f"{n_dist}"),
        ("Altura del separador GSL (Art. 191)", f"{C.ALTURA_SGSL_M:g} m, placas a 45°"),
    ]
    verificaciones = [
        (f"TRH = {datos['trh']:.1f} h — exigido: {_texto_rango((trh_min, trh_max), 'h')} "
         f"para {datos['temperatura']:.0f} °C (Art. 191, Tabla 31)",
         _en_rango(datos["trh"], (trh_min, trh_max))),
        (f"Velocidad ascensional media = {vasc_med:.2f} m/h — exigido: "
         f"{_texto_rango(C.VASC_UASB_MEDIA, 'm/h')} (Tabla 32)",
         _en_rango(vasc_med, C.VASC_UASB_MEDIA)),
        (f"Velocidad ascensional pico = {vasc_pico:.2f} m/h — exigido: < {C.VASC_UASB_PICO_MAX} m/h (Tabla 32)",
         vasc_pico < C.VASC_UASB_PICO_MAX),
        (f"Profundidad = {datos['profundidad']:.2f} m — exigido: "
         f"{_texto_rango(C.PROFUNDIDAD_UASB, 'm')} (Art. 191)",
         _en_rango(datos["profundidad"], C.PROFUNDIDAD_UASB)),
        (f"Área por distribuidor = {datos['area_distribuidor']:.1f} m² — exigido: "
         f"{_texto_rango(C.AREA_DISTRIBUIDOR_RANGO_M2, 'm²')} (Tabla 33)",
         _en_rango(datos["area_distribuidor"], C.AREA_DISTRIBUIDOR_RANGO_M2)),
    ]
    final = (
        f"{n} módulos de {lado:,.2f} m × {lado:,.2f} m × H = {datos['profundidad']:,.2f} m  "
        f"(V total = {vol:,.0f} m³)\nDBO₅ efluente ≈ {dbo_ef:,.0f} mg/L"
    )
    return _resultado(valores, filas, verificaciones, final)


# ======================================================================
# 6. LAGUNA FACULTATIVA — Art. 199 y Art. 201
# ======================================================================
def carga_superficial_mara(temperatura):
    """λs = 350·(1,107 − 0,002·T)^(T − 25)  [kg DBO₅/ha·día] (Mara, 1987),
    limitada al rango del Art. 199 (100 – 350)."""
    lam = 350 * (1.107 - 0.002 * temperatura) ** (temperatura - 25)
    return min(C.CARGA_SUPERFICIAL_FACULTATIVA[1], max(C.CARGA_SUPERFICIAL_FACULTATIVA[0], lam))


def calcular_laguna_facultativa(datos):
    """
    Carga = Qmed · DBO                 (kg/día)
    A     = Carga / λs                 (ha)
    V = A·H ; TRH = V / Qmed
    Se    = S0 / (1 + k·TRH), k = 0,3·1,05^(T−20)   (mezcla completa)
    """
    _positivo(datos, "q_medio_ls", "dbo_afluente", "carga_superficial", "profundidad",
              "num_lagunas", "relacion_lb")
    n = int(round(datos["num_lagunas"]))
    q_m3d = datos["q_medio_ls"] * 86.4
    carga = q_m3d * datos["dbo_afluente"] / 1000
    area_ha = carga / datos["carga_superficial"]
    area_m2 = area_ha * 10000
    area_u = area_m2 / n
    ancho = math.sqrt(area_u / datos["relacion_lb"])
    largo = datos["relacion_lb"] * ancho
    vol = area_m2 * datos["profundidad"]
    trh = vol / q_m3d
    k = C.K_LAGUNA_20C * C.THETA_LAGUNA ** (datos["temperatura"] - 20)
    dbo_ef = datos["dbo_afluente"] / (1 + k * trh)
    profundidad_total = datos["profundidad"] + datos["borde_libre"]

    valores = dict(
        q_medio_ls=datos["q_medio_ls"], dbo_afluente=datos["dbo_afluente"],
        temperatura=datos["temperatura"], carga_superficial=datos["carga_superficial"],
        profundidad=datos["profundidad"], num_lagunas=n, relacion_lb=datos["relacion_lb"],
        borde_libre=datos["borde_libre"], carga_dbo=carga, area_ha=area_ha,
        area_unidad=area_u, ancho=ancho, longitud=largo, volumen=vol, trh=trh, k=k,
        dbo_efluente=dbo_ef, profundidad_total=profundidad_total,
    )
    filas = [
        ("Caudal medio (m³/día)", f"{q_m3d:,.0f}"),
        ("Carga de DBO₅ afluente (kg/día)", f"{carga:,.1f}"),
        ("Carga superficial de diseño (kg DBO₅/ha·día)", f"{datos['carga_superficial']:,.0f}"),
        ("Área total requerida (ha)", f"{area_ha:,.3f}"),
        ("Área por laguna (m²)", f"{area_u:,.0f}"),
        ("Ancho / Largo por laguna, a media profundidad (m)", f"{ancho:,.1f} / {largo:,.1f}"),
        ("Volumen total (m³)", f"{vol:,.0f}"),
        ("Tiempo de retención hidráulica (días)", f"{trh:,.1f}"),
        ("Constante de remoción k a T (d⁻¹)", f"{k:,.3f}"),
        ("DBO₅ del efluente estimada (mg/L)", f"{dbo_ef:,.0f}"),
        ("Profundidad total con borde libre (m)", f"{profundidad_total:,.2f}"),
    ]
    verificaciones = [
        (f"Carga superficial = {datos['carga_superficial']:.0f} kg/ha·día — exigido: "
         f"{_texto_rango(C.CARGA_SUPERFICIAL_FACULTATIVA)} (Art. 199)",
         _en_rango(datos["carga_superficial"], C.CARGA_SUPERFICIAL_FACULTATIVA)),
        (f"TRH = {trh:.1f} días — exigido: {_texto_rango(C.TRH_LAGUNA_FACULTATIVA_D, 'días')} (Art. 199)",
         _en_rango(trh, C.TRH_LAGUNA_FACULTATIVA_D)),
        (f"Profundidad = {datos['profundidad']:.2f} m — exigido: "
         f"{_texto_rango(C.PROFUNDIDAD_LAGUNA_FACULTATIVA, 'm')} (Art. 199)",
         _en_rango(datos["profundidad"], C.PROFUNDIDAD_LAGUNA_FACULTATIVA)),
        (f"Borde libre = {datos['borde_libre']:.2f} m — exigido: "
         f"{_texto_rango(C.BORDE_LIBRE_LAGUNA, 'm')} (Art. 201)",
         _en_rango(datos["borde_libre"], C.BORDE_LIBRE_LAGUNA)),
    ]
    final = (
        f"{n} lagunas de {largo:,.1f} m × {ancho:,.1f} m × H = {profundidad_total:,.2f} m  "
        f"(área total {area_ha:,.2f} ha)\nTRH = {trh:,.1f} días — DBO₅ efluente ≈ {dbo_ef:,.0f} mg/L"
    )
    return _resultado(valores, filas, verificaciones, final)


# ======================================================================
# 7. LECHOS DE SECADO — Art. 211, Tabla 44
# ======================================================================
def calcular_lechos_secado(datos):
    """
    Área por población  = P · (m²/hab)                       (Tabla 44)
    Área por carga      = lodo (kg/día) · 365 / carga (kg/m²·año)
    Área adoptada       = la mayor de las dos (× 0,75 si los lechos se cubren)
    """
    _positivo(datos, "poblacion", "area_per_capita", "carga_solidos", "num_lechos",
              "ancho_lecho")
    area_pob = datos["poblacion"] * datos["area_per_capita"]
    lodo = datos.get("lodo_kg_dia", 0) or 0
    area_carga = lodo * 365 / datos["carga_solidos"] if lodo > 0 else 0.0
    area = max(area_pob, area_carga)
    cubierto = datos.get("cubierto") == "Sí"
    if cubierto:
        area *= C.FACTOR_LECHO_CUBIERTO
    n = int(round(datos["num_lechos"]))
    area_u = area / n
    largo = area_u / datos["ancho_lecho"]
    rango = C.LECHOS_SECADO_TABLA_44.get(datos["tipo_lodo"])

    valores = dict(
        poblacion=datos["poblacion"], tipo_lodo=datos["tipo_lodo"],
        area_per_capita=datos["area_per_capita"], carga_solidos=datos["carga_solidos"],
        lodo_kg_dia=lodo, area_por_poblacion=area_pob, area_por_carga=area_carga,
        cubierto=cubierto, area_total=area, num_lechos=n, area_lecho=area_u,
        ancho_lecho=datos["ancho_lecho"], longitud_lecho=largo,
    )
    filas = [
        ("Tipo de biosólido (Tabla 44)", datos["tipo_lodo"]),
        ("Área por población — P·(m²/hab) (m²)", f"{area_pob:,.0f}"),
        ("Lodo a secar (kg SST/día)", f"{lodo:,.0f}" if lodo else "— (sin UASB guardado)"),
        ("Área por carga de sólidos (m²)", f"{area_carga:,.0f}"),
        ("¿Lechos cubiertos? (reducción al 75%)", "Sí" if cubierto else "No"),
        ("Área total adoptada (m²)", f"{area:,.0f}"),
        ("Área por lecho (m²)", f"{area_u:,.1f}"),
        ("Dimensiones por lecho — ancho × largo (m)", f"{datos['ancho_lecho']:,.1f} × {largo:,.1f}"),
    ]
    verificaciones = []
    if rango:
        a_min, a_max, c_min, c_max = rango
        verificaciones = [
            (f"Área per cápita = {datos['area_per_capita']:.2f} m²/hab — exigido: "
             f"{_texto_rango((a_min, a_max), 'm²/hab')} (Tabla 44)",
             _en_rango(datos["area_per_capita"], (a_min - 1e-9, a_max + 1e-9))),
            (f"Carga de sólidos = {datos['carga_solidos']:.0f} kg/m²·año — exigido: "
             f"{_texto_rango((c_min, c_max), 'kg/m²·año')} (Tabla 44)",
             _en_rango(datos["carga_solidos"], (c_min, c_max))),
        ]
    final = (
        f"{n} lechos de {datos['ancho_lecho']:,.1f} m × {largo:,.1f} m  "
        f"(área total {area:,.0f} m²)"
    )
    return _resultado(valores, filas, verificaciones, final)


# ======================================================================
# Orden del tren de tratamiento: (atributo en EstadoProyecto, título).
# Lo usan el submenú de la PTAR y el informe PDF.
# ======================================================================
ESTRUCTURAS_PTAR = [
    ("ptar_caudal_ar", "Caudal de aguas residuales"),
    ("ptar_rejillas", "Rejillas (cribado)"),
    ("ptar_desarenador", "Desarenador"),
    ("ptar_trampa_grasas", "Trampa de grasas"),
    ("ptar_uasb", "Reactor UASB"),
    ("ptar_laguna_facultativa", "Laguna facultativa"),
    ("ptar_lechos_secado", "Lechos de secado de lodos"),
]
