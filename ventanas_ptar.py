"""
Módulo PTAR (Planta de Tratamiento de Aguas Residuales).

Contiene el submenú de procesos de la PTAR y una ventana de cálculo
por cada estructura del tren de tratamiento adoptado:

    1. Caudal de aguas residuales ... Res. 0330/2017, Art. 134 y 166
    2. Rejillas (cribado) ........... Art. 186
    3. Desarenador .................. Art. 188
    4. Trampa de grasas ............. Art. 185 (dimensiones según Art. 172)
    5. Reactor UASB ................. Art. 191 (Tablas 31, 32 y 33)
    6. Laguna facultativa ........... Art. 199 y 201
    7. Lechos de secado de lodos .... Art. 211 (Tabla 44)

Las fórmulas están en ptar_calculos.py, los rangos normativos en
ptar_criterios.py y la apariencia en ptar_ui.py / tema.py. Este archivo
solo une las tres cosas: qué datos pide cada ventana, de dónde salen
los datos de pasos anteriores y dónde se guarda el resultado.
"""

import tkinter as tk
from tkinter import messagebox

import ptar_calculos as calc
import ptar_criterios as C
import tema
from tema import fuente
from tema import C as T
from estado_proyecto import EstadoProyecto
from ptar_ui import VentanaCalculoPTAR, RequisitoFaltante, campo
from ui_utils import ajustar_geometria
from ventana_caudal_diseno import nivel_de_complejidad
from ventana_datos_tecnicos import VentanaDatosTecnicos


def _caudales_ptar():
    """Valores del caudal de aguas residuales, o RequisitoFaltante."""
    valores = EstadoProyecto.ptar_valores("ptar_caudal_ar")
    if valores is None:
        raise RequisitoFaltante(
            "Primero debe calcular el Caudal de Diseño — PTAR "
            "(caudal de aguas residuales)."
        )
    return valores


# ======================================================================
# 1. CAUDAL DE AGUAS RESIDUALES
# ======================================================================
class VentanaCaudalPTAR(VentanaCalculoPTAR):
    TITULO = "CAUDAL DE DISEÑO — PTAR"
    SUBTITULO = ("Caudal de aguas residuales — Res. 0330 de 2017, Art. 134 "
                 "(mod. Res. 799 de 2021) y Art. 166 (caudal de diseño de la PTAR)")
    TITULO_FINAL = "✅ ESTE ES EL CAUDAL DE DISEÑO DE LA PTAR"
    ATRIBUTO_ESTADO = "ptar_caudal_ar"

    @classmethod
    def datos_base(cls):
        if not EstadoProyecto.esta_definido():
            raise RequisitoFaltante(
                "Primero debe definir los Datos Preliminares (proyección poblacional)."
            )
        return {"poblacion": float(EstadoProyecto.poblacion_diseño)}

    def info_base(self):
        return [
            ("Municipio", f"{EstadoProyecto.municipio} ({EstadoProyecto.departamento})"),
            ("Población de diseño (hab)", f"{EstadoProyecto.poblacion_diseño:,.0f}"),
            ("Nivel de complejidad", nivel_de_complejidad(EstadoProyecto.poblacion_diseño)),
        ]

    def campos(self):
        if EstadoProyecto.dotacion_neta is not None:
            dotacion = round(EstadoProyecto.dotacion_neta, 1)
            nota_dot = ("Se toma la dotación neta del Caudal de Diseño de la PTAP. "
                        "Al cambiar la altitud se reemplaza por el valor del Art. 43.")
        else:
            dotacion = C.DOTACION_NETA_POR_ALTITUD["< 1000 m.s.n.m."]
            nota_dot = "Dotación neta máxima según la altitud del municipio (Art. 43)."
        return [
            campo("altitud", "Altitud promedio del municipio (Art. 43)", "< 1000 m.s.n.m.",
                  opciones=list(C.DOTACION_NETA_POR_ALTITUD)),
            campo("dotacion_neta", "Dotación neta — DN (L/hab·día)", dotacion, nota=nota_dot),
            campo("coef_retorno", "Coeficiente de retorno — CR", C.COEF_RETORNO_DEFECTO,
                  nota="Art. 134: sin mediciones de campo se toma CR = 0,85."),
            campo("area_total", "Área total del casco urbano (ha)", "",
                  nota="Puede medirse con Google Earth Pro sobre el perímetro urbano."),
            campo("porc_urbana", "Fracción del área que es urbana/drenada (decimal)",
                  C.PORC_AREA_URBANA),
            campo("porc_industrial", "Fracción del área industrial (decimal)", C.PORC_AREA_INDUSTRIAL),
            campo("aporte_industrial", "Aporte unitario industrial (L/s·ha)", C.APORTE_INDUSTRIAL_LS_HA),
            campo("porc_comercial", "Fracción del área comercial (decimal)", C.PORC_AREA_COMERCIAL),
            campo("aporte_comercial", "Aporte unitario comercial (L/s·ha)", C.APORTE_COMERCIAL_LS_HA),
            campo("porc_institucional", "Fracción del área institucional (decimal)",
                  C.PORC_AREA_INSTITUCIONAL),
            campo("aporte_institucional", "Aporte unitario institucional (L/s·ha)",
                  C.APORTE_INSTITUCIONAL_LS_HA,
                  nota="Aportes no domésticos: la Res. 0330 pide estimarlos con información "
                       "local; por defecto se usan los del Excel PTAR del proyecto (RAS 2000, D.3.3)."),
            campo("aporte_infiltracion", "Aporte por infiltración (L/s·ha)",
                  C.INFILTRACION_DEFECTO_LS_HA,
                  nota="Art. 134: sin aforos se acepta 0,1 L/s·ha (sobre el área urbana)."),
            campo("aporte_conexiones_erradas", "Aporte por conexiones erradas (L/s·ha)",
                  C.CONEXIONES_ERRADAS_MAX_LS_HA,
                  nota="Art. 134: sin información, valor máximo de 0,2 L/s·ha."),
        ]

    def al_cambiar_opcion(self, clave, valor):
        if clave == "altitud":
            self.fijar_valor("dotacion_neta", C.DOTACION_NETA_POR_ALTITUD[valor])

    def calcular_resultado(self, datos):
        return calc.calcular_caudal_ar(datos)

    def guardar_extra(self, r):
        v = r["valores"]
        EstadoProyecto.ptar_nivel_complejidad = nivel_de_complejidad(v["poblacion"])
        EstadoProyecto.ptar_dotacion_neta = v["dotacion_neta"]
        EstadoProyecto.ptar_qmd = v["q_medio"]
        EstadoProyecto.ptar_q_max_horario = v["q_max_horario"]
        EstadoProyecto.ptar_caudal_diseño_Ls = v["q_diseño"]
        EstadoProyecto.ptar_caudal_diseño_m3s = v["q_diseño"] / 1000


