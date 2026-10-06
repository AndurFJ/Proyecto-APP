"""
Base de datos de tablas técnicas de referencia.

Aquí se van acumulando las tablas normativas (RAS 2000 u otras) y las
tablas tomadas del archivo Excel de referencia del proyecto, que se
usan a lo largo del software (Datos Preliminares, Caudal de Diseño,
PTAP, PTAR, etc.). Cada tabla indica explícitamente su fuente para
que siempre se sepa de dónde sale cada coeficiente.

Para agregar una tabla nueva (por ejemplo cuando se implemente
Aducción o Desarenador), basta con añadir un diccionario nuevo a la
lista TABLAS_REFERENCIA con esta misma estructura.
"""

TABLAS_REFERENCIA = [
    # ---------------- NIVEL DE COMPLEJIDAD ----------------
    {
        "categoria": "Nivel de Complejidad",
        "titulo": "Determinación del Nivel de Complejidad del Sistema",
        "fuente": "RAS 2000, Título A, Tabla A.3.1",
        "columnas": ["Nivel de complejidad", "Población en la zona urbana (hab)", "Capacidad económica de los usuarios"],
        "filas": [
            ["Bajo", "< 2.500", "Baja"],
            ["Medio", "2.501 a 12.500", "Baja"],
            ["Medio Alto", "12.501 a 60.000", "Media"],
            ["Alto", "> 60.000", "Alta"],
        ],
        "notas": "La población debe corresponder a la proyectada al final del período de diseño (horizonte de planeamiento).",
    },
    {
        "categoria": "Nivel de Complejidad",
        "titulo": "Métodos de Cálculo Poblacional Permitidos según el Nivel de Complejidad",
        "fuente": "RAS 2000, Título B, Tabla B.2.1, pág. B.30",
        "columnas": ["Método", "Bajo", "Medio", "Medio Alto", "Alto"],
        "filas": [
            ["Aritmético, Geométrico y Exponencial", "X", "X", "", ""],
            ["Aritmético + Geométrico + Exponencial + otros", "", "", "X", "X"],
            ["Por componentes (demográfico)", "", "", "X", "X"],
            ["Detallar por zonas y densidades", "", "", "X", "X"],
        ],
    },

    # ---------------- POBLACIÓN Y DEMANDA ----------------
    {
        "categoria": "Población y Demanda",
        "titulo": "Dotación Neta Máxima — usada actualmente en el software",
        "fuente": "Archivo Excel de referencia del proyecto",
        "columnas": ["Nivel de complejidad", "Población", "Dotación neta máxima (L/hab·día)"],
        "filas": [
            ["Bajo", "≤ 2.500", "110"],
            ["Medio", "2.501 a 12.500", "135"],
            ["Medio Alto", "12.501 a 60.000", "145"],
            ["Alto", "> 60.000", "155"],
        ],
        "notas": (
            "⚠ Estos son los valores que usa hoy 'Caudal de Diseño' en el software (dotacion_neta_maxima() "
            "en ventana_caudal_diseno.py). No coinciden exactamente con la Tabla B.2.2 oficial del RAS 2000 "
            "(ver tabla siguiente) — parecen corresponder a otra referencia (p. ej. Resolución 0330 de 2017 "
            "u otra guía). Vale la pena confirmar cuál es la fuente correcta antes de usarlos en un diseño real."
        ),
    },
    {
        "categoria": "Población y Demanda",
        "titulo": "Dotación Neta según el Nivel de Complejidad (Oficial RAS 2000)",
        "fuente": "RAS 2000, Título B, Tabla B.2.2, pág. B.34",
        "columnas": ["Nivel de complejidad", "Dotación neta mínima (L/hab·día)", "Dotación neta máxima (L/hab·día)"],
        "filas": [
            ["Bajo", "100", "150"],
            ["Medio", "120", "175"],
            ["Medio Alto", "130", "—"],
            ["Alto", "150", "—"],
        ],
        "notas": "'—' indica que el RAS 2000 no fija un máximo explícito para ese nivel.",
    },
    {
        "categoria": "Población y Demanda",
        "titulo": "Variación de la Dotación Neta según el Clima",
        "fuente": "RAS 2000, Título B, Tabla B.2.3, pág. B.35",
        "columnas": ["Nivel de complejidad", "Clima cálido (>28°C)", "Clima templado (20-28°C)", "Clima frío (<20°C)"],
        "filas": [
            ["Bajo", "+15%", "+10%", "No se admite"],
            ["Medio", "+15%", "+10%", "No se admite"],
            ["Medio Alto", "+20%", "+15%", "Corrección por clima"],
            ["Alto", "+20%", "+15%", "Corrección por clima"],
        ],
    },
    {
        "categoria": "Población y Demanda",
        "titulo": "Porcentajes Máximos Admisibles de Pérdidas Técnicas",
        "fuente": "RAS 2000, Título B, Tabla B.2.4, pág. B.36",
        "columnas": ["Nivel de complejidad", "% máximo admisible de pérdidas técnicas"],
        "filas": [
            ["Bajo", "40%"],
            ["Medio", "30%"],
            ["Medio Alto", "25%"],
            ["Alto", "20%"],
        ],
        "notas": "El software actual usa 25% como valor editable por defecto (porc_perdidas).",
    },

    # ---------------- CAUDAL DE DISEÑO ----------------
    {
        "categoria": "Caudal de Diseño",
        "titulo": "Coeficiente de Consumo Máximo Diario — K1",
        "fuente": "RAS 2000, Título B, Tabla B.2.5, pág. B.38",
        "columnas": ["Nivel de complejidad", "K1"],
        "filas": [
            ["Bajo", "1.30"],
            ["Medio", "1.30"],
            ["Medio Alto", "1.20"],
            ["Alto", "1.20"],
        ],
        "notas": "El software usa K1 = 1.4 como valor editable por defecto; ajústalo según el nivel de complejidad real.",
    },
    {
        "categoria": "Caudal de Diseño",
        "titulo": "Coeficiente de Consumo Máximo Horario — K2",
        "fuente": "RAS 2000, Título B, Tabla B.2.6, pág. B.38",
        "columnas": ["Nivel de complejidad", "Red menor de distribución", "Red secundaria", "Red matriz"],
        "filas": [
            ["Bajo", "1.60", "—", "—"],
            ["Medio", "1.60", "1.50", "—"],
            ["Medio Alto", "1.50", "1.45", "1.40"],
            ["Alto", "1.50", "1.45", "1.40"],
        ],
        "notas": "El software usa K2 = 1.5 como valor editable por defecto; ajústalo según el nivel de complejidad real y el tipo de red.",
    },

    # ---------------- CAPTACIÓN — BOCATOMA CON REJILLA ----------------
    {
        "categoria": "Captación — Bocatoma con Rejilla",
        "titulo": "Separación entre Barrotes (z) según Tipo de Grava",
        "fuente": "Archivo Excel de referencia del proyecto — Tabla 'Distancia entre barrotes X (m) para la rejilla'",
        "columnas": ["Tipo de grava", "Rango mínimo (m)", "Rango máximo (m)"],
        "filas": [
            ["Finas", "0.02", "0.04"],
            ["Medias", "0.04", "0.075"],
            ["Gruesas", "0.075", "0.15"],
        ],
        "notas": "El software usa el límite inferior del rango como valor de diseño (z), igual que el archivo Excel original.",
    },
    {
        "categoria": "Captación — Bocatoma con Rejilla",
        "titulo": "Forma y Coeficiente de los Barrotes (Kirschmer)",
        "fuente": "Archivo Excel de referencia del proyecto — Tabla 'Forma y coeficiente de los barrotes'",
        "columnas": ["Forma", "Coeficiente β"],
        "filas": [
            ["C1", "2.42"],
            ["C2", "1.83"],
            ["C3", "1.67"],
            ["C4", "1.035"],
            ["C5", "0.92"],
            ["C6", "0.76"],
            ["C7", "1.79"],
        ],
        "notas": "Usado en la pérdida de carga: Δh = β · (s/z)^1.33. Ver imagen de referencia para la forma en proyección vertical de cada barrote.",
    },
    {
        "categoria": "Captación — Bocatoma con Rejilla",
        "titulo": "Inclinación de las Rejillas",
        "fuente": "Archivo Excel de referencia del proyecto — Tabla 'Inclinación de las rejillas'",
        "columnas": ["Tipo", "Rango (grados)"],
        "filas": [
            ["Verticales", "75° - 85°"],
            ["Inclinadas", "45° - 60°"],
        ],
        "notas": "En el software puedes digitar el ángulo exacto dentro del rango correspondiente al tipo seleccionado.",
    },

    # ---------------- DESARENADOR ----------------
    {
        "categoria": "Desarenador",
        "titulo": "Requisitos Mínimos de Diseño para Desarenadores (Agua Potable)",
        "fuente": "Resolución 0330 de 2017, Art. 55",
        "columnas": ["Parámetro", "Valor"],
        "filas": [
            ["Diámetro mínimo de partícula a remover", "0.1 mm"],
            ["Peso específico de la arena", "2.65 g/cm³"],
            ["Velocidad horizontal máxima", "0.25 m/s"],
            ["Relación Vh / Vs máxima", "20"],
            ["Tiempo de retención mínimo (partículas finas)", "20 minutos"],
            ["Pendiente mínima del sistema de evacuación de arenas", "10%"],
        ],
        "notas": (
            "La velocidad de asentamiento (Vs) se calcula en función de la temperatura del "
            "agua y el peso específico de la partícula, mediante la Ley de Stokes "
            "(régimen laminar): Vs = g·(ρs − ρw)·d² / (18·μ). El software dimensiona el "
            "desarenador por velocidad controlada (L = Vh·t, área transversal = Q/Vh) y usa "
            "Vs solo como verificación de que la partícula alcanza a asentar (Vs ≥ H/t); "
            "también verifica el número de Reynolds para confirmar el régimen laminar. "
            "⚠ Usar directamente As = Q/Vs para dimensionar (teoría de sedimentador ideal) "
            "implica ocultamente H = Vs·t, lo que para una partícula de 0.1 mm da una "
            "profundidad de ~10-11 m — no usar esa fórmula para este proceso."
        ),
    },
    {
        "categoria": "Desarenador",
        "titulo": "Propiedades del Agua según Temperatura",
        "fuente": "Tabla estándar de hidráulica (referencia general de diseño)",
        "columnas": ["Temperatura (°C)", "Viscosidad dinámica μ (mPa·s)", "Densidad ρ (kg/m³)"],
        "filas": [
            ["0", "1.787", "999.8"],
            ["5", "1.519", "1000.0"],
            ["10", "1.307", "999.7"],
            ["15", "1.139", "999.1"],
            ["20", "1.002", "998.2"],
            ["25", "0.890", "997.0"],
            ["30", "0.798", "995.6"],
        ],
        "notas": "El software interpola linealmente entre estos valores según la temperatura ingresada.",
    },

    # ---------------- PTAR — CAUDAL DE AGUAS RESIDUALES ----------------
    {
        "categoria": "PTAR — Caudal de Aguas Residuales",
        "titulo": "Aportes y Coeficientes del Caudal de Aguas Residuales",
        "fuente": "Resolución 0330 de 2017, Art. 134 (mod. Res. 799 de 2021)",
        "columnas": ["Parámetro", "Valor sin información local"],
        "filas": [
            ["Coeficiente de retorno (CR)", "0,85"],
            ["Infiltración", "0,1 L/s·ha"],
            ["Conexiones erradas", "máximo 0,2 L/s·ha"],
            ["Factor de mayoración (F)", "entre 1,4 y 3,8"],
        ],
        "notas": (
            "Qd = CR·P·DN/86400. El software calcula F con la fórmula de Flores "
            "(F = 3,5 / P^0,1, P en miles de habitantes) y lo limita a 1,4 – 3,8."
        ),
    },
    {
        "categoria": "PTAR — Caudal de Aguas Residuales",
        "titulo": "Caudal de Diseño de la PTAR",
        "fuente": "Resolución 0330 de 2017, Art. 166 (mod. Res. 799 de 2021)",
        "columnas": ["Tamaño de la planta", "Caudal de diseño de procesos y unidades"],
        "filas": [
            ["Q ≤ 30 L/s (excepto lagunas)", "3 × caudal medio de tiempo seco, sin infiltración ni conexiones erradas"],
            ["Q > 30 L/s y sistemas lagunares", "Según Tablas 22 y 23 del Art. 166 (factores pico)"],
        ],
        "notas": (
            "Para Q > 30 L/s el software usa QMH + Qinf + QCE como caudal de diseño "
            "hidráulico y el caudal medio para los procesos biológicos."
        ),
    },

    # ---------------- PTAR — TRATAMIENTO PRELIMINAR ----------------
    {
        "categoria": "PTAR — Tratamiento Preliminar",
        "titulo": "Rejillas",
        "fuente": "Resolución 0330 de 2017, Art. 186",
        "columnas": ["Parámetro", "Valor"],
        "filas": [
            ["Rejas gruesas (separación entre barras)", "4 a 10 cm"],
            ["Rejas medias", "2 a < 4 cm"],
            ["Rejas finas", "1 a < 2 cm"],
            ["Velocidad máxima con caudal máximo", "1,2 m/s"],
            ["Velocidad con caudal mínimo", "0,3 m/s"],
            ["Limpieza mecánica", "caudal medio ≥ 100 L/s"],
        ],
    },
    {
        "categoria": "PTAR — Tratamiento Preliminar",
        "titulo": "Desarenadores (aguas residuales)",
        "fuente": "Resolución 0330 de 2017, Art. 188",
        "columnas": ["Parámetro", "Valor"],
        "filas": [
            ["Diámetro mínimo de partícula a remover", "0,3 mm"],
            ["Velocidad de decantación", "0,03 m/s"],
            ["Velocidad horizontal (velocidad constante)", "0,3 m/s"],
            ["Número mínimo de unidades", "2"],
        ],
    },
    {
        "categoria": "PTAR — Tratamiento Preliminar",
        "titulo": "Trampas de Grasa",
        "fuente": "Resolución 0330 de 2017, Art. 185 y Art. 172",
        "columnas": ["Parámetro", "Valor"],
        "filas": [
            ["Tiempo de retención mínimo", "2,5 min"],
            ["Relación largo : ancho", "1:1 a 3:1"],
            ["Profundidad útil mínima", "0,35 m"],
            ["Desengrasador aireado", "plantas con caudal ≥ 100 L/s"],
        ],
        "notas": "El Art. 185 exige prever la remoción de grasas en el tratamiento preliminar de sistemas centralizados.",
    },

    # ---------------- PTAR — TRATAMIENTO BIOLÓGICO ----------------
    {
        "categoria": "PTAR — Tratamiento Biológico",
        "titulo": "Reactor UASB — Tiempo de Retención Hidráulica (Tabla 31)",
        "fuente": "Resolución 0330 de 2017, Art. 191, Tabla 31",
        "columnas": ["Temperatura del agua residual (°C)", "TRH (h)"],
        "filas": [
            ["16 – 19", "10 – 14"],
            ["20 – 26", "6 – 9"],
            ["> 26", "> 6"],
        ],
    },
    {
        "categoria": "PTAR — Tratamiento Biológico",
        "titulo": "Reactor UASB — Velocidad Ascensional (Tabla 32) y Geometría",
        "fuente": "Resolución 0330 de 2017, Art. 191, Tablas 32 y 33",
        "columnas": ["Parámetro", "Valor"],
        "filas": [
            ["Velocidad ascensional con caudal medio", "0,5 – 0,7 m/h"],
            ["Velocidad ascensional con caudal máximo", "0,9 – 1,1 m/h"],
            ["Velocidad ascensional con picos temporales", "< 1,5 m/h"],
            ["Profundidad del reactor", "4,5 – 6 m"],
            ["Separador gas-sólido-líquido", "2,5 m de altura, placas a 45°"],
            ["Área de influencia por distribuidor (Tabla 33)", "0,5 – 5,0 m²"],
        ],
    },
    {
        "categoria": "PTAR — Tratamiento Biológico",
        "titulo": "Lagunas de Estabilización",
        "fuente": "Resolución 0330 de 2017, Arts. 198, 199, 200 y 201",
        "columnas": ["Tipo", "Profundidad", "Tiempo de retención", "Carga"],
        "filas": [
            ["Anaerobia (Art. 198)", "2,5 – 5 m", "1 – 3 días", "100 – 500 g DBO₅/m³·día"],
            ["Facultativa (Art. 199)", "1,5 – 2,5 m", "5 – 30 días", "100 – 350 kg DBO₅/ha·día"],
            ["Maduración (Art. 200)", "0,9 – 1 m", "—", "—"],
        ],
        "notas": "Borde libre (Art. 201): 0,3 a 0,5 m; 0,51 a 0,8 m en condiciones de alta turbulencia.",
    },

    # ---------------- PTAR — LODOS ----------------
    {
        "categoria": "PTAR — Manejo de Lodos",
        "titulo": "Lechos de Secado (Tabla 44)",
        "fuente": "Resolución 0330 de 2017, Art. 211, Tabla 44",
        "columnas": ["Tipo de biosólido", "Área (m²/hab)", "Carga (kg SS/m²·año)"],
        "filas": [
            ["Primario digerido", "0,10", "120 – 150"],
            ["Filtro percolador digerido", "0,12 – 0,16", "90 – 120"],
            ["Lodos activados digeridos", "0,16 – 0,24", "60 – 100"],
        ],
        "notas": "Los valores pueden reducirse al 75% cuando los lechos de secado se cubren.",
    },
]


def obtener_categorias():
    """Retorna la lista de categorías, en el orden en que aparecen los datos."""
    vistas = []
    for tabla in TABLAS_REFERENCIA:
        if tabla["categoria"] not in vistas:
            vistas.append(tabla["categoria"])
    return vistas


def obtener_tablas_por_categoria(categoria):
    """Retorna las tablas (dicts) que pertenecen a una categoría dada."""
    return [t for t in TABLAS_REFERENCIA if t["categoria"] == categoria]
