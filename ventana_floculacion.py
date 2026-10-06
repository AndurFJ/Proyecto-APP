"""
Ventana de Floculación — Floculador hidráulico de pantallas (flujo horizontal).

Siguiente proceso de diseño de la PTAP (después de la mezcla rápida):
el agua ya coagulada recorre canales separados por pantallas, con
velocidades decrecientes, para que los microflóculos crezcan sin
romperse.

Requisitos de la Resolución 0330 de 2017 (mod. Res. 799 de 2021) y del
RAS para floculación (ver constantes más abajo):

- Gradiente medio de velocidad (G) entre 20 y 70 s⁻¹, decreciente de
  una zona a la siguiente.
- Tiempo de retención total entre 20 y 40 minutos.
- En floculadores hidráulicos, velocidad del agua en los canales entre
  0.10 y 0.60 m/s.

MÉTODO DE DISEÑO (Romero Rojas / Arboleda), por cada zona:

    L   = v · t                       recorrido del agua en la zona
    Ac  = Q / v                       área de cada canal
    a   = Ac / h                      ancho del canal entre pantallas
    lc  = B − 1.5·a                   longitud útil de cada canal (deja
                                       un paso de 1.5·a en cada vuelta)
    N   = ⌈L / lc⌉                    número de canales
    Lz  = N·a + (N − 1)·e             longitud de la zona en planta
    h1  = K·(N − 1)·v² / 2g           pérdidas en las vueltas
    R   = a·h / (a + 2h)
    h2  = (n·v / R^(2/3))² · L        pérdidas por fricción (Manning)
    G   = √(γ·(h1 + h2) / (μ·t))
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

from estado_proyecto import EstadoProyecto
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria
from ventana_desarenador import propiedades_agua


G_GRAV = 9.81  # m/s2

GRADIENTE_MIN = 20         # s-1
GRADIENTE_MAX = 70         # s-1
T_TOTAL_MIN = 20           # min
T_TOTAL_MAX = 40           # min
VELOCIDAD_MIN = 0.10       # m/s
VELOCIDAD_MAX = 0.60       # m/s

NUM_ZONAS = 3
ZONAS_DEFECTO = [  # (tiempo min, velocidad m/s)
    (7, 0.20),
    (8, 0.15),
    (10, 0.11),
]
PROFUNDIDAD_DEFECTO = 1.0       # m
ANCHO_TANQUE_DEFECTO = 3.0      # m
ESPESOR_PANTALLA_DEFECTO = 0.05  # m
MANNING_DEFECTO = 0.013          # concreto / asbesto-cemento
K_VUELTAS_DEFECTO = 3.0


def calcular_zona(q_m3s, t_min, v, h, ancho_tanque, espesor, n_manning, k_vueltas, mu, gamma):
    """Calcula una zona del floculador. Retorna un dict con los resultados."""
    t_s = t_min * 60
    recorrido = v * t_s
    area_canal = q_m3s / v
    ancho_canal = area_canal / h
    longitud_canal = ancho_tanque - 1.5 * ancho_canal
    if longitud_canal <= 0:
        raise ValueError(
            f"El ancho del tanque ({ancho_tanque:.2f} m) es muy pequeño para canales de "
            f"{ancho_canal:.2f} m. Aumente el ancho del tanque o la profundidad."
        )
    num_canales = math.ceil(recorrido / longitud_canal)
    longitud_zona = num_canales * ancho_canal + (num_canales - 1) * espesor

    perdida_vueltas = k_vueltas * (num_canales - 1) * v ** 2 / (2 * G_GRAV)
    radio_hidraulico = ancho_canal * h / (ancho_canal + 2 * h)
    perdida_friccion = (n_manning * v / radio_hidraulico ** (2 / 3)) ** 2 * recorrido
    perdida_total = perdida_vueltas + perdida_friccion
    gradiente = math.sqrt(gamma * perdida_total / (mu * t_s))

    return dict(
        t_min=t_min, v=v, recorrido=recorrido, area_canal=area_canal,
        ancho_canal=ancho_canal, longitud_canal=longitud_canal,
        num_canales=num_canales, longitud_zona=longitud_zona,
        perdida_vueltas=perdida_vueltas, perdida_friccion=perdida_friccion,
        perdida_total=perdida_total, gradiente=gradiente,
        cumple_velocidad=VELOCIDAD_MIN <= v <= VELOCIDAD_MAX,
        cumple_gradiente=GRADIENTE_MIN <= gradiente <= GRADIENTE_MAX,
    )


def calcular_floculador(q_total, num_unidades, temperatura_c, zonas, h, ancho_tanque,
                        espesor, n_manning, k_vueltas):
    """zonas: lista de (t_min, v). Retorna un dict con las zonas y los totales."""
    q_unidad = q_total / num_unidades
    mu, rho = propiedades_agua(temperatura_c)
    gamma = rho * G_GRAV

    resultados = [
        calcular_zona(q_unidad, t, v, h, ancho_tanque, espesor, n_manning, k_vueltas, mu, gamma)
        for t, v in zonas
    ]

    t_total = sum(z["t_min"] for z in resultados)
    perdida_total = sum(z["perdida_total"] for z in resultados)
    longitud_total = sum(z["longitud_zona"] for z in resultados) + espesor * (len(resultados) - 1)
    gradiente_medio = math.sqrt(gamma * perdida_total / (mu * t_total * 60))
    volumen = longitud_total * ancho_tanque * h

    gradientes = [z["gradiente"] for z in resultados]
    cumple_decreciente = all(g1 >= g2 for g1, g2 in zip(gradientes, gradientes[1:]))
    cumple_tiempo = T_TOTAL_MIN <= t_total <= T_TOTAL_MAX
    cumple_todo = (
        cumple_tiempo and cumple_decreciente
        and all(z["cumple_gradiente"] and z["cumple_velocidad"] for z in resultados)
    )

    return dict(
        q_total=q_total, num_unidades=num_unidades, q_unidad=q_unidad,
        temperatura=temperatura_c, mu=mu, rho=rho,
        profundidad=h, ancho_tanque=ancho_tanque, espesor=espesor,
        n_manning=n_manning, k_vueltas=k_vueltas,
        zonas=resultados, t_total=t_total, perdida_total=perdida_total,
        longitud_total=longitud_total, gradiente_medio=gradiente_medio, volumen=volumen,
        cumple_tiempo=cumple_tiempo, cumple_decreciente=cumple_decreciente,
        cumple_todo=cumple_todo,
    )


class VentanaFloculacion(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Floculación — Floculador de pantallas")
        ajustar_geometria(self)
        self.configure(bg=C.FONDO)

        self.al_guardar = al_guardar

        self._crear_estilos()
        self._crear_widgets()
        self._precargar()

    # ------------------------------------------------------------------
    def _crear_estilos(self):
        """Los estilos Editable.TEntry / Editable.TCombobox los define tema.py."""

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        cuerpo, lateral = tema.layout_formulario(
            self, "FLOCULACIÓN — FLOCULADOR HIDRÁULICO DE PANTALLAS",
            "Resolución 0330 de 2017 (mod. Res. 799 de 2021) — "
            "G entre 20 y 70 s⁻¹, tiempo total entre 20 y 40 min",
        )
        self.canvas = cuerpo.canvas

        def etiqueta(padre, texto, editable=False):
            if editable:
                texto = f"✎ {texto}   (dato editable)"
            tk.Label(
                padre, text=texto, font=fuente(10, "bold" if editable else "normal"),
                bg=C.SUPERFICIE, fg=C.EDITABLE_TEXTO if editable else C.TEXTO, anchor="w",
            ).pack(fill="x", pady=(8, 2))

        def resultado(padre, nombre_attr, valor_inicial="—"):
            lbl = tk.Label(
                padre, text=valor_inicial, font=fuente(11, "bold"),
                bg=C.RESULTADO_FONDO, fg=C.RESULTADO_TEXTO, anchor="w", relief="flat", bd=0,
                highlightthickness=1, highlightbackground=C.BORDE, padx=8,
            )
            lbl.pack(fill="x", ipady=4)
            setattr(self, nombre_attr, lbl)
            return lbl

        def nota(padre, texto):
            lbl = tk.Label(
                padre, text=texto, font=fuente(8, "italic"),
                bg=C.SUPERFICIE, fg=C.TEXTO_TENUE, anchor="w", justify="left", wraplength=680,
            )
            lbl.pack(fill="x", pady=(0, 2))
            return lbl

        def entrada(padre, texto, valor):
            etiqueta(padre, texto, editable=True)
            entry = ttk.Entry(padre, style="Editable.TEntry")
            entry.insert(0, str(valor))
            entry.pack(fill="x")
            return entry

        # --- Caudal ---
        etiqueta(cuerpo, "Caudal de diseño (m³/s):")
        resultado(cuerpo, "lbl_caudal")

        self.entry_num_unidades = entrada(cuerpo, "Número de unidades en paralelo:", 1)

        etiqueta(cuerpo, "Caudal por unidad (m³/s):")
        resultado(cuerpo, "lbl_caudal_unidad")

        self.entry_temperatura = entrada(cuerpo, "Temperatura del agua (°C):", "")

        etiqueta(cuerpo, "Viscosidad dinámica — μ (Pa·s)   /   Peso específico — γ (N/m³):")
        resultado(cuerpo, "lbl_propiedades")

        # --- Geometría del tanque ---
        self.entry_profundidad = entrada(cuerpo, "Profundidad del agua — h (m):", PROFUNDIDAD_DEFECTO)
        self.entry_ancho_tanque = entrada(
            cuerpo, "Ancho del tanque (longitud de las pantallas) — B (m):", ANCHO_TANQUE_DEFECTO,
        )
        self.entry_espesor = entrada(cuerpo, "Espesor de las pantallas — e (m):", ESPESOR_PANTALLA_DEFECTO)
        self.entry_manning = entrada(cuerpo, "Coeficiente de Manning — n:", MANNING_DEFECTO)
        self.entry_k_vueltas = entrada(cuerpo, "Coeficiente de pérdida en las vueltas — K:", K_VUELTAS_DEFECTO)
        nota(cuerpo, "En cada vuelta se deja un paso de 1.5 veces el ancho del canal entre el "
                     "extremo de la pantalla y el muro.")

        # --- Zonas ---
        etiqueta(cuerpo, f"Zonas de floculación — tiempo y velocidad "
                         f"({VELOCIDAD_MIN:.2f}-{VELOCIDAD_MAX:.2f} m/s):", editable=True)
        tabla_zonas = tk.Frame(cuerpo, bg=C.BORDE)
        tabla_zonas.pack(fill="x")
        for col, texto in enumerate(["Zona", "t (min)", "v (m/s)"]):
            tk.Label(
                tabla_zonas, text=texto, font=fuente(9, "bold"), bg=C.ENCABEZADO, fg="white", pady=4,
            ).grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            tabla_zonas.columnconfigure(col, weight=1)
        self.entries_zonas = []
        for i, (t, v) in enumerate(ZONAS_DEFECTO[:NUM_ZONAS], start=1):
            tk.Label(tabla_zonas, text=str(i), bg=C.SUPERFICIE, fg=C.TEXTO).grid(row=i, column=0, sticky="nsew", padx=1, pady=1)
            entry_t = ttk.Entry(tabla_zonas, style="Editable.TEntry", width=10)
            entry_t.insert(0, str(t))
            entry_t.grid(row=i, column=1, sticky="ew", padx=1, pady=1)
            entry_v = ttk.Entry(tabla_zonas, style="Editable.TEntry", width=10)
            entry_v.insert(0, str(v))
            entry_v.grid(row=i, column=2, sticky="ew", padx=1, pady=1)
            self.entries_zonas.append((entry_t, entry_v))
        nota(cuerpo, "Las velocidades deben disminuir de una zona a la siguiente para que el "
                     "gradiente sea decreciente y el flóculo formado no se rompa.")

        # --- Resultados por zona ---
        etiqueta(cuerpo, "Resultados por zona:")
        self.tabla_resultados = tk.Frame(cuerpo, bg=C.BORDE)
        self.tabla_resultados.pack(fill="x")
        encabezados = ["Zona", "a (m)", "N canales", "L recorrido (m)", "L zona (m)", "hf (m)", "G (s⁻¹)"]
        for col, texto in enumerate(encabezados):
            tk.Label(
                self.tabla_resultados, text=texto, font=fuente(9, "bold"), bg=C.ENCABEZADO, fg="white", pady=4,
            ).grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            self.tabla_resultados.columnconfigure(col, weight=1)
        self.celdas_resultados = []
        for i in range(1, NUM_ZONAS + 1):
            fila = []
            for col in range(len(encabezados)):
                lbl = tk.Label(
                    self.tabla_resultados, text=str(i) if col == 0 else "—",
                    font=fuente(9, "bold" if col else "normal"), bg=C.RESULTADO_FONDO, fg=C.RESULTADO_TEXTO,
                )
                lbl.grid(row=i, column=col, sticky="nsew", padx=1, pady=1)
                fila.append(lbl)
            self.celdas_resultados.append(fila)

        etiqueta(cuerpo, "Tiempo de retención total (20-40 min):")
        resultado(cuerpo, "lbl_t_total")

        etiqueta(cuerpo, "Pérdida de carga total (m)   /   Gradiente medio (s⁻¹):")
        resultado(cuerpo, "lbl_perdida_gradiente")

        etiqueta(cuerpo, "Gradiente decreciente entre zonas:")
        resultado(cuerpo, "lbl_decreciente")

        # --- Botón calcular ---
        tk.Button(
            lateral, text="Calcular", font=fuente(11, "bold"),
            bg=C.PRIMARIO, fg="white", cursor="hand2", command=self.calcular,
        ).pack(fill="x", pady=(15, 10), ipady=6)

        # --- Resultado final destacado ---
        marco_final = tk.Frame(
            lateral, bg=C.EXITO_FONDO, bd=0,
            highlightbackground=C.EXITO, highlightthickness=1,
        )
        marco_final.pack(fill="x", pady=(10, 15))
        tk.Label(
            marco_final, text="✅ DIMENSIONES DEL FLOCULADOR (por unidad)",
            font=fuente(11, "bold"), bg=C.EXITO_FONDO, fg=C.EXITO,
        ).pack(pady=(10, 4))
        self.lbl_dimensiones_final = tk.Label(
            marco_final, text="L: — m   ×   B: — m   ×   h: — m",
            font=fuente(15, "bold"), bg=C.EXITO_FONDO, fg=C.EXITO,
        )
        self.lbl_dimensiones_final.pack(pady=(0, 4))
        self.lbl_cumple_final = tk.Label(
            marco_final, text="", font=fuente(9, "bold"),
            bg=C.EXITO_FONDO, fg=C.EXITO, justify="center", wraplength=tema.ANCHO_TEXTO_LATERAL,
        )
        self.lbl_cumple_final.pack(pady=(0, 10))

        tk.Button(
            lateral, text="💾 Guardar y continuar", font=fuente(12, "bold"),
            bg=C.EXITO_BOTON, fg="white", cursor="hand2", command=self.guardar,
        ).pack(fill="x", ipady=8, pady=(0, 20))

        entradas = [
            self.entry_num_unidades, self.entry_temperatura, self.entry_profundidad,
            self.entry_ancho_tanque, self.entry_espesor, self.entry_manning, self.entry_k_vueltas,
        ] + [e for par in self.entries_zonas for e in par]
        for entry in entradas:
            entry.bind("<FocusOut>", lambda e: self.calcular(silencioso=True))

        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)

    # ------------------------------------------------------------------
    def _precargar(self):
        if not EstadoProyecto.caudal_definido():
            messagebox.showwarning(
                "Falta el caudal de diseño",
                "Primero debe calcular el Caudal de Diseño.",
            )
            self.destroy()
            return

        self.lbl_caudal.config(text=f"{EstadoProyecto.caudal_diseño_m3s:,.5f}")
        temperatura = (
            EstadoProyecto.floculacion_temperatura
            or EstadoProyecto.mezcla_temperatura
            or EstadoProyecto.desarenador_temperatura
            or 20
        )
        self.entry_temperatura.delete(0, "end")
        self.entry_temperatura.insert(0, f"{temperatura:g}")
        self.calcular(silencioso=True)

    # ------------------------------------------------------------------
    def calcular(self, silencioso=False):
        try:
            num_unidades = int(self.entry_num_unidades.get())
            temperatura = float(self.entry_temperatura.get())
            h = float(self.entry_profundidad.get())
            ancho_tanque = float(self.entry_ancho_tanque.get())
            espesor = float(self.entry_espesor.get())
            n_manning = float(self.entry_manning.get())
            k_vueltas = float(self.entry_k_vueltas.get())
            zonas = [(float(et.get()), float(ev.get())) for et, ev in self.entries_zonas]

            if num_unidades < 1:
                raise ValueError("El número de unidades debe ser al menos 1.")
            if h <= 0 or ancho_tanque <= 0:
                raise ValueError("La profundidad y el ancho del tanque deben ser mayores que 0.")
            if espesor < 0 or n_manning <= 0 or k_vueltas < 0:
                raise ValueError("Revise el espesor de pantallas, n de Manning y K.")
            if any(t <= 0 or v <= 0 for t, v in zonas):
                raise ValueError("Los tiempos y velocidades de cada zona deben ser mayores que 0.")

            r = calcular_floculador(
                EstadoProyecto.caudal_diseño_m3s, num_unidades, temperatura, zonas,
                h, ancho_tanque, espesor, n_manning, k_vueltas,
            )
        except (ValueError, TypeError, ZeroDivisionError) as e:
            if hasattr(self, "_resultado"):
                del self._resultado
            if not silencioso:
                messagebox.showwarning("Datos inválidos", f"Revise los valores ingresados.\n{e}")
            return

        if not r["cumple_todo"] and not silencioso:
            problemas = []
            if not r["cumple_tiempo"]:
                problemas.append(
                    f"• Tiempo total = {r['t_total']:.1f} min debe estar entre "
                    f"{T_TOTAL_MIN} y {T_TOTAL_MAX} min."
                )
            for i, z in enumerate(r["zonas"], start=1):
                if not z["cumple_velocidad"]:
                    problemas.append(
                        f"• Zona {i}: v = {z['v']:.2f} m/s debe estar entre "
                        f"{VELOCIDAD_MIN} y {VELOCIDAD_MAX} m/s."
                    )
                if not z["cumple_gradiente"]:
                    problemas.append(
                        f"• Zona {i}: G = {z['gradiente']:.1f} s⁻¹ debe estar entre "
                        f"{GRADIENTE_MIN} y {GRADIENTE_MAX} s⁻¹ (ajuste v o t)."
                    )
            if not r["cumple_decreciente"]:
                problemas.append("• El gradiente debe disminuir de una zona a la siguiente.")
            messagebox.showwarning(
                "Requisitos de floculación no cumplidos",
                "Ajuste el diseño:\n\n" + "\n".join(problemas),
            )

        self._resultado = r

        self.lbl_caudal_unidad.config(text=f"{r['q_unidad']:,.5f}")
        self.lbl_propiedades.config(text=f"{r['mu']:,.6f}   /   {r['rho'] * G_GRAV:,.0f}")

        for fila, z in zip(self.celdas_resultados, r["zonas"]):
            valores = [
                f"{z['ancho_canal']:,.3f}", f"{z['num_canales']}", f"{z['recorrido']:,.1f}",
                f"{z['longitud_zona']:,.2f}", f"{z['perdida_total']:,.4f}",
                f"{z['gradiente']:,.1f} {'✔' if z['cumple_gradiente'] else '⚠'}",
            ]
            for lbl, texto in zip(fila[1:], valores):
                lbl.config(text=texto)

        self.lbl_t_total.config(
            text=f"{r['t_total']:,.1f} min   {'✔ cumple' if r['cumple_tiempo'] else '⚠ no cumple'}"
        )
        self.lbl_perdida_gradiente.config(
            text=f"{r['perdida_total']:,.4f}   /   {r['gradiente_medio']:,.1f}"
        )
        self.lbl_decreciente.config(
            text=" → ".join(f"{z['gradiente']:,.1f}" for z in r["zonas"])
                 + f"   {'✔ decreciente' if r['cumple_decreciente'] else '⚠ no es decreciente'}"
        )

        self.lbl_dimensiones_final.config(
            text=f"L: {r['longitud_total']:,.2f} m   ×   B: {r['ancho_tanque']:,.2f} m   ×   "
                 f"h: {r['profundidad']:,.2f} m"
        )
        self.lbl_cumple_final.config(
            text=(
                f"{r['num_unidades']} unidad(es) — {sum(z['num_canales'] for z in r['zonas'])} canales — "
                f"t = {r['t_total']:,.0f} min — hf = {r['perdida_total']:,.3f} m — "
                f"{'✔ cumple los requisitos de floculación' if r['cumple_todo'] else '⚠ revise los parámetros marcados arriba'}"
            )
        )

    # ------------------------------------------------------------------
    def guardar(self):
        if not hasattr(self, "_resultado"):
            messagebox.showwarning("Falta calcular", "Primero presione Calcular.")
            return

        r = self._resultado
        EstadoProyecto.floculacion_num_unidades = r["num_unidades"]
        EstadoProyecto.floculacion_q_unidad = r["q_unidad"]
        EstadoProyecto.floculacion_temperatura = r["temperatura"]
        EstadoProyecto.floculacion_profundidad = r["profundidad"]
        EstadoProyecto.floculacion_ancho_tanque = r["ancho_tanque"]
        EstadoProyecto.floculacion_espesor_pantalla = r["espesor"]
        EstadoProyecto.floculacion_manning = r["n_manning"]
        EstadoProyecto.floculacion_k_vueltas = r["k_vueltas"]
        EstadoProyecto.floculacion_zonas = r["zonas"]
        EstadoProyecto.floculacion_t_total = r["t_total"]
        EstadoProyecto.floculacion_perdida_total = r["perdida_total"]
        EstadoProyecto.floculacion_gradiente_medio = r["gradiente_medio"]
        EstadoProyecto.floculacion_longitud_total = r["longitud_total"]
        EstadoProyecto.floculacion_volumen = r["volumen"]
        EstadoProyecto.floculacion_cumple = r["cumple_todo"]

        messagebox.showinfo(
            "Guardado",
            "Floculador guardado correctamente.\n\n" + EstadoProyecto.resumen_floculacion(),
        )

        if self.al_guardar:
            self.al_guardar()

        self.destroy()