# ======================================================================
# 2. REJILLAS
# ======================================================================
class VentanaRejillasPTAR(VentanaCalculoPTAR):
    TITULO = "REJILLAS (CRIBADO) — PTAR"
    SUBTITULO = ("Res. 0330 de 2017, Art. 186 — separación de barras, velocidad máx. "
                 "1,2 m/s con Qmax y 0,3 m/s con Qmin")
    TITULO_FINAL = "✅ DIMENSIONES DEL CANAL DE REJILLAS"
    ATRIBUTO_ESTADO = "ptar_rejillas"

    @classmethod
    def datos_base(cls):
        q = _caudales_ptar()
        return {"q_max_ls": q["q_diseño"], "q_min_ls": q["q_min"], "q_medio_ls": q["q_medio"]}

    def info_base(self):
        b = self.base
        return [
            ("Caudal de diseño — Qmax (L/s)", f"{b['q_max_ls']:,.2f}"),
            ("Caudal medio (L/s)", f"{b['q_medio_ls']:,.2f}"),
            ("Caudal mínimo de referencia (L/s)", f"{b['q_min_ls']:,.2f}"),
        ]

    def campos(self):
        # Ancho sugerido: el que da una velocidad de ~0,6 m/s con tirante ≈ 0,8·B.
        area = self.base["q_max_ls"] / 1000 / 0.6
        ancho = max(0.30, round((area / 0.8) ** 0.5 / 0.05) * 0.05)
        return [
            campo("ancho_canal", "Ancho del canal de aproximación — B (m)", round(ancho, 2)),
            campo("pendiente", "Pendiente del canal (m/m)", C.PENDIENTE_CANAL_DEFECTO),
            campo("manning", "Coeficiente de Manning — n", C.MANNING_CONCRETO),
            campo("separacion_cm", "Separación libre entre barras — b (cm)",
                  C.SEPARACION_REJILLA_DEFECTO_CM,
                  nota="Art. 186: gruesas 4–10 cm, medias 2–4 cm, finas 1–2 cm."),
            campo("espesor_cm", "Espesor de las barras — t (cm)", C.ESPESOR_BARRA_DEFECTO_CM),
            campo("angulo", "Inclinación de las barras respecto a la horizontal (°)",
                  C.ANGULO_REJILLA_DEFECTO, nota="Limpieza manual: típico 45° a 60°."),
            campo("beta", "Factor de forma de Kirschmer — β", C.BETA_KIRSCHMER_DEFECTO,
                  nota="2,42 barra rectangular; 1,79 barra circular."),
            campo("borde_libre", "Borde libre del canal (m)", 0.30),
        ]

    def calcular_resultado(self, datos):
        return calc.calcular_rejillas(datos)


