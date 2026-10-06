"""
Ventana de Aducción / Conducción.

Proceso de diseño de la PTAP (después del desarenador): a partir del caudal de diseño
(Paso 2) y de un diámetro comercial elegido por el usuario, calcula
el área, la velocidad resultante y la pérdida de carga (fórmula de
Hazen-Williams) de la línea de aducción o conducción — siguiendo los
requisitos del Art. 56 de la Resolución 0330 de 2017 (modificado por
la Res. 799 de 2021):

- Velocidad mínima: 0.5 m/s (o el esfuerzo cortante mínimo de 1.5 Pa,
  que no se evalúa aquí — se usa el límite de velocidad).
- Velocidad máxima: la recomendada para el material/accesorios (dato
  editable, la resolución no fija un valor único).
- Factor de seguridad por golpe de ariete: 1.3 para sistemas por
  bombeo, 1.1 para sistemas por gravedad.
- La elección final del diámetro debe basarse en un estudio técnico-
  económico comparando varios diámetros comerciales (Art. 56); esta
  ventana ayuda a evaluar cada diámetro candidato, pero la decisión
  final de cuál adoptar es del diseñador.
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

from estado_proyecto import EstadoProyecto
import tema
from tema import C, fuente
from ui_utils import ajustar_geometria


# --- Coeficiente de rugosidad de Hazen-Williams según el material ---
COEFICIENTES_C_HAZEN_WILLIAMS = {
    "PVC / Polietileno (PEAD)": 150,
    "Fibra de vidrio (GRP)": 150,
    "Asbesto-cemento": 140,
    "Hierro fundido dúctil (nuevo)": 130,
    "Concreto": 130,
    "Acero (nuevo)": 120,
    "Hierro fundido (usado)": 100,
    "Acero (usado)": 100,
}

# --- Diámetros comerciales típicos disponibles (mm) ---
DIAMETROS_COMERCIALES_MM = [
    50, 63, 75, 90, 110, 140, 160, 200, 250, 315, 355, 400, 450, 500, 630,
]

# Velocidad mínima normativa (Art. 56, Res. 0330 de 2017)
V_MIN_NORMATIVA = 0.5


class VentanaAduccionConduccion(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Aducción / Conducción")
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
            self, "ADUCCIÓN / CONDUCCIÓN",
            "Art. 56, Resolución 0330 de 2017 (modificado por Res. 799 de 2021)",
        )

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

        # --- Caudal de diseño ---
        etiqueta(cuerpo, "Caudal de diseño (m³/s):")
        resultado(cuerpo, "lbl_caudal")

        # --- Tipo de sistema (gravedad / bombeo) ---
        etiqueta(cuerpo, "Tipo de sistema:", editable=True)
        self.cb_sistema = ttk.Combobox(
            cuerpo, values=["Por gravedad", "Por bombeo"],
            state="readonly", style="Editable.TCombobox",
        )
        self.cb_sistema.set("Por gravedad")
        self.cb_sistema.pack(fill="x")
        self.cb_sistema.bind("<<ComboboxSelected>>", lambda e: self.calcular())

        etiqueta(cuerpo, "Factor de seguridad por golpe de ariete (Art. 56):")
        resultado(cuerpo, "lbl_factor_ariete")

        # --- Material de la tubería ---
        etiqueta(cuerpo, "Material de la tubería:", editable=True)
        self.cb_material = ttk.Combobox(
            cuerpo, values=list(COEFICIENTES_C_HAZEN_WILLIAMS.keys()),
            state="readonly", style="Editable.TCombobox",
        )
        self.cb_material.set("PVC / Polietileno (PEAD)")
        self.cb_material.pack(fill="x")
        self.cb_material.bind("<<ComboboxSelected>>", lambda e: self.calcular())

        etiqueta(cuerpo, "Coeficiente de rugosidad — C (Hazen-Williams):")
        resultado(cuerpo, "lbl_c_hw")

        # --- Longitud de la línea ---
        etiqueta(cuerpo, "Longitud de la línea (m):", editable=True)
        self.entry_longitud = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_longitud.insert(0, "500")
        self.entry_longitud.pack(fill="x")

        # --- Velocidades límite ---
        etiqueta(cuerpo, "Velocidad mínima normativa — Art. 56 (m/s):")
        resultado(cuerpo, "lbl_vmin")

        etiqueta(cuerpo, "Velocidad máxima admisible según el material (m/s):", editable=True)
        self.entry_vmax = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_vmax.insert(0, "5.0")
        self.entry_vmax.pack(fill="x")

        # --- Diámetro comercial a evaluar ---
        etiqueta(cuerpo, "Diámetro comercial a evaluar (mm):", editable=True)
        self.cb_diametro = ttk.Combobox(
            cuerpo, values=[str(d) for d in DIAMETROS_COMERCIALES_MM],
            state="readonly", style="Editable.TCombobox",
        )
        self.cb_diametro.set("160")
        self.cb_diametro.pack(fill="x")
        self.cb_diametro.bind("<<ComboboxSelected>>", lambda e: self.calcular())

        etiqueta(cuerpo, "Área de la tubería (m²):")
        resultado(cuerpo, "lbl_area")

        etiqueta(cuerpo, "Velocidad resultante (m/s):")
        resultado(cuerpo, "lbl_velocidad")

        etiqueta(cuerpo, "Pérdida de carga — Hazen-Williams (m):")
        resultado(cuerpo, "lbl_perdida")

        # --- Desnivel disponible (opcional, útil para sistemas por gravedad) ---
        etiqueta(cuerpo, "Desnivel / cabeza disponible entre extremos (m) — opcional:", editable=True)
        self.entry_desnivel = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_desnivel.pack(fill="x")

        etiqueta(cuerpo, "Presión / cabeza residual disponible (m):")
        resultado(cuerpo, "lbl_presion_residual")

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
            marco_final, text="✅ DIÁMETRO ADOPTADO", font=fuente(11, "bold"),
            bg=C.EXITO_FONDO, fg=C.EXITO,
        ).pack(pady=(10, 4))
        self.lbl_diametro_final = tk.Label(
            marco_final, text="— mm", font=fuente(18, "bold"),
            bg=C.EXITO_FONDO, fg=C.EXITO,
        )
        self.lbl_diametro_final.pack(pady=(0, 4))
        self.lbl_cumple_velocidad = tk.Label(
            marco_final, text="", font=fuente(10, "bold"),
            bg=C.EXITO_FONDO, fg=C.EXITO,
        )
        self.lbl_cumple_velocidad.pack(pady=(0, 10))

        tk.Button(
            lateral, text="💾 Guardar y continuar", font=fuente(12, "bold"),
            bg=C.EXITO_BOTON, fg="white", cursor="hand2", command=self.guardar,
        ).pack(fill="x", ipady=8, pady=(0, 20))

        for entry in (self.entry_longitud, self.entry_vmax, self.entry_desnivel):
            entry.bind("<FocusOut>", lambda e: self.calcular())

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
        self.lbl_vmin.config(text=f"{V_MIN_NORMATIVA:,.2f}")
        self.calcular(silencioso=True)

    # ------------------------------------------------------------------
    def calcular(self, silencioso=False):
        try:
            q = EstadoProyecto.caudal_diseño_m3s
            tipo_sistema = self.cb_sistema.get()
            material = self.cb_material.get()
            c_hw = COEFICIENTES_C_HAZEN_WILLIAMS[material]
            v_max = float(self.entry_vmax.get())
            longitud = float(self.entry_longitud.get())
            diam_mm = float(self.cb_diametro.get())

            texto_desnivel = self.entry_desnivel.get().strip()
            desnivel = float(texto_desnivel) if texto_desnivel else None

            if longitud <= 0:
                raise ValueError("La longitud debe ser mayor que 0.")
            if v_max <= V_MIN_NORMATIVA:
                raise ValueError(
                    f"La velocidad máxima debe ser mayor que la mínima normativa "
                    f"({V_MIN_NORMATIVA} m/s)."
                )

        except (ValueError, TypeError, KeyError) as e:
            if not silencioso:
                messagebox.showwarning("Datos inválidos", f"Revise los valores ingresados.\n{e}")
            return

        diam_m = diam_mm / 1000
        area = math.pi * diam_m ** 2 / 4
        velocidad = q / area

        cumple_velocidad = V_MIN_NORMATIVA <= velocidad <= v_max
        if not cumple_velocidad and not silencioso:
            messagebox.showwarning(
                "Velocidad fuera de rango",
                f"Con un diámetro de {diam_mm:,.0f} mm la velocidad resultante es "
                f"{velocidad:,.2f} m/s, fuera del rango permitido "
                f"[{V_MIN_NORMATIVA:,.2f} – {v_max:,.2f}] m/s.\n\n"
                f"Pruebe con otro diámetro comercial.",
            )

        # Hazen-Williams (SI): hf = 10.67 · L · Q^1.852 / (C^1.852 · D^4.87)
        perdida = 10.67 * longitud * (q ** 1.852) / (c_hw ** 1.852 * diam_m ** 4.87)

        factor_ariete = 1.3 if tipo_sistema == "Por bombeo" else 1.1

        presion_residual = None
        if desnivel is not None:
            presion_residual = desnivel - perdida

        self._resultado = dict(
            q=q, tipo_sistema=tipo_sistema, material=material, c_hw=c_hw,
            longitud=longitud, diam_mm=diam_mm, area=area, velocidad=velocidad,
            v_min=V_MIN_NORMATIVA, v_max=v_max, perdida=perdida,
            factor_ariete=factor_ariete, desnivel=desnivel,
            presion_residual=presion_residual, cumple_velocidad=cumple_velocidad,
        )

        self.lbl_factor_ariete.config(text=f"{factor_ariete:,.2f}")
        self.lbl_c_hw.config(text=f"{c_hw:,.0f}")
        self.lbl_area.config(text=f"{area:,.4f}")
        self.lbl_velocidad.config(
            text=f"{velocidad:,.3f}   {'✔ cumple' if cumple_velocidad else '⚠ fuera de rango'}"
        )
        self.lbl_perdida.config(text=f"{perdida:,.3f}")
        self.lbl_presion_residual.config(
            text=f"{presion_residual:,.3f}" if presion_residual is not None else "— (sin desnivel ingresado)"
        )

        self.lbl_diametro_final.config(text=f"{diam_mm:,.0f} mm")
        self.lbl_cumple_velocidad.config(
            text=f"Velocidad: {velocidad:,.3f} m/s — {'✔ cumple Art. 56' if cumple_velocidad else '⚠ NO cumple, revise el diámetro'}"
        )

    # ------------------------------------------------------------------
    def guardar(self):
        if not hasattr(self, "_resultado"):
            messagebox.showwarning("Falta calcular", "Primero presione Calcular.")
            return

        r = self._resultado
        EstadoProyecto.aduccion_tipo_sistema = r["tipo_sistema"]
        EstadoProyecto.aduccion_material = r["material"]
        EstadoProyecto.aduccion_c_hazen_williams = r["c_hw"]
        EstadoProyecto.aduccion_longitud = r["longitud"]
        EstadoProyecto.aduccion_diametro_mm = r["diam_mm"]
        EstadoProyecto.aduccion_area = r["area"]
        EstadoProyecto.aduccion_velocidad = r["velocidad"]
        EstadoProyecto.aduccion_v_min = r["v_min"]
        EstadoProyecto.aduccion_v_max = r["v_max"]
        EstadoProyecto.aduccion_perdida_carga = r["perdida"]
        EstadoProyecto.aduccion_factor_seguridad_ariete = r["factor_ariete"]
        EstadoProyecto.aduccion_desnivel_disponible = r["desnivel"]
        EstadoProyecto.aduccion_presion_residual = r["presion_residual"]

        messagebox.showinfo(
            "Guardado",
            "Aducción / conducción guardada correctamente.\n\n" + EstadoProyecto.resumen_aduccion(),
        )

        if self.al_guardar:
            self.al_guardar()

        self.destroy()
