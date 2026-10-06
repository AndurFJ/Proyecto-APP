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

    # ---------------- MEZCLA RÁPIDA ----------------
    {
        "categoria": "Mezcla Rápida",
        "titulo": "Requisitos de Diseño para Mezcla Rápida (Canaleta Parshall)",
        "fuente": "Resolución 0330 de 2017 (mod. Res. 799 de 2021); Romero Rojas / Arboleda",
        "columnas": ["Parámetro", "Valor"],
        "filas": [
            ["Gradiente medio de velocidad (G)", "1000 - 2000 s⁻¹"],
            ["Tiempo de mezcla en mezcladores hidráulicos", "< 1 s"],
            ["Número de Froude del resalto", "1.7 - 2.5 ó 4.5 - 9.0"],
            ["Relación Ha / W (recomendación)", "0.4 - 0.8"],
        ],
        "notas": (
            "Evitar el rango de Froude 2.5 - 4.5 (resalto oscilante). El coagulante se "
            "aplica en el resalto, a la salida de la garganta."
        ),
    },
    {
        "categoria": "Mezcla Rápida",
        "titulo": "Canaletas Parshall Normalizadas — Q = K·Ha^n",
        "fuente": "Azevedo Netto; Romero Rojas, 'Potabilización del agua'",
        "columnas": ["W", "W (cm)", "K", "n", "Q mín (L/s)", "Q máx (L/s)"],
        "filas": [
            ['1"', "2.5", "0.0604", "1.550", "0.28", "5.67"],
            ['2"', "5.1", "0.1207", "1.550", "0.57", "14.15"],
            ['3"', "7.6", "0.176", "1.547", "0.85", "53.8"],
            ['6"', "15.2", "0.381", "1.580", "1.42", "110.4"],
            ['9"', "22.9", "0.535", "1.530", "2.58", "251.9"],
            ["1'", "30.5", "0.690", "1.522", "3.11", "455.6"],
            ["1.5'", "45.7", "1.054", "1.538", "4.25", "696.2"],
            ["2'", "61.0", "1.426", "1.550", "11.89", "936.7"],
            ["3'", "91.5", "2.182", "1.566", "17.26", "1426.3"],
            ["4'", "122.0", "2.935", "1.578", "36.79", "1921.5"],
            ["5'", "152.5", "3.728", "1.587", "62.8", "2422"],
            ["6'", "183.0", "4.515", "1.595", "74.4", "2929"],
            ["7'", "213.5", "5.306", "1.601", "115.4", "3440"],
            ["8'", "244.0", "6.101", "1.606", "130.7", "3950"],
        ],
        "notas": "Q en m³/s y Ha en m. Las dimensiones A-N de cada canaleta están en ventana_mezcla_rapida.py.",
    },

    # ---------------- FLOCULACIÓN ----------------
    {
        "categoria": "Floculación",
        "titulo": "Requisitos de Diseño para Floculadores Hidráulicos",
        "fuente": "Resolución 0330 de 2017 (mod. Res. 799 de 2021); RAS Título C",
        "columnas": ["Parámetro", "Valor"],
        "filas": [
            ["Gradiente medio de velocidad (G)", "20 - 70 s⁻¹ (decreciente)"],
            ["Tiempo de retención total", "20 - 40 min"],
            ["Velocidad del agua en los canales", "0.10 - 0.60 m/s"],
            ["Paso libre en cada vuelta", "1.5 veces el ancho del canal"],
            ["Coeficiente de pérdida por vuelta (K)", "2 - 4 (típico 3)"],
        ],
        "notas": (
            "El tiempo de retención y los gradientes óptimos deberían confirmarse con "
            "ensayos de jarras sobre el agua cruda."
        ),
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
