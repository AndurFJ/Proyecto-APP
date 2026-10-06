"""
Ventana de Mezcla Rápida / Coagulación — Canaleta Parshall.

Siguiente proceso de diseño de la PTAP (después del desarenador): el
coagulante se aplica en el resalto hidráulico de una canaleta Parshall,
que además sirve como medidor de caudal de la planta.

Requisitos de la Resolución 0330 de 2017 (mod. Res. 799 de 2021) y del
RAS para mezcla rápida (ver constantes más abajo):

- Gradiente medio de velocidad (G) entre 1000 y 2000 s⁻¹.
- En mezcladores hidráulicos el tiempo de mezcla es muy corto (menor
  a 1 s); se reporta como verificación.
- Número de Froude del resalto entre 1.7 y 2.5 (resalto débil) o entre
  4.5 y 9.0 (resalto estable). Debe evitarse el rango 2.5 - 4.5
  (resalto oscilante), que genera ondas y una mezcla irregular.
- Relación Ha/W entre 0.4 y 0.8 (recomendación de diseño, para que la
  canaleta trabaje en la zona de buena precisión y forme el resalto).

MÉTODO DE DISEÑO (Romero Rojas / Arboleda, ACODAL):

    Ha  = (Q / K)^(1/n)                 lámina en la sección de medición
    D'  = 2/3·(D − W) + W               ancho en la sección de medición
    Vo  = Q / (D'·Ha)
    Eo  = Vo²/2g + Ha + N               energía específica
    V1³ − 2g·Eo·V1 + 2g·Q/W = 0         velocidad en la garganta (raíz
                                         supercrítica, solución trigonométrica)
    h1  = Q / (V1·W)        F1 = V1 / √(g·h1)
    h2  = h1/2·(√(1 + 8F1²) − 1)        altura conjugada del resalto
    hp  = (h2 − h1)³ / (4·h1·h2)        pérdida de energía en el resalto
    V2  = Q / (W·h2)
    h3  = h2 − (N − K)       V3 = Q / (C·h3)
    t   = 2·G / (V2 + V3)               tiempo de mezcla (G = long. divergente)
    Gv  = √(γ·hp / (μ·t))               gradiente de velocidad
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

from estado_proyecto import EstadoProyecto
from ui_utils import ajustar_geometria
from ventana_desarenador import propiedades_agua


G_GRAV = 9.81  # m/s2

GRADIENTE_MIN = 1000      # s-1
GRADIENTE_MAX = 2000      # s-1
T_MEZCLA_MAX_HIDRAULICO = 1.0   # s (referencia para mezcladores hidráulicos)
FROUDE_RANGOS_ACEPTABLES = [(1.7, 2.5), (4.5, 9.0)]
RELACION_HA_W_MIN = 0.4
RELACION_HA_W_MAX = 0.8


# --- Canaletas Parshall normalizadas ---
# Ancho de garganta: (W cm, K, n, Qmín L/s, Qmáx L/s,
#                    A, B, C, D, E, F, G, K', N  en cm)
# Q (m³/s) = K · Ha(m)^n. Dimensiones según Azevedo Netto / Romero Rojas.
CANALETAS_PARSHALL = {
    '1"':  (2.5,  0.0604, 1.55,  0.28,    5.67,  36.3,  35.6,   9.3,  16.8, 22.9,  7.6, 20.3, 1.9,  2.9),
    '2"':  (5.1,  0.1207, 1.55,  0.57,   14.15,  41.4,  40.6,  13.5,  21.4, 25.4, 11.4, 25.4, 2.2,  4.3),
    '3"':  (7.6,  0.176,  1.547, 0.85,   53.8,   46.6,  45.7,  17.8,  25.9, 38.1, 15.2, 30.5, 2.5,  5.7),
    '6"':  (15.2, 0.381,  1.580, 1.42,  110.4,   62.1,  61.0,  39.4,  40.3, 45.7, 30.5, 61.0, 7.6, 11.4),
    '9"':  (22.9, 0.535,  1.530, 2.58,  251.9,   88.0,  86.4,  38.0,  57.5, 61.0, 30.5, 45.7, 7.6, 11.4),
    "1'":  (30.5, 0.690,  1.522, 3.11,  455.6,  137.2, 134.4,  61.0,  84.5, 91.5, 61.0, 91.5, 7.6, 22.9),
    "1.5'": (45.7, 1.054, 1.538, 4.25,  696.2,  144.9, 142.0,  76.2, 102.6, 91.5, 61.0, 91.5, 7.6, 22.9),
    "2'":  (61.0, 1.426,  1.550, 11.89,  936.7, 152.5, 149.6,  91.5, 120.7, 91.5, 61.0, 91.5, 7.6, 22.9),
    "3'":  (91.5, 2.182,  1.566, 17.26, 1426.3, 167.7, 164.5, 122.0, 157.2, 91.5, 61.0, 91.5, 7.6, 22.9),
    "4'":  (122.0, 2.935, 1.578, 36.79, 1921.5, 183.0, 179.5, 152.5, 193.8, 91.5, 61.0, 91.5, 7.6, 22.9),
    "5'":  (152.5, 3.728, 1.587, 62.8,  2422.0, 198.3, 194.1, 183.0, 230.3, 91.5, 61.0, 91.5, 7.6, 22.9),
    "6'":  (183.0, 4.515, 1.595, 74.4,  2929.0, 213.5, 209.0, 213.5, 266.7, 91.5, 61.0, 91.5, 7.6, 22.9),
    "7'":  (213.5, 5.306, 1.601, 115.4, 3440.0, 228.8, 224.0, 244.0, 303.0, 91.5, 61.0, 91.5, 7.6, 22.9),
    "8'":  (244.0, 6.101, 1.606, 130.7, 3950.0, 244.0, 239.2, 274.5, 340.0, 91.5, 61.0, 91.5, 7.6, 22.9),
}


def froude_aceptable(froude):
    return any(lo <= froude <= hi for lo, hi in FROUDE_RANGOS_ACEPTABLES)


def calcular_parshall(q_m3s, ancho_garganta, temperatura_c):
    """
    Calcula la canaleta Parshall de ancho `ancho_garganta` (clave de
    CANALETAS_PARSHALL) para el caudal `q_m3s`. Retorna un dict con
    todos los resultados intermedios y las verificaciones.
    Lanza ValueError si el resalto no tiene solución física.
    """
    (w_cm, k, n, qmin_ls, qmax_ls, a_cm, b_cm, c_cm, d_cm, e_cm,
     f_cm, g_cm, kp_cm, n_cm) = CANALETAS_PARSHALL[ancho_garganta]
    w, c, d, g_long = w_cm / 100, c_cm / 100, d_cm / 100, g_cm / 100
    k_caida, n_caida = kp_cm / 100, n_cm / 100

    mu, rho = propiedades_agua(temperatura_c)
    gamma = rho * G_GRAV  # N/m3

    ha = (q_m3s / k) ** (1 / n)
    d_prima = 2 / 3 * (d - w) + w
    vo = q_m3s / (d_prima * ha)
    eo = vo ** 2 / (2 * G_GRAV) + ha + n_caida

    # V1³ − 2g·Eo·V1 + 2g·Q/W = 0  →  raíz supercrítica (la mayor positiva)
    cos_theta = -(G_GRAV * q_m3s / w) / (2 * G_GRAV * eo / 3) ** 1.5
    if cos_theta < -1:
        raise ValueError(
            f"La canaleta de {ancho_garganta} no admite este caudal "
            f"(no se forma el resalto). Pruebe con un ancho mayor."
        )
    theta = math.acos(cos_theta)
    v1 = 2 * math.sqrt(2 * G_GRAV * eo / 3) * math.cos(theta / 3)

    h1 = q_m3s / (v1 * w)
    froude = v1 / math.sqrt(G_GRAV * h1)
    h2 = h1 / 2 * (math.sqrt(1 + 8 * froude ** 2) - 1)
    hp = (h2 - h1) ** 3 / (4 * h1 * h2)
    v2 = q_m3s / (w * h2)
    h3 = h2 - (n_caida - k_caida)
    if h3 <= 0:
        raise ValueError(
            f"Con la canaleta de {ancho_garganta} la lámina a la salida queda en "
            f"{h3:.3f} m (sin agua sobre la cresta). Pruebe con un ancho menor."
        )
    v3 = q_m3s / (c * h3)
    t_mezcla = 2 * g_long / (v2 + v3)
    gradiente = math.sqrt(gamma * hp / (mu * t_mezcla))

    q_ls = q_m3s * 1000
    cumple_rango_q = qmin_ls <= q_ls <= qmax_ls
    cumple_froude = froude_aceptable(froude)
    cumple_gradiente = GRADIENTE_MIN <= gradiente <= GRADIENTE_MAX
    cumple_tiempo = t_mezcla <= T_MEZCLA_MAX_HIDRAULICO
    relacion_ha_w = ha / w
    cumple_ha_w = RELACION_HA_W_MIN <= relacion_ha_w <= RELACION_HA_W_MAX

    return dict(
        ancho_garganta=ancho_garganta, w=w, k=k, n=n, qmin_ls=qmin_ls, qmax_ls=qmax_ls,
        dimensiones_cm=dict(A=a_cm, B=b_cm, C=c_cm, D=d_cm, E=e_cm, F=f_cm,
                            G=g_cm, K=kp_cm, N=n_cm),
        temperatura=temperatura_c, mu=mu, rho=rho,
        ha=ha, d_prima=d_prima, vo=vo, eo=eo, v1=v1, h1=h1, froude=froude,
        h2=h2, hp=hp, v2=v2, h3=h3, v3=v3, t_mezcla=t_mezcla, gradiente=gradiente,
        cumple_rango_q=cumple_rango_q, cumple_froude=cumple_froude,
        cumple_gradiente=cumple_gradiente, cumple_tiempo=cumple_tiempo,
        relacion_ha_w=relacion_ha_w, cumple_ha_w=cumple_ha_w,
        cumple_todo=cumple_rango_q and cumple_froude and cumple_gradiente and cumple_ha_w,
    )


def sugerir_ancho_garganta(q_m3s, temperatura_c):
    """Entre las canaletas cuyo rango de caudal admite Q, retorna la que
    cumple más requisitos (Froude, gradiente, Ha/W); a igualdad, la más
    pequeña. Si ninguna admite Q, retorna la primera de la lista."""
    mejor, mejor_puntaje = None, -1
    for ancho in CANALETAS_PARSHALL:
        try:
            r = calcular_parshall(q_m3s, ancho, temperatura_c)
        except (ValueError, ZeroDivisionError):
            continue
        if not r["cumple_rango_q"]:
            continue
        puntaje = r["cumple_froude"] + r["cumple_gradiente"] + r["cumple_ha_w"]
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = ancho, puntaje
    return mejor or next(iter(CANALETAS_PARSHALL))


class VentanaMezclaRapida(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Mezcla rápida — Canaleta Parshall")
        self.resizable(False, True)
        ajustar_geometria(self, ancho=640, alto=880)
        self.configure(bg="#F2F4F4")

        self.al_guardar = al_guardar

        self._crear_estilos()
        self._crear_widgets()
        self._precargar()

    # ------------------------------------------------------------------
    def _crear_estilos(self):
        estilo = ttk.Style(self)
        color_editable = "#FEF9E7"
        borde_editable = "#F1C40F"
        estilo.configure(
            "Editable.TEntry", fieldbackground=color_editable,
            bordercolor=borde_editable, lightcolor=borde_editable,
        )
        estilo.configure("Editable.TCombobox", fieldbackground=color_editable)
        estilo.map(
            "Editable.TCombobox",
            fieldbackground=[("readonly", color_editable)],
        )

    # ------------------------------------------------------------------
    def _crear_widgets(self):
        titulo = tk.Label(
            self, text="MEZCLA RÁPIDA — CANALETA PARSHALL",
            font=("Arial", 14, "bold"), bg="#1F4E78", fg="white", pady=10,
        )
        titulo.pack(fill="x")

        subtitulo = tk.Label(
            self,
            text="Resolución 0330 de 2017 (mod. Res. 799 de 2021) — "
                 "G entre 1000 y 2000 s⁻¹, resalto hidráulico estable",
            font=("Arial", 8, "italic"), bg="#1F4E78", fg="#D9E1F2", pady=6,
        )
        subtitulo.pack(fill="x")

        contenedor = tk.Frame(self, bg="#F2F4F4")
        contenedor.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(contenedor, bg="#F2F4F4", highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        cuerpo_ext = tk.Frame(self.canvas, bg="#F2F4F4")
        ventana_id = self.canvas.create_window((0, 0), window=cuerpo_ext, anchor="nw")
        cuerpo_ext.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(ventana_id, width=e.width),
        )

        def _rueda(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _rueda)

        cuerpo = tk.Frame(cuerpo_ext, bg="#F2F4F4")
        cuerpo.pack(fill="both", expand=True, padx=20, pady=15)

        def etiqueta(padre, texto, editable=False):
            if editable:
                texto = f"✎ {texto}   (dato editable)"
            tk.Label(
                padre, text=texto, font=("Arial", 10, "bold" if editable else "normal"),
                bg="#F2F4F4", fg="#B9770E" if editable else "black", anchor="w",
            ).pack(fill="x", pady=(8, 2))

        def resultado(padre, nombre_attr, valor_inicial="—"):
            lbl = tk.Label(
                padre, text=valor_inicial, font=("Arial", 11, "bold"),
                bg="white", fg="#1B4F72", anchor="w", relief="solid", bd=1,
            )
            lbl.pack(fill="x", ipady=4)
            setattr(self, nombre_attr, lbl)
            return lbl

        def nota(padre, texto):
            lbl = tk.Label(
                padre, text=texto, font=("Arial", 8, "italic"),
                bg="#F2F4F4", fg="#7B7D7D", anchor="w", justify="left", wraplength=560,
            )
            lbl.pack(fill="x", pady=(0, 2))
            return lbl

        # --- Caudal y temperatura ---
        etiqueta(cuerpo, "Caudal de diseño (m³/s):")
        resultado(cuerpo, "lbl_caudal")

        etiqueta(cuerpo, "Temperatura del agua (°C):", editable=True)
        self.entry_temperatura = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_temperatura.pack(fill="x")

        etiqueta(cuerpo, "Viscosidad dinámica — μ (Pa·s)   /   Peso específico — γ (N/m³):")
        resultado(cuerpo, "lbl_propiedades")

        # --- Selección de la canaleta ---
        etiqueta(cuerpo, "Ancho de garganta de la canaleta — W:", editable=True)
        fila_w = tk.Frame(cuerpo, bg="#F2F4F4")
        fila_w.pack(fill="x")
        self.cb_ancho = ttk.Combobox(
            fila_w, values=list(CANALETAS_PARSHALL.keys()),
            state="readonly", style="Editable.TCombobox",
        )
        self.cb_ancho.pack(side="left", fill="x", expand=True)
        self.cb_ancho.bind("<<ComboboxSelected>>", lambda e: self.calcular())
        tk.Button(
            fila_w, text="Sugerir W", font=("Arial", 9, "bold"),
            bg="#5DADE2", fg="white", cursor="hand2", bd=0,
            command=self.sugerir_ancho,
        ).pack(side="left", padx=(8, 0), ipadx=6)
        nota(cuerpo, "«Sugerir W» elige, entre las canaletas cuyo rango admite el caudal, la que "
                     "cumple más requisitos (Froude, gradiente, Ha/W). Para caudales pequeños "
                     "puede que ninguna los cumpla todos; en ese caso se elige la más cercana.")

        etiqueta(cuerpo, "Rango de caudal de la canaleta (L/s):")
        resultado(cuerpo, "lbl_rango_q")

        etiqueta(cuerpo, "Dimensiones normalizadas (cm):")
        resultado(cuerpo, "lbl_dimensiones")

        # --- Hidráulica ---
        etiqueta(cuerpo, "Lámina en la sección de medición — Ha = (Q/K)^(1/n) (m):")
        resultado(cuerpo, "lbl_ha")

        etiqueta(cuerpo, "Relación Ha / W (recomendado entre 0.4 y 0.8):")
        resultado(cuerpo, "lbl_ha_w")

        etiqueta(cuerpo, "Ancho en la sección de medición — D' (m)   /   Velocidad Vo (m/s):")
        resultado(cuerpo, "lbl_d_vo")

        etiqueta(cuerpo, "Energía específica — Eo = Vo²/2g + Ha + N (m):")
        resultado(cuerpo, "lbl_eo")

        etiqueta(cuerpo, "Velocidad en la garganta — V1 (m/s)   /   Lámina h1 (m):")
        resultado(cuerpo, "lbl_v1_h1")

        etiqueta(cuerpo, "Número de Froude — F1 (1.7-2.5 ó 4.5-9.0):")
        resultado(cuerpo, "lbl_froude")

        etiqueta(cuerpo, "Altura conjugada del resalto — h2 (m)   /   V2 (m/s):")
        resultado(cuerpo, "lbl_h2_v2")

        etiqueta(cuerpo, "Lámina a la salida — h3 (m)   /   V3 (m/s):")
        resultado(cuerpo, "lbl_h3_v3")

        etiqueta(cuerpo, "Pérdida de energía en el resalto — hp (m):")
        resultado(cuerpo, "lbl_hp")

        etiqueta(cuerpo, "Tiempo de mezcla — t = 2G / (V2 + V3) (s):")
        resultado(cuerpo, "lbl_t_mezcla")

        etiqueta(cuerpo, "Gradiente de velocidad — G = √(γ·hp / (μ·t)) (s⁻¹):")
        resultado(cuerpo, "lbl_gradiente")

        # --- Botón calcular ---
        tk.Button(
            cuerpo, text="Calcular", font=("Arial", 11, "bold"),
            bg="#2E86C1", fg="white", cursor="hand2", command=self.calcular,
        ).pack(fill="x", pady=(15, 10), ipady=6)

        # --- Resultado final destacado ---
        marco_final = tk.Frame(
            cuerpo, bg="#EAFAF1", bd=2, relief="solid",
            highlightbackground="#1E8449", highlightthickness=2,
        )
        marco_final.pack(fill="x", pady=(10, 15))
        tk.Label(
            marco_final, text="✅ CANALETA PARSHALL DE MEZCLA RÁPIDA",
            font=("Arial", 11, "bold"), bg="#EAFAF1", fg="#1E8449",
        ).pack(pady=(10, 4))
        self.lbl_resultado_final = tk.Label(
            marco_final, text="W: —   G: — s⁻¹   t: — s",
            font=("Arial", 15, "bold"), bg="#EAFAF1", fg="#1E8449",
        )
        self.lbl_resultado_final.pack(pady=(0, 4))
        self.lbl_cumple_final = tk.Label(
            marco_final, text="", font=("Arial", 9, "bold"),
            bg="#EAFAF1", fg="#1E8449", justify="center", wraplength=560,
        )
        self.lbl_cumple_final.pack(pady=(0, 10))

        tk.Button(
            cuerpo, text="💾 Guardar y continuar", font=("Arial", 12, "bold"),
            bg="#28B463", fg="white", cursor="hand2", command=self.guardar,
        ).pack(fill="x", ipady=8, pady=(0, 20))

        self.entry_temperatura.bind("<FocusOut>", lambda e: self.calcular())

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
            EstadoProyecto.mezcla_temperatura
            or EstadoProyecto.desarenador_temperatura
            or 20
        )
        self.entry_temperatura.insert(0, f"{temperatura:g}")

        if EstadoProyecto.mezcla_ancho_garganta:
            self.cb_ancho.set(EstadoProyecto.mezcla_ancho_garganta)
        else:
            self.cb_ancho.set(sugerir_ancho_garganta(EstadoProyecto.caudal_diseño_m3s, temperatura))
        self.calcular(silencioso=True)

    # ------------------------------------------------------------------
    def sugerir_ancho(self):
        try:
            temperatura = float(self.entry_temperatura.get())
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Revise la temperatura del agua.")
            return
        self.cb_ancho.set(sugerir_ancho_garganta(EstadoProyecto.caudal_diseño_m3s, temperatura))
        self.calcular()

    # ------------------------------------------------------------------
    def calcular(self, silencioso=False):
        try:
            q = EstadoProyecto.caudal_diseño_m3s
            temperatura = float(self.entry_temperatura.get())
            ancho = self.cb_ancho.get()
            if ancho not in CANALETAS_PARSHALL:
                raise ValueError("Seleccione el ancho de garganta de la canaleta.")
            r = calcular_parshall(q, ancho, temperatura)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            if hasattr(self, "_resultado"):
                del self._resultado
            if not silencioso:
                messagebox.showwarning("Datos inválidos", f"Revise los valores ingresados.\n{e}")
            return

        if not r["cumple_todo"] and not silencioso:
            problemas = []
            if not r["cumple_rango_q"]:
                problemas.append(
                    f"• Q = {q * 1000:,.2f} L/s está fuera del rango de la canaleta de {ancho} "
                    f"({r['qmin_ls']:,.2f} - {r['qmax_ls']:,.1f} L/s)."
                )
            if not r["cumple_froude"]:
                problemas.append(
                    f"• F1 = {r['froude']:.2f} debe estar entre 1.7 y 2.5 o entre 4.5 y 9.0 "
                    f"(resalto oscilante o inexistente)."
                )
            if not r["cumple_ha_w"]:
                problemas.append(
                    f"• Ha/W = {r['relacion_ha_w']:.2f} debería estar entre {RELACION_HA_W_MIN} y "
                    f"{RELACION_HA_W_MAX}."
                )
            if not r["cumple_gradiente"]:
                problemas.append(
                    f"• G = {r['gradiente']:,.0f} s⁻¹ debe estar entre {GRADIENTE_MIN} y "
                    f"{GRADIENTE_MAX} s⁻¹."
                )
            messagebox.showwarning(
                "Requisitos de mezcla rápida no cumplidos",
                "Ajuste el diseño (pruebe con «Sugerir W» u otro ancho de garganta):\n\n"
                + "\n".join(problemas),
            )

        self._resultado = r

        dim = r["dimensiones_cm"]
        self.lbl_propiedades.config(text=f"{r['mu']:,.6f}   /   {r['rho'] * G_GRAV:,.0f}")
        self.lbl_rango_q.config(
            text=f"{r['qmin_ls']:,.2f} - {r['qmax_ls']:,.1f}   "
                 f"{'✔ Q dentro del rango' if r['cumple_rango_q'] else '⚠ Q fuera del rango'}"
        )
        self.lbl_dimensiones.config(
            text="  ".join(f"{k}={v:g}" for k, v in dim.items())
        )
        self.lbl_ha.config(text=f"{r['ha']:,.4f}")
        self.lbl_ha_w.config(
            text=f"{r['relacion_ha_w']:,.2f}   {'✔ cumple' if r['cumple_ha_w'] else '⚠ fuera de rango'}"
        )
        self.lbl_d_vo.config(text=f"{r['d_prima']:,.4f}   /   {r['vo']:,.4f}")
        self.lbl_eo.config(text=f"{r['eo']:,.4f}")
        self.lbl_v1_h1.config(text=f"{r['v1']:,.4f}   /   {r['h1']:,.4f}")
        self.lbl_froude.config(
            text=f"{r['froude']:,.2f}   {'✔ resalto estable' if r['cumple_froude'] else '⚠ fuera de rango'}"
        )
        self.lbl_h2_v2.config(text=f"{r['h2']:,.4f}   /   {r['v2']:,.4f}")
        self.lbl_h3_v3.config(text=f"{r['h3']:,.4f}   /   {r['v3']:,.4f}")
        self.lbl_hp.config(text=f"{r['hp']:,.4f}")
        self.lbl_t_mezcla.config(
            text=f"{r['t_mezcla']:,.3f}   "
                 f"{'✔ < 1 s (mezcla instantánea)' if r['cumple_tiempo'] else '⚠ mayor a 1 s'}"
        )
        self.lbl_gradiente.config(
            text=f"{r['gradiente']:,.0f}   {'✔ cumple' if r['cumple_gradiente'] else '⚠ no cumple'}"
        )

        self.lbl_resultado_final.config(
            text=f"W: {ancho} ({r['w'] * 100:g} cm)   G: {r['gradiente']:,.0f} s⁻¹   "
                 f"t: {r['t_mezcla']:,.2f} s"
        )
        self.lbl_cumple_final.config(
            text=(
                f"Ha = {r['ha']:,.3f} m — F1 = {r['froude']:,.2f} — hp = {r['hp']:,.3f} m — "
                f"{'✔ cumple los requisitos de mezcla rápida' if r['cumple_todo'] else '⚠ revise los parámetros marcados arriba'}"
            )
        )

    # ------------------------------------------------------------------
    def guardar(self):
        if not hasattr(self, "_resultado"):
            messagebox.showwarning("Falta calcular", "Primero presione Calcular.")
            return

        r = self._resultado
        EstadoProyecto.mezcla_temperatura = r["temperatura"]
        EstadoProyecto.mezcla_ancho_garganta = r["ancho_garganta"]
        EstadoProyecto.mezcla_w = r["w"]
        EstadoProyecto.mezcla_k = r["k"]
        EstadoProyecto.mezcla_n = r["n"]
        EstadoProyecto.mezcla_dimensiones_cm = r["dimensiones_cm"]
        EstadoProyecto.mezcla_ha = r["ha"]
        EstadoProyecto.mezcla_relacion_ha_w = r["relacion_ha_w"]
        EstadoProyecto.mezcla_d_prima = r["d_prima"]
        EstadoProyecto.mezcla_vo = r["vo"]
        EstadoProyecto.mezcla_eo = r["eo"]
        EstadoProyecto.mezcla_v1 = r["v1"]
        EstadoProyecto.mezcla_h1 = r["h1"]
        EstadoProyecto.mezcla_froude = r["froude"]
        EstadoProyecto.mezcla_h2 = r["h2"]
        EstadoProyecto.mezcla_v2 = r["v2"]
        EstadoProyecto.mezcla_h3 = r["h3"]
        EstadoProyecto.mezcla_v3 = r["v3"]
        EstadoProyecto.mezcla_perdida = r["hp"]
        EstadoProyecto.mezcla_tiempo = r["t_mezcla"]
        EstadoProyecto.mezcla_gradiente = r["gradiente"]
        EstadoProyecto.mezcla_cumple = r["cumple_todo"]

        messagebox.showinfo(
            "Guardado",
            "Mezcla rápida guardada correctamente.\n\n" + EstadoProyecto.resumen_mezcla_rapida(),
        )

        if self.al_guardar:
            self.al_guardar()

        self.destroy()
