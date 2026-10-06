"""
Ventana de Desarenador.

Siguiente proceso de diseño de la PTAP (después de la captación):
remueve las partículas de arena en suspensión antes de que el agua
continúe hacia el resto de la planta.

Sigue el Art. 55 de la Resolución 0330 de 2017 (requisitos mínimos de
diseño para desarenadores en sistemas de agua potable):

- Diámetro mínimo de partícula a remover: 0.1 mm.
- Peso específico de la arena: 2.65 g/cm³.
- Velocidad de asentamiento (Vs): calculada según la temperatura del
  agua y el peso específico de la partícula (Ley de Stokes, régimen
  laminar — válido para partículas finas de este tamaño).
- Velocidad horizontal: inferior a 0.25 m/s.
- Relación Vh / Vs: inferior a 20.
- Tiempo de retención de partículas finas: no menor a 20 minutos.
- Pendiente del sistema de evacuación de arenas: superior al 10%.

MÉTODO DE DISEÑO — desarenador de flujo horizontal por velocidad
controlada (no sedimentador ideal tipo Hazen):

    L  = Vh · t                    (longitud: garantiza el tiempo de
                                     retención por construcción)
    Ac = Q / Vh                    (área transversal, por continuidad)
    H  = √(Ac / (B/H))             (profundidad, según relación B/H
                                     constructiva elegida)
    B  = (B/H) · H                 (ancho)

    Verificación (no dimensionamiento): la partícula crítica debe
    llegar al fondo dentro del tiempo disponible, es decir Vs ≥ H/t.
    Como H/t suele ser mucho menor que Vs (para tamaños de partícula
    normativos), esta verificación casi siempre se cumple.

    NOTA: la versión anterior de este módulo usaba As = Q/Vs para
    calcular L directamente (teoría de sedimentador ideal). Esa
    fórmula implica ocultamente H = Vs·t, lo que para una partícula
    de 0.1 mm da una profundidad de ~10-11 m — imposible de construir.
    Por eso se cambió al método de velocidad controlada, que es el que
    corresponde a un desarenador de flujo horizontal según el Art. 55.

    IMPORTANTE: L = Vh·t NO depende del caudal ni del número de
    unidades en paralelo — solo de la velocidad y el tiempo mínimo.
    Repartir el caudal en más unidades en paralelo NO acorta el canal
    (solo lo hace más angosto/bajo); para acortarlo hay que plegar esa
    misma longitud en varios tramos en serie (serpentín), lo cual NO
    cambia el volumen, la velocidad ni el tiempo de retención — solo
    empaqueta la misma longitud en menos espacio en planta.
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

from estado_proyecto import EstadoProyecto
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria


# --- Propiedades del agua según temperatura (tabla estándar de hidráulica) ---
# T(°C): (viscosidad dinámica μ en mPa·s, densidad ρ en kg/m³)
PROPIEDADES_AGUA = {
    0:  (1.787, 999.8),
    5:  (1.519, 1000.0),
    10: (1.307, 999.7),
    15: (1.139, 999.1),
    20: (1.002, 998.2),
    25: (0.890, 997.0),
    30: (0.798, 995.6),
}

G = 9.81  # m/s2
PESO_ESPECIFICO_ARENA_NORMATIVO = 2.65   # g/cm3 (Art. 55)
D_PARTICULA_NORMATIVO_MM = 0.1           # mm (Art. 55)
VH_MAXIMO_NORMATIVO = 0.25               # m/s (Art. 55)
RELACION_VH_VS_MAXIMA = 20               # adimensional (Art. 55)
T_RETENCION_MINIMO_MIN = 20              # minutos (Art. 55)
PENDIENTE_MINIMA_EVACUACION = 10         # % (Art. 55)
RELACION_B_H_DEFECTO = 1.5               # relación constructiva típica


def propiedades_agua(temperatura_c):
    """Interpola μ (Pa·s) y ρ (kg/m³) del agua para la temperatura dada,
    a partir de la tabla estándar (0-30°C)."""
    temps = sorted(PROPIEDADES_AGUA.keys())
    t = max(temps[0], min(temps[-1], temperatura_c))  # limitar al rango de la tabla

    for i in range(len(temps) - 1):
        t1, t2 = temps[i], temps[i + 1]
        if t1 <= t <= t2:
            mu1, rho1 = PROPIEDADES_AGUA[t1]
            mu2, rho2 = PROPIEDADES_AGUA[t2]
            frac = (t - t1) / (t2 - t1) if t2 != t1 else 0
            mu = mu1 + frac * (mu2 - mu1)
            rho = rho1 + frac * (rho2 - rho1)
            return mu / 1000, rho  # μ en Pa·s

    mu, rho = PROPIEDADES_AGUA[temps[-1]]
    return mu / 1000, rho


class VentanaDesarenador(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Desarenador")
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
            self, "DESARENADOR",
            "Art. 55, Resolución 0330 de 2017 — Diseño por velocidad controlada",
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

        # --- Caudal de diseño y número de unidades ---
        etiqueta(cuerpo, "Caudal de diseño (m³/s):")
        resultado(cuerpo, "lbl_caudal")

        etiqueta(cuerpo, "Número de unidades en paralelo:", editable=True)
        self.entry_num_unidades = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_num_unidades.insert(0, "1")
        self.entry_num_unidades.pack(fill="x")
        nota(cuerpo, "Repartir el caudal en más unidades hace cada canal más angosto/bajo, "
                     "pero NO acorta su longitud (ver nota del serpentín más abajo).")

        etiqueta(cuerpo, "Caudal por unidad (m³/s):")
        resultado(cuerpo, "lbl_caudal_unidad")

        # --- Temperatura del agua ---
        etiqueta(cuerpo, "Temperatura del agua (°C):", editable=True)
        self.entry_temperatura = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_temperatura.insert(0, "20")
        self.entry_temperatura.pack(fill="x")

        etiqueta(cuerpo, "Viscosidad dinámica del agua — μ (Pa·s):")
        resultado(cuerpo, "lbl_viscosidad")

        etiqueta(cuerpo, "Densidad del agua — ρw (kg/m³):")
        resultado(cuerpo, "lbl_densidad")

        # --- Partícula a remover ---
        etiqueta(cuerpo, "Diámetro de partícula a remover (mm):", editable=True)
        self.entry_diametro_particula = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_diametro_particula.insert(0, str(D_PARTICULA_NORMATIVO_MM))
        self.entry_diametro_particula.pack(fill="x")

        etiqueta(cuerpo, "Peso específico de la arena (g/cm³):", editable=True)
        self.entry_peso_especifico = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_peso_especifico.insert(0, str(PESO_ESPECIFICO_ARENA_NORMATIVO))
        self.entry_peso_especifico.pack(fill="x")

        etiqueta(cuerpo, "Velocidad de asentamiento — Vs (Ley de Stokes, m/s):")
        resultado(cuerpo, "lbl_vs")

        etiqueta(cuerpo, "Número de Reynolds de la partícula (verificación de régimen):")
        resultado(cuerpo, "lbl_reynolds")

        # --- Velocidad horizontal ---
        etiqueta(cuerpo, "Velocidad horizontal de diseño — Vh, máx. 0.25 m/s (Art. 55):", editable=True)
        self.entry_vh = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_vh.insert(0, "0.15")
        self.entry_vh.pack(fill="x")

        etiqueta(cuerpo, "Vh máximo recomendado (según Vs y la relación Vh/Vs ≤ 20):")
        resultado(cuerpo, "lbl_vh_max_recomendado")

        etiqueta(cuerpo, "Relación Vh / Vs (máx. 20, Art. 55):")
        resultado(cuerpo, "lbl_relacion_vh_vs")

        # --- Tiempo de retención de diseño ---
        etiqueta(cuerpo, "Tiempo de retención de diseño, mín. 20 min (Art. 55):", editable=True)
        self.entry_t_retencion = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_t_retencion.insert(0, str(T_RETENCION_MINIMO_MIN))
        self.entry_t_retencion.pack(fill="x")
        nota(cuerpo, "La longitud se calcula como L = Vh · t, así el tiempo de retención "
                     "queda garantizado por construcción, no como resultado.")

        etiqueta(cuerpo, "Longitud desarrollada total del canal — L = Vh · t (m):")
        resultado(cuerpo, "lbl_longitud")

        # --- Relación B/H ---
        etiqueta(cuerpo, "Relación constructiva Ancho/Profundidad — B/H:", editable=True)
        self.entry_relacion_bh = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_relacion_bh.insert(0, str(RELACION_B_H_DEFECTO))
        self.entry_relacion_bh.pack(fill="x")

        etiqueta(cuerpo, "Área transversal — Ac = Q / Vh (m²):")
        resultado(cuerpo, "lbl_area_transversal")

        etiqueta(cuerpo, "Ancho — B (m):")
        resultado(cuerpo, "lbl_ancho")

        etiqueta(cuerpo, "Profundidad — H (m):")
        resultado(cuerpo, "lbl_profundidad")

        # --- Verificación de asentamiento (no dimensionamiento) ---
        etiqueta(cuerpo, "Área de referencia — As = Q/Vs (informativa, sedimentador ideal):")
        resultado(cuerpo, "lbl_area_referencia")

        etiqueta(cuerpo, "Vs requerida para que la partícula asiente — H/t (verificación):")
        resultado(cuerpo, "lbl_vs_requerida")

        # --- Serpentín ---
        etiqueta(cuerpo, "Número de tramos en serpentín (plegado del canal):", editable=True)
        self.entry_num_tramos = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_num_tramos.insert(0, "1")
        self.entry_num_tramos.pack(fill="x")
        nota(cuerpo, "Plegar el canal no cambia el volumen, la velocidad ni el tiempo de "
                     "retención; solo empaqueta la misma longitud L en menos espacio en planta "
                     "(el agua recorre los tramos en serie, uno tras otro).")

        etiqueta(cuerpo, "Longitud por tramo (m):")
        resultado(cuerpo, "lbl_longitud_tramo")

        etiqueta(cuerpo, "Ancho total de la estructura (todos los tramos, sin muros) (m):")
        resultado(cuerpo, "lbl_ancho_total")

        # --- Pendiente de evacuación de lodos ---
        etiqueta(cuerpo, "Pendiente del sistema de evacuación de arenas, mín. 10% (Art. 55):", editable=True)
        self.entry_pendiente = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_pendiente.insert(0, "12")
        self.entry_pendiente.pack(fill="x")

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
            marco_final, text="✅ DIMENSIONES DEL DESARENADOR (por unidad, por tramo)",
            font=fuente(11, "bold"), bg=C.EXITO_FONDO, fg=C.EXITO,
        ).pack(pady=(10, 4))
        self.lbl_dimensiones_final = tk.Label(
            marco_final, text="L: — m   ×   B: — m   ×   H: — m",
            font=fuente(15, "bold"), bg=C.EXITO_FONDO, fg=C.EXITO,
        )
        self.lbl_dimensiones_final.pack(pady=(0, 4))
        self.lbl_estructura_final = tk.Label(
            marco_final, text="", font=fuente(9, "bold"),
            bg=C.EXITO_FONDO, fg=C.EXITO, justify="center", wraplength=tema.ANCHO_TEXTO_LATERAL,
        )
        self.lbl_estructura_final.pack(pady=(0, 4))
        self.lbl_cumple_final = tk.Label(
            marco_final, text="", font=fuente(9, "bold"),
            bg=C.EXITO_FONDO, fg=C.EXITO, justify="center",
        )
        self.lbl_cumple_final.pack(pady=(0, 10))

        tk.Button(
            lateral, text="💾 Guardar y continuar", font=fuente(12, "bold"),
            bg=C.EXITO_BOTON, fg="white", cursor="hand2", command=self.guardar,
        ).pack(fill="x", ipady=8, pady=(0, 20))

        for entry in (
            self.entry_num_unidades, self.entry_temperatura, self.entry_diametro_particula,
            self.entry_peso_especifico, self.entry_vh, self.entry_t_retencion,
            self.entry_relacion_bh, self.entry_num_tramos, self.entry_pendiente,
        ):
            entry.bind("<FocusOut>", lambda e: self.calcular())

        # Forzar redibujo y dejar el scroll arriba del todo.
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
        self.calcular(silencioso=True)

    # ------------------------------------------------------------------
    def calcular(self, silencioso=False):
        try:
            q_total = EstadoProyecto.caudal_diseño_m3s
            num_unidades = int(self.entry_num_unidades.get())
            temperatura = float(self.entry_temperatura.get())
            d_particula_mm = float(self.entry_diametro_particula.get())
            peso_especifico = float(self.entry_peso_especifico.get())
            vh = float(self.entry_vh.get())
            t_retencion_min = float(self.entry_t_retencion.get())
            relacion_bh = float(self.entry_relacion_bh.get())
            num_tramos = int(self.entry_num_tramos.get())
            pendiente = float(self.entry_pendiente.get())

            if num_unidades < 1:
                raise ValueError("El número de unidades debe ser al menos 1.")
            if d_particula_mm <= 0:
                raise ValueError("El diámetro de partícula debe ser mayor que 0.")
            if vh <= 0:
                raise ValueError("La velocidad horizontal debe ser mayor que 0.")
            if t_retencion_min < T_RETENCION_MINIMO_MIN:
                raise ValueError(
                    f"El tiempo de retención de diseño no puede ser menor al mínimo "
                    f"normativo ({T_RETENCION_MINIMO_MIN} min, Art. 55)."
                )
            if relacion_bh <= 0:
                raise ValueError("La relación B/H debe ser mayor que 0.")
            if num_tramos < 1:
                raise ValueError("El número de tramos debe ser al menos 1.")

        except (ValueError, TypeError) as e:
            if not silencioso:
                messagebox.showwarning("Datos inválidos", f"Revise los valores ingresados.\n{e}")
            return

        q_unidad = q_total / num_unidades

        mu, rho_agua = propiedades_agua(temperatura)
        rho_particula = peso_especifico * 1000  # g/cm3 -> kg/m3
        d_particula_m = d_particula_mm / 1000

        # Ley de Stokes: Vs = g·(ρs - ρw)·d² / (18·μ)
        vs = G * (rho_particula - rho_agua) * d_particula_m ** 2 / (18 * mu)

        nu = mu / rho_agua  # viscosidad cinemática, m2/s
        reynolds = vs * d_particula_m / nu if nu > 0 else 0

        relacion_vh_vs = vh / vs if vs > 0 else float("inf")
        vh_max_recomendado = min(VH_MAXIMO_NORMATIVO, RELACION_VH_VS_MAXIMA * vs) if vs > 0 else VH_MAXIMO_NORMATIVO

        t_retencion_s = t_retencion_min * 60

        # --- Dimensionamiento por velocidad controlada ---
        # OJO: L depende solo de Vh y t (no de q_unidad ni num_unidades).
        longitud = vh * t_retencion_s                    # L = Vh · t
        area_transversal = q_unidad / vh                  # Ac = Q / Vh (continuidad, sí depende de q_unidad)
        profundidad = math.sqrt(area_transversal / relacion_bh)
        ancho = relacion_bh * profundidad

        # --- Verificación (no dimensionamiento) ---
        area_referencia_ideal = q_unidad / vs if vs > 0 else float("inf")  # solo informativa
        vs_requerida = profundidad / t_retencion_s if t_retencion_s > 0 else float("inf")
        cumple_asentamiento = vs >= vs_requerida

        # --- Serpentín (tramos en serie): pliega la misma L en menos espacio ---
        longitud_por_tramo = longitud / num_tramos
        ancho_total_estructura = ancho * num_tramos

        cumple_vh = vh <= VH_MAXIMO_NORMATIVO
        cumple_relacion = relacion_vh_vs <= RELACION_VH_VS_MAXIMA
        cumple_pendiente = pendiente > PENDIENTE_MINIMA_EVACUACION
        cumple_todo = cumple_vh and cumple_relacion and cumple_asentamiento and cumple_pendiente

        if not cumple_todo and not silencioso:
            problemas = []
            if not cumple_vh:
                problemas.append(f"• Vh = {vh:.3f} m/s debe ser menor o igual a {VH_MAXIMO_NORMATIVO} m/s.")
            if not cumple_relacion:
                problemas.append(
                    f"• Vh/Vs = {relacion_vh_vs:.1f} debe ser menor o igual a {RELACION_VH_VS_MAXIMA} "
                    f"(pruebe con Vh ≤ {vh_max_recomendado:.3f} m/s)."
                )
            if not cumple_asentamiento:
                problemas.append(
                    f"• La partícula no alcanza a asentar: Vs = {vs:.5f} m/s < Vs requerida = "
                    f"{vs_requerida:.5f} m/s. Aumente el tiempo de retención o reduzca H "
                    f"(baje la relación B/H)."
                )
            if not cumple_pendiente:
                problemas.append(f"• Pendiente = {pendiente:.1f}% debe ser mayor a {PENDIENTE_MINIMA_EVACUACION}%.")
            messagebox.showwarning(
                "Requisitos del Art. 55 no cumplidos",
                "Ajuste el diseño:\n\n" + "\n".join(problemas),
            )

        self._resultado = dict(
            q_total=q_total, num_unidades=num_unidades, q_unidad=q_unidad,
            temperatura=temperatura, mu=mu, rho_agua=rho_agua,
            d_particula_mm=d_particula_mm, peso_especifico=peso_especifico,
            vs=vs, reynolds=reynolds, vh=vh, vh_max_recomendado=vh_max_recomendado,
            relacion_vh_vs=relacion_vh_vs, t_retencion_min=t_retencion_min,
            longitud=longitud, relacion_bh=relacion_bh, area_transversal=area_transversal,
            ancho=ancho, profundidad=profundidad, area_referencia_ideal=area_referencia_ideal,
            vs_requerida=vs_requerida, cumple_asentamiento=cumple_asentamiento,
            num_tramos=num_tramos, longitud_por_tramo=longitud_por_tramo,
            ancho_total_estructura=ancho_total_estructura,
            pendiente=pendiente, cumple_todo=cumple_todo,
        )

        self.lbl_caudal_unidad.config(text=f"{q_unidad:,.5f}")
        self.lbl_viscosidad.config(text=f"{mu:,.6f}")
        self.lbl_densidad.config(text=f"{rho_agua:,.1f}")
        self.lbl_vs.config(text=f"{vs:,.5f}")
        self.lbl_reynolds.config(
            text=f"{reynolds:,.3f}   {'✔ laminar (Re<1)' if reynolds < 1 else '⚠ fuera de régimen laminar'}"
        )
        self.lbl_vh_max_recomendado.config(text=f"{vh_max_recomendado:,.3f} m/s")
        self.lbl_relacion_vh_vs.config(
            text=f"{relacion_vh_vs:,.1f}   {'✔ cumple' if cumple_relacion else '⚠ no cumple'}"
        )
        self.lbl_longitud.config(text=f"{longitud:,.2f}")
        self.lbl_area_transversal.config(text=f"{area_transversal:,.4f}")
        self.lbl_ancho.config(text=f"{ancho:,.3f}")
        self.lbl_profundidad.config(text=f"{profundidad:,.3f}")
        self.lbl_area_referencia.config(text=f"{area_referencia_ideal:,.3f}  (no se usa para dimensionar)")
        self.lbl_vs_requerida.config(
            text=f"{vs_requerida:,.5f} m/s   {'✔ Vs real es mayor, sí asienta' if cumple_asentamiento else '⚠ Vs real es menor, NO asienta'}"
        )
        self.lbl_longitud_tramo.config(text=f"{longitud_por_tramo:,.2f}")
        self.lbl_ancho_total.config(text=f"{ancho_total_estructura:,.3f}")

        self.lbl_dimensiones_final.config(
            text=f"L: {longitud_por_tramo:,.2f} m   ×   B: {ancho:,.2f} m   ×   H: {profundidad:,.2f} m"
        )
        if num_tramos > 1:
            self.lbl_estructura_final.config(
                text=f"Serpentín de {num_tramos} tramos en serie — ancho total de la "
                     f"estructura: {ancho_total_estructura:,.2f} m "
                     f"(longitud desarrollada total: {longitud:,.1f} m)"
            )
        else:
            self.lbl_estructura_final.config(text="")
        self.lbl_cumple_final.config(
            text=(
                f"{num_unidades} unidad(es) en paralelo — t. retención de diseño: "
                f"{t_retencion_min:,.0f} min — "
                f"{'✔ cumple el Art. 55' if cumple_todo else '⚠ revise los parámetros marcados arriba'}"
            )
        )

    # ------------------------------------------------------------------
    def guardar(self):
        if not hasattr(self, "_resultado"):
            messagebox.showwarning("Falta calcular", "Primero presione Calcular.")
            return

        r = self._resultado
        EstadoProyecto.desarenador_num_unidades = r["num_unidades"]
        EstadoProyecto.desarenador_q_unidad = r["q_unidad"]
        EstadoProyecto.desarenador_temperatura = r["temperatura"]
        EstadoProyecto.desarenador_viscosidad = r["mu"]
        EstadoProyecto.desarenador_densidad_agua = r["rho_agua"]
        EstadoProyecto.desarenador_d_particula_mm = r["d_particula_mm"]
        EstadoProyecto.desarenador_peso_especifico = r["peso_especifico"]
        EstadoProyecto.desarenador_vs = r["vs"]
        EstadoProyecto.desarenador_reynolds = r["reynolds"]
        EstadoProyecto.desarenador_vh = r["vh"]
        EstadoProyecto.desarenador_relacion_vh_vs = r["relacion_vh_vs"]
        EstadoProyecto.desarenador_ancho = r["ancho"]
        EstadoProyecto.desarenador_area_superficial = r["area_referencia_ideal"]
        EstadoProyecto.desarenador_longitud = r["longitud_por_tramo"]
        EstadoProyecto.desarenador_profundidad = r["profundidad"]
        EstadoProyecto.desarenador_t_retencion_min = r["t_retencion_min"]
        EstadoProyecto.desarenador_pendiente = r["pendiente"]
        EstadoProyecto.desarenador_relacion_bh = r["relacion_bh"]
        EstadoProyecto.desarenador_vs_requerida = r["vs_requerida"]
        EstadoProyecto.desarenador_cumple_asentamiento = r["cumple_asentamiento"]
        EstadoProyecto.desarenador_num_tramos = r["num_tramos"]
        EstadoProyecto.desarenador_longitud_total = r["longitud"]
        EstadoProyecto.desarenador_ancho_total_estructura = r["ancho_total_estructura"]

        messagebox.showinfo(
            "Guardado",
            "Desarenador guardado correctamente.\n\n" + EstadoProyecto.resumen_desarenador(),
        )

        if self.al_guardar:
            self.al_guardar()

        self.destroy()
