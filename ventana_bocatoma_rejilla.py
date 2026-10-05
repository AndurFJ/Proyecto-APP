"""
Ventana de Captación — Bocatoma con Rejilla.

Primer proceso de diseño de la PTAP: a partir del caudal de diseño
(Paso 2) calcula el área de captación, la geometría de la rejilla
(número y longitud de barrotes, área y ancho de la rejilla) y las
pérdidas de carga en la rejilla — replicando la lógica de las hojas
"DISEÑO DE LA REJILLA" / "TERMINOS DE REFERENCIA" / "DATOS
PRELIMINARES" del archivo de referencia (RAS 2000).

Nota: la fórmula del área de la rejilla (Ar) en el Excel de
referencia tiene una inconsistencia dimensional cuando Hrh != 1
(el Excel usa "(n*s) + (n+1)*z*Hrh" en vez de "((n*s)+(n+1)*z)*Hrh").
Aquí se usa la fórmula físicamente correcta.
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

from estado_proyecto import EstadoProyecto
from ui_utils import ajustar_geometria


# --- Tablas de referencia (RAS 2000 / archivo Excel de referencia) ---

RANGOS_INCLINACION = {
    "Verticales": (75, 85),
    "Inclinadas": (45, 60),
}

# Separación entre barrotes (z), según tipo de grava.
# El Excel de referencia usa el límite inferior del rango.
VALORES_Z_GRAVA = {
    "Finas": 0.02,
    "Medias": 0.04,
    "Gruesas": 0.075,
}

# Coeficiente de pérdidas por forma del barrote (Kirschmer),
# tomado de la tabla "FORMA Y COEFICIENTE DE LOS BARROTES" del Excel.
COEFICIENTES_FORMA_BARROTE = {
    "C1": 2.42,
    "C2": 1.83,
    "C3": 1.67,
    "C4": 1.035,
    "C5": 0.92,
    "C6": 0.76,
    "C7": 1.79,
}


class VentanaBocatomaRejilla(tk.Toplevel):
    def __init__(self, master, al_guardar=None):
        super().__init__(master)
        self.title("Captación — Bocatoma con Rejilla")
        self.resizable(False, True)
        ajustar_geometria(self, ancho=620, alto=780)
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
            self, text="CAPTACIÓN — BOCATOMA CON REJILLA",
            font=("Arial", 14, "bold"), bg="#1F4E78", fg="white", pady=10,
        )
        titulo.pack(fill="x")

        contenedor = tk.Frame(self, bg="#F2F4F4")
        contenedor.pack(fill="both", expand=True)

        canvas = tk.Canvas(contenedor, bg="#F2F4F4", highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        cuerpo_ext = tk.Frame(canvas, bg="#F2F4F4")
        ventana_id = canvas.create_window((0, 0), window=cuerpo_ext, anchor="nw")
        cuerpo_ext.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(ventana_id, width=e.width),
        )

        def _rueda(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _rueda)

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

        # --- Caudal y velocidad de aproximación ---
        etiqueta(cuerpo, "Caudal de diseño (m³/s):")
        resultado(cuerpo, "lbl_caudal")

        etiqueta(cuerpo, "Velocidad efectiva del flujo Vf (m/s):", editable=True)
        self.entry_vf = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_vf.insert(0, "0.15")
        self.entry_vf.pack(fill="x")

        etiqueta(cuerpo, "Área de captación — Ac (m²):")
        resultado(cuerpo, "lbl_ac")

        etiqueta(cuerpo, "Área de captación efectiva — Ac efectiva (m²):")
        resultado(cuerpo, "lbl_ac_ef")

        # --- Inclinación de la rejilla ---
        etiqueta(cuerpo, "Tipo de inclinación de la rejilla:", editable=True)
        self.cb_inclinacion = ttk.Combobox(
            cuerpo, values=list(RANGOS_INCLINACION.keys()),
            state="readonly", style="Editable.TCombobox",
        )
        self.cb_inclinacion.set("Inclinadas")
        self.cb_inclinacion.pack(fill="x")
        self.cb_inclinacion.bind("<<ComboboxSelected>>", self._al_cambiar_inclinacion)

        self.lbl_rango_inclinacion = tk.Label(
            cuerpo, text="", font=("Arial", 8, "italic"), bg="#F2F4F4", fg="#7B7D7D", anchor="w",
        )
        self.lbl_rango_inclinacion.pack(fill="x")

        etiqueta(cuerpo, "Ángulo de inclinación (°):", editable=True)
        self.entry_angulo = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_angulo.pack(fill="x")

        # --- Separación entre barrotes ---
        etiqueta(cuerpo, "Tipo de grava (separación entre barrotes z):", editable=True)
        self.cb_grava = ttk.Combobox(
            cuerpo, values=list(VALORES_Z_GRAVA.keys()),
            state="readonly", style="Editable.TCombobox",
        )
        self.cb_grava.set("Gruesas")
        self.cb_grava.pack(fill="x")
        self.cb_grava.bind("<<ComboboxSelected>>", lambda e: self.calcular())

        etiqueta(cuerpo, "Separación entre barrotes — z (m):")
        resultado(cuerpo, "lbl_z")

        # --- Forma y espesor del barrote ---
        etiqueta(cuerpo, "Forma del barrote:", editable=True)
        self.cb_forma = ttk.Combobox(
            cuerpo, values=list(COEFICIENTES_FORMA_BARROTE.keys()),
            state="readonly", style="Editable.TCombobox",
        )
        self.cb_forma.set("C7")
        self.cb_forma.pack(fill="x")
        self.cb_forma.bind("<<ComboboxSelected>>", lambda e: self.calcular())

        etiqueta(cuerpo, "Coeficiente de pérdidas (Kirschmer):")
        resultado(cuerpo, "lbl_coef_forma")

        etiqueta(cuerpo, "Diámetro / espesor del barrote (in):", editable=True)
        self.entry_diametro = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_diametro.insert(0, "1")
        self.entry_diametro.pack(fill="x")

        etiqueta(cuerpo, "Espesor del barrote — s (m):")
        resultado(cuerpo, "lbl_s")

        # --- Borde libre y altura húmeda ---
        etiqueta(cuerpo, "Borde libre (m):", editable=True)
        self.entry_borde = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_borde.insert(0, "0.3")
        self.entry_borde.pack(fill="x")

        etiqueta(cuerpo, "Altura de la rejilla en área húmeda — Hrh (m):", editable=True)
        self.entry_hrh = ttk.Entry(cuerpo, style="Editable.TEntry")
        self.entry_hrh.insert(0, "1")
        self.entry_hrh.pack(fill="x")

        # --- Resultados geométricos ---
        etiqueta(cuerpo, "N° de espacios entre barrotes (n+1):")
        resultado(cuerpo, "lbl_num_espacios")

        etiqueta(cuerpo, "N° de barrotes (n):")
        resultado(cuerpo, "lbl_num_barrotes")

        etiqueta(cuerpo, "Longitud sumergida del barrote — Lrh (m):")
        resultado(cuerpo, "lbl_lrh")

        etiqueta(cuerpo, "Longitud total del barrote — Lrt (m):")
        resultado(cuerpo, "lbl_lrt")

        etiqueta(cuerpo, "Longitud de barrotes — valor de referencia/catálogo (m):")
        resultado(cuerpo, "lbl_long_barrotes")

        # --- Botón calcular ---
        tk.Button(
            cuerpo, text="Calcular", font=("Arial", 11, "bold"),
            bg="#2E86C1", fg="white", cursor="hand2", command=self.calcular,
        ).pack(fill="x", pady=(15, 10), ipady=6)

        # --- Resultados finales destacados ---
        marco_final = tk.Frame(
            cuerpo, bg="#EAFAF1", bd=2, relief="solid",
            highlightbackground="#1E8449", highlightthickness=2,
        )
        marco_final.pack(fill="x", pady=(10, 15))
        tk.Label(
            marco_final, text="✅ RESULTADOS DE LA REJILLA", font=("Arial", 11, "bold"),
            bg="#EAFAF1", fg="#1E8449",
        ).pack(pady=(10, 4))

        fila = tk.Frame(marco_final, bg="#EAFAF1")
        fila.pack(pady=(0, 4))
        self.lbl_area_rejilla = tk.Label(
            fila, text="Área: — m²", font=("Arial", 13, "bold"), bg="#EAFAF1", fg="#1E8449",
        )
        self.lbl_area_rejilla.pack(side="left", padx=10)
        self.lbl_ancho_rejilla = tk.Label(
            fila, text="Ancho: — m", font=("Arial", 13, "bold"), bg="#EAFAF1", fg="#1E8449",
        )
        self.lbl_ancho_rejilla.pack(side="left", padx=10)

        self.lbl_perdidas = tk.Label(
            marco_final, text="Pérdidas en la rejilla (Δh): — m",
            font=("Arial", 12, "bold"), bg="#EAFAF1", fg="#1E8449",
        )
        self.lbl_perdidas.pack(pady=(0, 10))

        tk.Button(
            cuerpo, text="💾 Guardar y continuar", font=("Arial", 12, "bold"),
            bg="#28B463", fg="white", cursor="hand2", command=self.guardar,
        ).pack(fill="x", ipady=8, pady=(0, 20))

        for entry in (self.entry_vf, self.entry_angulo, self.entry_diametro,
                      self.entry_borde, self.entry_hrh):
            entry.bind("<FocusOut>", lambda e: self.calcular())

    # ------------------------------------------------------------------
    def _al_cambiar_inclinacion(self, event=None):
        self._actualizar_rango_inclinacion()
        self.calcular()

    def _actualizar_rango_inclinacion(self):
        tipo = self.cb_inclinacion.get()
        minimo, maximo = RANGOS_INCLINACION[tipo]
        self.lbl_rango_inclinacion.config(
            text=f"Rango permitido para '{tipo}': {minimo}° – {maximo}°"
        )
        # Si el ángulo actual está vacío o fuera de rango, sugerir el valor medio
        try:
            angulo_actual = float(self.entry_angulo.get())
        except ValueError:
            angulo_actual = None
        if angulo_actual is None or not (minimo <= angulo_actual <= maximo):
            self.entry_angulo.delete(0, tk.END)
            self.entry_angulo.insert(0, str((minimo + maximo) / 2))

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
        self._actualizar_rango_inclinacion()
        self.calcular()

    # ------------------------------------------------------------------
    def calcular(self):
        try:
            q_diseño = EstadoProyecto.caudal_diseño_m3s
            vf = float(self.entry_vf.get())
            tipo_inclinacion = self.cb_inclinacion.get()
            angulo = float(self.entry_angulo.get())
            tipo_grava = self.cb_grava.get()
            forma = self.cb_forma.get()
            diametro_in = float(self.entry_diametro.get())
            borde_libre = float(self.entry_borde.get())
            hrh = float(self.entry_hrh.get())

            if vf <= 0:
                raise ValueError("La velocidad Vf debe ser mayor que 0.")
            if hrh <= 0:
                raise ValueError("La altura Hrh debe ser mayor que 0.")

            minimo, maximo = RANGOS_INCLINACION[tipo_inclinacion]
            if not (minimo <= angulo <= maximo):
                raise ValueError(
                    f"El ángulo debe estar entre {minimo}° y {maximo}° "
                    f"para rejillas '{tipo_inclinacion}'."
                )

        except (ValueError, TypeError, KeyError) as e:
            messagebox.showwarning("Datos inválidos", f"Revise los valores ingresados.\n{e}")
            return

        z = VALORES_Z_GRAVA[tipo_grava]
        coef_forma = COEFICIENTES_FORMA_BARROTE[forma]
        s = diametro_in * 0.0254
        angulo_rad = math.radians(angulo)
        sen_angulo = math.sin(angulo_rad)

        ac = q_diseño / vf
        ac_ef = ac * 2

        num_espacios = ac_ef / (hrh * z)         # n+1
        num_barrotes = num_espacios - 1          # n

        # Área de la rejilla: fórmula físicamente correcta
        # (ancho total de la cara de la rejilla) x (altura húmeda)
        area_rejilla = ((num_barrotes * s) + (num_espacios * z)) * hrh
        ancho_rejilla = area_rejilla / hrh

        perdidas = coef_forma * (s / z) ** 1.33

        lrh = hrh / sen_angulo
        lrt = round((hrh + borde_libre) / sen_angulo, 1)
        long_barrotes = s * 5  # valor de referencia/catálogo (ver nota del Excel original)

        self._resultado = dict(
            q_diseño=q_diseño, vf=vf, ac=ac, ac_ef=ac_ef,
            tipo_inclinacion=tipo_inclinacion, angulo=angulo,
            tipo_grava=tipo_grava, z=z, forma=forma, coef_forma=coef_forma,
            diametro_in=diametro_in, s=s, borde_libre=borde_libre, hrh=hrh,
            num_espacios=num_espacios, num_barrotes=num_barrotes,
            area_rejilla=area_rejilla, ancho_rejilla=ancho_rejilla,
            perdidas=perdidas, lrh=lrh, lrt=lrt, long_barrotes=long_barrotes,
        )

        self.lbl_ac.config(text=f"{ac:,.4f}")
        self.lbl_ac_ef.config(text=f"{ac_ef:,.4f}")
        self.lbl_z.config(text=f"{z:,.3f}")
        self.lbl_coef_forma.config(text=f"{coef_forma:,.3f}")
        self.lbl_s.config(text=f"{s:,.4f}")
        self.lbl_num_espacios.config(text=f"{num_espacios:,.2f}")
        self.lbl_num_barrotes.config(text=f"{num_barrotes:,.2f}")
        self.lbl_lrh.config(text=f"{lrh:,.3f}")
        self.lbl_lrt.config(text=f"{lrt:,.1f}")
        self.lbl_long_barrotes.config(text=f"{long_barrotes:,.4f}")

        self.lbl_area_rejilla.config(text=f"Área: {area_rejilla:,.3f} m²")
        self.lbl_ancho_rejilla.config(text=f"Ancho: {ancho_rejilla:,.3f} m")
        self.lbl_perdidas.config(text=f"Pérdidas en la rejilla (Δh): {perdidas:,.4f} m")

    # ------------------------------------------------------------------
    def guardar(self):
        if not hasattr(self, "_resultado"):
            messagebox.showwarning("Falta calcular", "Primero presione Calcular.")
            return

        r = self._resultado
        EstadoProyecto.vf = r["vf"]
        EstadoProyecto.tipo_inclinacion = r["tipo_inclinacion"]
        EstadoProyecto.angulo_inclinacion = r["angulo"]
        EstadoProyecto.tipo_grava = r["tipo_grava"]
        EstadoProyecto.valor_z = r["z"]
        EstadoProyecto.forma_barrote = r["forma"]
        EstadoProyecto.coef_forma_barrote = r["coef_forma"]
        EstadoProyecto.diametro_barrote_in = r["diametro_in"]
        EstadoProyecto.s_barrote = r["s"]
        EstadoProyecto.borde_libre = r["borde_libre"]
        EstadoProyecto.hrh = r["hrh"]
        EstadoProyecto.longitud_barrotes = r["long_barrotes"]
        EstadoProyecto.longitud_sumergida = r["lrh"]
        EstadoProyecto.longitud_total_barrote = r["lrt"]
        EstadoProyecto.area_captacion = r["ac"]
        EstadoProyecto.area_captacion_efectiva = r["ac_ef"]
        EstadoProyecto.num_espacios = r["num_espacios"]
        EstadoProyecto.num_barrotes = r["num_barrotes"]
        EstadoProyecto.area_rejilla = r["area_rejilla"]
        EstadoProyecto.ancho_rejilla = r["ancho_rejilla"]
        EstadoProyecto.perdidas_rejilla = r["perdidas"]

        messagebox.showinfo(
            "Guardado",
            "Bocatoma con rejilla guardada correctamente.\n\n" + EstadoProyecto.resumen_rejilla(),
        )

        if self.al_guardar:
            self.al_guardar()

        self.destroy()
