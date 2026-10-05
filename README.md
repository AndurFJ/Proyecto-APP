# HydroLab

Software de escritorio para el diseño de **Plantas de Tratamiento de Agua Potable (PTAP)** y **Plantas de Tratamiento de Aguas Residuales (PTAR)**, siguiendo la **Resolución 0330 de 2017** (modificada por la Resolución 799 de 2021) del Ministerio de Vivienda de Colombia.

La aplicación está escrita en Python con interfaz gráfica Tkinter. Desde la ventana principal se ingresan los datos del proyecto, se calcula el caudal de diseño y luego se diseña cada proceso de la planta en su propia ventana de cálculo. Al final se puede exportar un informe en PDF con los resultados.

## Requisitos

- Python 3.9 o superior, con Tkinter (incluido en Python para Windows y macOS; en Linux instalar `python3-tk`).
- Las librerías de `requirements.txt`: pandas, matplotlib y reportlab.

## Instalación

```bash
git clone https://github.com/AndurFJ/Proyecto-APP.git
cd Proyecto-APP
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

## Módulos implementados

| Módulo | Archivo | Estado |
|---|---|---|
| ① Datos preliminares (población DANE, proyección) | `ventana_datos_preliminares.py`, `datos_dane.py` | Implementado |
| ② Caudal de diseño PTAP | `ventana_caudal_diseno.py` | Implementado |
| ② Caudal de diseño PTAR | `ventana_caudal_diseno.py` | Provisional (usa las fórmulas de PTAP) |
| PTAP: Captación (bocatoma con rejilla) | `ventana_bocatoma_rejilla.py` | Implementado |
| PTAP: Desarenador | `ventana_desarenador.py` | Implementado |
| PTAP: Aducción / conducción | `m.py` | Escrito, aún no conectado al menú |
| PTAP: Mezcla rápida, floculación, sedimentación, filtración, desinfección, tanque de almacenamiento | `ventanas_ptap.py` | Pendiente |
| PTAR: procesos de tratamiento | — | Pendiente |
| Datos técnicos de referencia | `ventana_datos_tecnicos.py`, `datos_tecnicos_referencia.py` | Implementado |
| Informe PDF | `generador_pdf.py` | Implementado |

## Estructura del proyecto

- `main.py`: ventana principal y punto de entrada.
- `estado_proyecto.py`: estado compartido del proyecto entre ventanas.
- `ui_utils.py`: utilidades de interfaz (geometría, scroll).
- `pob_municipal.csv`: datos de población municipal del DANE.
- `DejaVuSans*.ttf`: fuentes usadas en el informe PDF.

## Autor

Elier Mendoza, Ingeniería Ambiental y Sanitaria.