# ======================================================================
# 3. DESARENADOR
# ======================================================================
class VentanaDesarenadorPTAR(VentanaCalculoPTAR):
    TITULO = "DESARENADOR — PTAR"
    SUBTITULO = ("Res. 0330 de 2017, Art. 188 — partícula ≥ 0,3 mm, Vs = 0,03 m/s, "
                 "Vh = 0,3 m/s (velocidad constante), mínimo dos unidades")
    TITULO_FINAL = "✅ DIMENSIONES DEL DESARENADOR (por unidad)"
    ATRIBUTO_ESTADO = "ptar_desarenador"

    @classmethod
    def datos_base(cls):
        q = _caudales_ptar()
        return {"q_max_ls": q["q_diseño"], "q_medio_ls": q["q_medio"]}

    def info_base(self):
        return [
            ("Caudal de diseño — Qmax (L/s)", f"{self.base['q_max_ls']:,.2f}"),
            ("Caudal medio (L/s)", f"{self.base['q_medio_ls']:,.2f}"),
        ]

    def campos(self):
        return [
            campo("num_unidades", "Número de unidades en paralelo",
                  C.UNIDADES_MIN_DESARENADOR, nota="Art. 188: mínimo dos unidades."),
            campo("vh", "Velocidad horizontal — Vh (m/s)", C.VH_DESARENADOR_MS,
                  nota="Se mantiene constante con un vertedero proporcional o canaleta "
                       "Parshall a la salida."),
            campo("vs", "Velocidad de sedimentación — Vs (m/s)", C.VS_DESARENADOR_MS),
            campo("relacion_bh", "Relación ancho / profundidad — B/H", C.RELACION_BH_DESARENADOR),
            campo("factor_seguridad", "Factor de seguridad de la longitud",
                  C.FACTOR_SEGURIDAD_LONGITUD, nota="Por turbulencia de entrada (típico 1,5)."),
            campo("arena_l_m3", "Arena retenida (L por m³ de agua residual)",
                  C.ARENA_RETENIDA_L_M3, nota="Valores típicos: 0,004 a 0,037 L/m³."),
            campo("dias_limpieza", "Días entre limpiezas", C.DIAS_LIMPIEZA_DESARENADOR),
        ]

    def calcular_resultado(self, datos):
        return calc.calcular_desarenador(datos)


# ======================================================================
# 4. TRAMPA DE GRASAS
# ======================================================================
class VentanaTrampaGrasasPTAR(VentanaCalculoPTAR):
    TITULO = "TRAMPA DE GRASAS — PTAR"
    SUBTITULO = ("Res. 0330 de 2017, Art. 185 (remoción de grasas en el tratamiento "
                 "preliminar) con los criterios del Art. 172: TR ≥ 2,5 min, L:B de 1:1 a 3:1")
    TITULO_FINAL = "✅ DIMENSIONES DE LA TRAMPA DE GRASAS (por unidad)"
    ATRIBUTO_ESTADO = "ptar_trampa_grasas"

    @classmethod
    def datos_base(cls):
        q = _caudales_ptar()
        return {"q_max_ls": q["q_diseño"], "q_medio_ls": q["q_medio"]}

    def info_base(self):
        return [("Caudal de diseño — Qmax (L/s)", f"{self.base['q_max_ls']:,.2f}")]

    def campos(self):
        return [
            campo("num_unidades", "Número de unidades en paralelo", 2),
            campo("tr_min", "Tiempo de retención (min)", C.TR_TRAMPA_DEFECTO_MIN,
                  nota="Art. 172: mínimo 2,5 minutos."),
            campo("profundidad", "Profundidad útil — H (m)", C.PROFUNDIDAD_TRAMPA_DEFECTO_M,
                  nota="Art. 172: mínimo 0,35 m."),
            campo("relacion_lb", "Relación largo / ancho — L/B", 2.0),
            campo("borde_libre", "Borde libre (m)", 0.30),
        ]

    def calcular_resultado(self, datos):
        return calc.calcular_trampa_grasas(datos)


