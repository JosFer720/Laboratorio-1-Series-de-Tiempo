"""Construye los notebooks reproducibles S0 y S1 para el avance.

Los notebooks se generan con nbformat y luego deben ejecutarse desde la raíz:

    .venv/bin/python -m jupyter nbconvert --execute --to notebook \
        --inplace notebooks/02_series_total.ipynb
"""

from pathlib import Path

import nbformat as nbf


RAIZ = Path(__file__).resolve().parent.parent
DIR_NOTEBOOKS = RAIZ / "notebooks"


def md(texto):
    return nbf.v4.new_markdown_cell(texto.strip())


def code(codigo):
    return nbf.v4.new_code_cell(codigo.strip())


def construir_notebook(nombre_serie, titulo, etiqueta, prefijo_img, interpretaciones):
    nb = nbf.v4.new_notebook()
    nb["metadata"]["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb["metadata"]["language_info"] = {"name": "python", "version": "3.12"}

    nb["cells"] = [
        md(
            f"""
# {titulo}

**Serie:** `{nombre_serie}` · **Unidad:** viajeros por mes ·
**Filtro:** Turista + Excursionista

## Resumen técnico

{interpretaciones["resumen"]}

El análisis de estacionariedad y la descomposición se realizan exclusivamente
sobre entrenamiento (enero de 2009 a marzo de 2021). El tramo de prueba se
conserva intacto para la evaluación predictiva de la entrega final.
"""
        ),
        md(
            """
## 1. Contexto y metodología

La serie se agrega al inicio de cada mes (`MS`) y usa una frecuencia estacional
de 12 observaciones por año. La partición es temporal: los primeros 147 meses
forman entrenamiento y los últimos 63 forman prueba. No se barajan los datos.
"""
        ),
        code(
            f"""
from pathlib import Path
import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.graphics.tsaplots import plot_acf

RAIZ = Path.cwd().resolve()
if RAIZ.name == "notebooks":
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ / "src"))

import config
from utils_ts import (
    cargar_serie,
    descomponer,
    fuerza_estacional,
    fuerza_tendencia,
    partir_train_test,
    test_estacionariedad,
)

warnings.filterwarnings("ignore", category=UserWarning)
sns.set_theme(style="whitegrid")
plt.rcParams.update({{"figure.dpi": 110, "axes.titlesize": 12}})

DIR_IMG = RAIZ / "informe" / "img"
DIR_IMG.mkdir(parents=True, exist_ok=True)

serie = cargar_serie("{nombre_serie}")
train, test = partir_train_test(serie)

resumen = pd.DataFrame({{
    "serie": ["{etiqueta}"],
    "inicio_total": [serie.index.min().strftime("%Y-%m")],
    "fin_total": [serie.index.max().strftime("%Y-%m")],
    "frecuencia": ["mensual (m=12)"],
    "meses_total": [len(serie)],
    "inicio_train": [train.index.min().strftime("%Y-%m")],
    "fin_train": [train.index.max().strftime("%Y-%m")],
    "meses_train": [len(train)],
    "inicio_test": [test.index.min().strftime("%Y-%m")],
    "fin_test": [test.index.max().strftime("%Y-%m")],
    "meses_test": [len(test)],
}})
resumen
"""
        ),
        md(
            """
## 2. La serie completa muestra el corte pandémico y la recuperación

La gráfica presenta todo el período para dar contexto, pero el análisis
estadístico posterior solo utiliza el tramo anterior a la línea de corte.
"""
        ),
        code(
            f"""
fig, ax = plt.subplots(figsize=(13, 4.2))
ax.plot(serie.index, serie.values, color="#2f6690", linewidth=1.5,
        label="{etiqueta}")
ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2021-12-01"),
           color="#f2cf5b", alpha=0.20, label="pandemia y restricciones")
ax.axvline(test.index.min(), color="#b23a48", linestyle="--", linewidth=1.5,
           label="inicio del test (2021-04)")
ax.set_title("{etiqueta}: serie mensual y partición temporal")
ax.set_ylabel("viajeros")
ax.set_xlabel("")
ax.legend(loc="upper left", fontsize=8)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(DIR_IMG / "{prefijo_img}_serie.png", bbox_inches="tight")
plt.show()

print(f"Mínimo de entrenamiento: {{train.min():,.0f}} viajeros "
      f"({{train.idxmin():%Y-%m}})")
print(f"Máximo de entrenamiento: {{train.max():,.0f}} viajeros "
      f"({{train.idxmax():%Y-%m}})")
"""
        ),
        md(interpretaciones["primera_vista"]),
        md(
            """
## 3. La descomposición confirma tendencia y estacionalidad

Se utiliza una descomposición aditiva con período 12. La pandemia rompe
temporalmente el patrón y debe interpretarse como un cambio estructural, no
como un error de captura.
"""
        ),
        code(
            f"""
descomp = descomponer(train, modelo="additive", graficar=False)

fig, axes = plt.subplots(4, 1, figsize=(13, 9), sharex=True)
componentes = [
    (train, "Observada", "#2f6690"),
    (descomp.trend, "Tendencia", "#c44536"),
    (descomp.seasonal, "Estacionalidad", "#6a994e"),
    (descomp.resid, "Residuo", "#6c757d"),
]
for ax, (datos, nombre, color) in zip(axes, componentes):
    ax.plot(datos.index, datos.values, color=color, linewidth=1.2)
    ax.set_ylabel(nombre)
    ax.grid(alpha=0.25)
axes[0].set_title("{etiqueta}: descomposición aditiva del entrenamiento")
fig.tight_layout()
fig.savefig(DIR_IMG / "{prefijo_img}_descomposicion.png", bbox_inches="tight")
plt.show()

print(f"Fuerza estacional: {{fuerza_estacional(descomp):.3f}}")
print(f"Fuerza de tendencia: {{fuerza_tendencia(descomp):.3f}}")
"""
        ),
        md(interpretaciones["descomposicion"]),
        md(
            """
## 4. La transformación logarítmica es adecuada para la varianza

Como la serie es estrictamente positiva, el logaritmo es aplicable. Se compara
la media y desviación móvil de 12 meses antes y después de transformar.
"""
        ),
        code(
            f"""
log_train = np.log(train)
media_movil = train.rolling(12).mean()
desv_movil = train.rolling(12).std()
media_log = log_train.rolling(12).mean()
desv_log = log_train.rolling(12).std()

fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
axes[0].plot(train.index, train, color="#9ecae1", linewidth=0.9,
             label="serie")
axes[0].plot(media_movil.index, media_movil, color="#2f6690",
             linewidth=1.5, label="media móvil 12m")
axes[0].plot(desv_movil.index, desv_movil, color="#c44536",
             linewidth=1.3, label="desv. móvil 12m")
axes[0].set_title("{etiqueta}: nivel original")
axes[0].legend(fontsize=8)

axes[1].plot(log_train.index, log_train, color="#b7d7a8", linewidth=0.9,
             label="log(serie)")
axes[1].plot(media_log.index, media_log, color="#386641",
             linewidth=1.5, label="media móvil 12m")
axes[1].plot(desv_log.index, desv_log, color="#6a4c93",
             linewidth=1.3, label="desv. móvil 12m")
axes[1].set_title("{etiqueta}: escala logarítmica")
axes[1].legend(fontsize=8)

for ax in axes:
    ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(DIR_IMG / "{prefijo_img}_varianza.png", bbox_inches="tight")
plt.show()

print(f"Correlación media-desviación móvil, nivel: "
      f"{{media_movil.corr(desv_movil):.3f}}")
print(f"Correlación media-desviación móvil, log: "
      f"{{media_log.corr(desv_log):.3f}}")
"""
        ),
        md(interpretaciones["transformacion"]),
        md(
            """
## 5. ACF y pruebas formales: se requiere diferenciación

ADF usa como hipótesis nula la presencia de raíz unitaria; KPSS usa como
hipótesis nula la estacionariedad. Se revisan nivel, logaritmo, primera
diferencia, diferencia estacional y la combinación de ambas.
"""
        ),
        code(
            """
transformaciones = {
    "Nivel": train,
    "Log": log_train,
    "Δ Log (d=1)": log_train.diff().dropna(),
    "Δ12 Log (D=1)": log_train.diff(12).dropna(),
    "Δ Δ12 Log (d=1, D=1)": log_train.diff().diff(12).dropna(),
}

resultados = []
for nombre, datos in transformaciones.items():
    resultado = test_estacionariedad(datos, nombre=nombre, verbose=False)
    resultados.append({
        "transformación": nombre,
        "ADF": resultado["adf_estadistico"],
        "p ADF": resultado["adf_p"],
        "rezagos ADF": resultado["adf_rezagos"],
        "KPSS": resultado["kpss_estadistico"],
        "p KPSS": resultado["kpss_p"],
        "veredicto": resultado["veredicto"],
    })

tabla_pruebas = pd.DataFrame(resultados)
tabla_pruebas.round({
    "ADF": 4, "p ADF": 4, "KPSS": 4, "p KPSS": 4
})
"""
        ),
        code(
            f"""
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
plot_acf(train, lags=36, ax=axes[0], color="#2f6690")
axes[0].set_title("ACF del nivel")
plot_acf(log_train.diff().dropna(), lags=36, ax=axes[1], color="#c44536")
axes[1].set_title("ACF de Δ log (d=1)")
plot_acf(log_train.diff().diff(12).dropna(), lags=36,
         ax=axes[2], color="#6a994e")
axes[2].set_title("ACF de ΔΔ12 log (d=1, D=1)")
for ax in axes:
    ax.grid(alpha=0.20)
fig.suptitle("{etiqueta}: autocorrelación antes y después de diferenciar",
             y=1.03)
fig.tight_layout()
fig.savefig(DIR_IMG / "{prefijo_img}_acf.png", bbox_inches="tight")
plt.show()
"""
        ),
        md(interpretaciones["estacionariedad"]),
        md(
            f"""
## 6. Conclusión para el avance

| Serie | Inicio–fin | Frecuencia | ¿Estacionaria en nivel? | Transformación | `d` propuesto | `D` estacional candidato |
|---|---|---|---|---|---:|---:|
| {etiqueta} | ene 2009–jun 2026 | mensual (`m=12`) | No | log | 1 | 1 |

{interpretaciones["conclusion"]}

La selección de `p`, `q` y de los modelos predictivos se deja para la entrega
final, tal como establece la planificación del avance.
"""
        ),
    ]
    return nb


NOTEBOOKS = [
    (
        "02_series_total.ipynb",
        construir_notebook(
            "S0_total",
            "02 — Análisis de la serie total (S0)",
            "S0 — Total mensual",
            "2_s0",
            {
                "resumen": (
                    "S0 presenta crecimiento y estacionalidad antes de 2020, "
                    "seguido de una ruptura por la pandemia. El nivel no supera "
                    "ADF al 5%; la primera diferencia del logaritmo sí lo hace."
                ),
                "primera_vista": (
                    "A primera vista se distingue un crecimiento sostenido entre "
                    "2009 y 2019, oscilaciones anuales y un máximo en diciembre "
                    "de 2019. En marzo de 2020 comienza el colapso por la pandemia. "
                    "El corte de entrenamiento ocurre en marzo de 2021, cuando la "
                    "recuperación todavía era incompleta; por ello el futuro test "
                    "contiene un régimen distinto al tramo final del entrenamiento."
                ),
                "descomposicion": (
                    "La tendencia cambia a lo largo del tiempo y la componente "
                    "estacional repite un patrón mensual, por lo que la media no "
                    "es constante. La dispersión de los residuos aumenta durante "
                    "el choque pandémico. La serie no puede considerarse "
                    "estacionaria en media y la varianza debe analizarse en una "
                    "escala relativa."
                ),
                "transformacion": (
                    "Se adopta `log(S0)` porque todos los valores son positivos y "
                    "la transformación expresa los cambios de forma relativa, "
                    "reduce la influencia de los picos y hace más comparable la "
                    "amplitud estacional entre niveles. El logaritmo no elimina "
                    "la ruptura de 2020, que seguirá tratándose como limitación "
                    "estructural del entrenamiento."
                ),
                "estacionariedad": (
                    "En nivel, ADF no rechaza la raíz unitaria (`p≈0.152`) y la "
                    "ACF decae lentamente, coherente con no estacionariedad en "
                    "media. En el logaritmo el resultado sigue sin ser suficiente "
                    "(`p≈0.116`). La primera diferencia del logaritmo sí rechaza "
                    "la raíz unitaria (`p≈0.028`) y KPSS no rechaza "
                    "estacionariedad, por lo que se propone `d=1`. Los picos "
                    "estacionales justifican evaluar además `D=1`; la combinación "
                    "`d=1, D=1` supera ambas pruebas con holgura."
                ),
                "conclusion": (
                    "Para la siguiente fase se trabajará con la escala logarítmica "
                    "y una diferencia regular. La diferencia estacional se "
                    "comparará como candidata en los modelos SARIMA, sin utilizar "
                    "el conjunto de prueba para escogerla."
                ),
            },
        ),
    ),
    (
        "03_series_fronteras.ipynb",
        construir_notebook(
            "S1_la_aurora",
            "03 — Análisis de la frontera La Aurora (S1)",
            "S1 — La Aurora",
            "3_s1",
            {
                "resumen": (
                    "La Aurora muestra una estacionalidad mensual más marcada que "
                    "la serie total y una ruptura extrema durante la pandemia. "
                    "El nivel no supera ADF; la primera diferencia logarítmica sí."
                ),
                "primera_vista": (
                    "La serie crece gradualmente antes de 2020 y presenta picos "
                    "recurrentes asociados con temporadas de viaje aéreo. Durante "
                    "el cierre pandémico cae a valores cercanos a cero. El "
                    "entrenamiento finaliza en marzo de 2021, antes de que el "
                    "aeropuerto recupere su patrón habitual, lo que anticipa una "
                    "evaluación predictiva especialmente exigente."
                ),
                "descomposicion": (
                    "La componente estacional es clara y recurrente, mientras la "
                    "tendencia ascendente se rompe en 2020. La media cambia y los "
                    "residuos son mucho más dispersos alrededor del choque. Por "
                    "tanto, La Aurora no es estacionaria en media y la estabilidad "
                    "de varianza debe evaluarse después de transformar."
                ),
                "transformacion": (
                    "Se adopta `log(S1)` porque la serie es estrictamente positiva "
                    "y la estacionalidad se interpreta mejor en términos "
                    "proporcionales. La transformación comprime los picos y el "
                    "colapso, pero no convierte la pandemia en un comportamiento "
                    "ordinario; ese quiebre permanece como limitación."
                ),
                "estacionariedad": (
                    "En nivel, ADF no rechaza la raíz unitaria (`p≈0.150`) y la "
                    "ACF conserva autocorrelaciones altas, evidencia de no "
                    "estacionariedad. El logaritmo tampoco basta (`p≈0.273`). La "
                    "primera diferencia logarítmica rechaza la raíz unitaria "
                    "(`p≈0.027`) y KPSS no rechaza estacionariedad, por lo que se "
                    "propone `d=1`. La estacionalidad visible y los rezagos 12, 24 "
                    "y 36 justifican evaluar `D=1`; la transformación combinada "
                    "también supera las pruebas."
                ),
                "conclusion": (
                    "Para la fase de modelos se usará el logaritmo con `d=1` y se "
                    "compararán especificaciones con y sin `D=1`. La decisión "
                    "definitiva deberá apoyarse en residuos y desempeño fuera de "
                    "muestra, no solo en estas pruebas."
                ),
            },
        ),
    ),
]


for archivo, notebook in NOTEBOOKS:
    ruta = DIR_NOTEBOOKS / archivo
    nbf.write(notebook, ruta)
    print(f"[creado] {ruta.relative_to(RAIZ)}")