# ======================================================================
# 5. REACTOR UASB
# ======================================================================
class VentanaUASB(VentanaCalculoPTAR):
    TITULO = "REACTOR UASB — PTAR"
    SUBTITULO = ("Res. 0330 de 2017, Art. 191 — TRH según temperatura (Tabla 31), "
                 "velocidad ascensional (Tabla 32), profundidad 4,5–6 m, distribuidores (Tabla 33)")
    TITULO_FINAL = "✅ DIMENSIONES DEL REACTOR UASB"
    ATRIBUTO_ESTADO = "ptar_uasb"

    @classmethod
    def datos_base(cls):
        q = _caudales_ptar()
        return {"q_medio_ls": q["q_medio"], "q_pico_ls": q["q_diseño"]}

    def info_base(self):
        return [
            ("Caudal medio — QmAR (L/s)", f"{self.base['q_medio_ls']:,.2f}"),
            ("Caudal de diseño / pico (L/s)", f"{self.base['q_pico_ls']:,.2f}"),
        ]

    def campos(self):
        return [
            campo("temperatura", "Temperatura del agua residual (°C)", C.TEMPERATURA_DEFECTO_C),
            campo("trh", "Tiempo de retención hidráulica — TRH (h)", 9.0,
                  nota="Tabla 31: 16–19 °C → 10–14 h; 20–26 °C → 6–9 h; > 26 °C → > 6 h."),
            campo("profundidad", "Profundidad del reactor — H (m)", C.PROFUNDIDAD_UASB[0],
                  nota="Art. 191: entre 4,5 y 6 m. Con H/TRH se fija la velocidad ascensional media."),
            campo("num_modulos", "Número de módulos", 2),
            campo("dbo", "DBO₅ del agua residual cruda (mg/L)", C.DBO_AFLUENTE_DEFECTO_MGL),
            campo("dqo", "DQO del agua residual cruda (mg/L)", C.DQO_AFLUENTE_DEFECTO_MGL,
                  nota="Idealmente de la caracterización del Art. 169; si no, valores típicos."),
            campo("eficiencia_dbo", "Eficiencia de remoción de DBO₅ (decimal)",
                  C.EFICIENCIA_DBO_UASB, nota="Típica de un UASB: 0,55 a 0,75."),
            campo("coef_lodo", "Producción de lodo (kg SST / kg DQO aplicada)",
                  C.COEF_PRODUCCION_LODO_UASB, nota="Típico: 0,10 a 0,20."),
            campo("area_distribuidor", "Área de influencia por distribuidor (m²)",
                  C.AREA_DISTRIBUIDOR_DEFECTO_M2, nota="Tabla 33: entre 0,5 y 5,0 m²."),
        ]

    def calcular_resultado(self, datos):
        return calc.calcular_uasb(datos)


# ======================================================================
# 6. LAGUNA FACULTATIVA
# ======================================================================
class VentanaLagunaFacultativa(VentanaCalculoPTAR):
    TITULO = "LAGUNA FACULTATIVA — PTAR"
    SUBTITULO = ("Res. 0330 de 2017, Art. 199 — TRH 5–30 días, profundidad 1,5–2,5 m, "
                 "carga 100–350 kg DBO₅/ha·día; Art. 201 — borde libre 0,3–0,5 m")
    TITULO_FINAL = "✅ DIMENSIONES DE LAS LAGUNAS FACULTATIVAS"
    ATRIBUTO_ESTADO = "ptar_laguna_facultativa"

    @classmethod
    def datos_base(cls):
        q = _caudales_ptar()
        return {"q_medio_ls": q["q_medio"]}

    def info_base(self):
        return [("Caudal medio — QmAR (L/s)", f"{self.base['q_medio_ls']:,.2f}")]

    def campos(self):
        uasb = EstadoProyecto.ptar_valores("ptar_uasb")
        if uasb:
            dbo = round(uasb["dbo_efluente"], 1)
            temperatura = uasb["temperatura"]
            nota_dbo = "Tomada del efluente del reactor UASB."
        else:
            dbo = round(C.DBO_AFLUENTE_DEFECTO_MGL * (1 - C.EFICIENCIA_DBO_UASB), 1)
            temperatura = C.TEMPERATURA_DEFECTO_C
            nota_dbo = "Aún no hay UASB guardado: se estima con DBO 250 mg/L y 65% de remoción."
        lam = calc.carga_superficial_mara(temperatura)
        return [
            campo("dbo_afluente", "DBO₅ que entra a la laguna (mg/L)", dbo, nota=nota_dbo),
            campo("temperatura", "Temperatura del aire, mes más frío (°C)", temperatura),
            campo("carga_superficial", "Carga superficial de diseño (kg DBO₅/ha·día)",
                  round(lam), nota=f"Mara: λs = 350·(1,107 − 0,002·T)^(T − 25), limitada a "
                                   f"100–350 (Art. 199). A {temperatura:g} °C da {lam:,.0f}."),
            campo("profundidad", "Profundidad útil — H (m)", 2.0,
                  nota="Art. 199: entre 1,5 y 2,5 m."),
            campo("num_lagunas", "Número de lagunas en paralelo", 2),
            campo("relacion_lb", "Relación largo / ancho — L/B", C.RELACION_LB_LAGUNA_DEFECTO),
            campo("borde_libre", "Borde libre (m)", C.BORDE_LIBRE_LAGUNA[1],
                  nota="Art. 201: 0,3 a 0,5 m (0,51 a 0,8 m con alta turbulencia)."),
        ]

    def calcular_resultado(self, datos):
        return calc.calcular_laguna_facultativa(datos)


# ======================================================================
# 7. LECHOS DE SECADO
# ======================================================================
class VentanaLechosSecado(VentanaCalculoPTAR):
    TITULO = "LECHOS DE SECADO — PTAR"
    SUBTITULO = ("Res. 0330 de 2017, Art. 211, Tabla 44 — área por habitante y carga de "
                 "sólidos; reducción al 75% si los lechos se cubren")
    TITULO_FINAL = "✅ LECHOS DE SECADO"
    ATRIBUTO_ESTADO = "ptar_lechos_secado"

    @classmethod
    def datos_base(cls):
        _caudales_ptar()
        uasb = EstadoProyecto.ptar_valores("ptar_uasb")
        return {
            "poblacion": float(EstadoProyecto.poblacion_diseño),
            "lodo_kg_dia": uasb["lodo_kg_dia"] if uasb else 0.0,
        }

    def info_base(self):
        lodo = self.base["lodo_kg_dia"]
        return [
            ("Población de diseño (hab)", f"{self.base['poblacion']:,.0f}"),
            ("Lodo producido en el UASB (kg SST/día)",
             f"{lodo:,.0f}" if lodo else "— (guarde primero el reactor UASB)"),
        ]

    def campos(self):
        tipo = "Primario digerido"
        a_min, _, c_min, _ = C.LECHOS_SECADO_TABLA_44[tipo]
        return [
            campo("tipo_lodo", "Tipo de biosólido (Tabla 44)", tipo,
                  opciones=list(C.LECHOS_SECADO_TABLA_44),
                  nota="El lodo del UASB ya sale digerido; se asimila a 'Primario digerido'."),
            campo("area_per_capita", "Área por habitante (m²/hab)", a_min),
            campo("carga_solidos", "Carga de sólidos (kg SS/m²·año)", c_min),
            campo("cubierto", "¿Los lechos se cubren?", "No", opciones=["No", "Sí"]),
            campo("num_lechos", "Número de lechos", 8),
            campo("ancho_lecho", "Ancho de cada lecho (m)", C.ANCHO_LECHO_DEFECTO_M),
        ]

    def al_cambiar_opcion(self, clave, valor):
        if clave == "tipo_lodo":
            a_min, _, c_min, _ = C.LECHOS_SECADO_TABLA_44[valor]
            self.fijar_valor("area_per_capita", a_min)
            self.fijar_valor("carga_solidos", c_min)

    def calcular_resultado(self, datos):
        return calc.calcular_lechos_secado(datos)


VENTANAS_PTAR = {
    "ptar_caudal_ar": VentanaCaudalPTAR,
    "ptar_rejillas": VentanaRejillasPTAR,
    "ptar_desarenador": VentanaDesarenadorPTAR,
    "ptar_trampa_grasas": VentanaTrampaGrasasPTAR,
    "ptar_uasb": VentanaUASB,
    "ptar_laguna_facultativa": VentanaLagunaFacultativa,
    "ptar_lechos_secado": VentanaLechosSecado,
}


# ======================================================================
# SUBMENÚ DE PROCESOS DE LA PTAR
# ======================================================================
class ProcesosPTAR(tk.Toplevel):
    """Ventana con el listado de procesos de diseño de una PTAR."""

    # Nota: en este módulo `C` es ptar_criterios; los colores del tema
    # se importan como `T` (tema.C).

    def __init__(self, master, al_guardar_caudal=None):
        super().__init__(master)
        self.title("PTAR — Procesos de diseño")
        ajustar_geometria(self)
        self.configure(bg=T.FONDO)
        self.al_guardar_caudal = al_guardar_caudal

        self._crear_widgets()
        self._actualizar_estado_botones()

    def _crear_widgets(self):
        tema.encabezado(
            self, "PTAR — Procesos de diseño",
            "Planta de Tratamiento de Aguas Residuales · elija la estructura que desea diseñar",
        )

        cuerpo = tema.area_desplazable(self, bg=T.FONDO, ancho_max=1180, padx=40)

        tk.Label(
            cuerpo, text="MÓDULO PTAR · AGUAS RESIDUALES", font=fuente(9, "bold"),
            bg=T.FONDO, fg=T.PTAR, anchor="w",
        ).pack(fill="x", pady=(28, 0))

        barra = tk.Frame(cuerpo, bg=T.FONDO)
        barra.pack(fill="x", pady=(2, 4))
        tk.Label(
            barra, text="Procesos de la planta", font=fuente(18, "bold"),
            bg=T.FONDO, fg=T.TEXTO, anchor="w",
        ).pack(side="left")
        tema.boton(
            barra, "📚  Datos técnicos de referencia", self.abrir_datos_tecnicos,
            tipo="secundario", tamano=10,
        ).pack(side="right")

        tk.Label(
            cuerpo,
            text="Los procesos marcados con ✔ ya fueron calculados y guardados. "
                 "Empiece por el caudal de diseño.",
            font=fuente(10), bg=T.FONDO, fg=T.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x", pady=(0, 14))

        contenedor = tk.Frame(cuerpo, bg=T.FONDO)
        contenedor.pack(fill="x", pady=(0, 30))
        columnas = 2
        for c in range(columnas):
            contenedor.grid_columnconfigure(c, weight=1, uniform="procesos")

        self.botones = {}
        for i, (atributo, nombre) in enumerate(calc.ESTRUCTURAS_PTAR, start=1):
            btn = tk.Button(
                contenedor, text=f"{i:02d}    {nombre}", font=fuente(12, "bold"),
                bg=T.SUPERFICIE, fg=T.TEXTO, anchor="w", padx=24, pady=22,
                highlightthickness=1, highlightbackground=T.BORDE, cursor="hand2",
                command=lambda a=atributo: self.abrir_proceso(a),
            )
            btn.grid(row=(i - 1) // columnas, column=(i - 1) % columnas,
                     sticky="nsew", padx=6, pady=6)
            self.botones[atributo] = (btn, nombre)

    def _actualizar_estado_botones(self):
        """Marca con ✔ los procesos que ya fueron calculados y guardados."""
        for i, (atributo, (btn, nombre)) in enumerate(self.botones.items(), start=1):
            if EstadoProyecto.ptar_definido(atributo):
                btn.config(text=f"✔     {nombre}", bg=T.EXITO_FONDO, fg=T.EXITO,
                           highlightbackground=T.EXITO)
            else:
                btn.config(text=f"{i:02d}    {nombre}", bg=T.SUPERFICIE, fg=T.TEXTO,
                           highlightbackground=T.BORDE)

    def _al_guardar(self, atributo):
        self._actualizar_estado_botones()
        if atributo == "ptar_caudal_ar" and self.al_guardar_caudal:
            self.al_guardar_caudal()

    def abrir_proceso(self, atributo):
        clase = VENTANAS_PTAR[atributo]
        falta = clase.requisito_faltante()
        if falta:
            messagebox.showwarning("Falta un paso previo", falta, parent=self)
            return
        ventana = clase(self, al_guardar=lambda: self._al_guardar(atributo))
        ventana.grab_set()

    def abrir_datos_tecnicos(self):
        ventana = VentanaDatosTecnicos(self)
        ventana.grab_set()
