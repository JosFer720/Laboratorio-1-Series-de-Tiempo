from pathlib import Path

import nbformat as nbf


RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "notebooks" / "03_series_fronteras.ipynb"


def md(texto):
    return nbf.v4.new_markdown_cell(texto.strip())


def code(codigo):
    return nbf.v4.new_code_cell(codigo.strip())


nb = nbf.v4.new_notebook()
nb["metadata"]["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb["metadata"]["language_info"] = {"name": "python", "version": "3.12"}

nb["cells"] = [
    md(
        """
# 03 — Análisis completo de Fronteras (S1–S3)

Este cuaderno completa el **Bloque B de la Parte II** para las tres fronteras
con mayor acumulado de turistas y excursionistas: La Aurora, Valle Nuevo y San
Cristóbal. Cada serie sigue el mismo flujo: inspección, descomposición aditiva
y multiplicativa, estacionariedad en varianza y media, ACF/PACF, candidatos
ARIMA/SARIMA, cuatro modelos alternativos, residuos y pronóstico de los 63
meses de prueba.
"""
    ),
    md(
        """
## Metodología común

- Frecuencia mensual (`MS`) y período estacional 12.
- Entrenamiento: enero de 2009 a marzo de 2021 (147 meses).
- Prueba: abril de 2021 a junio de 2026 (63 meses), sin barajar.
- La elección de `d` y `D` usa ADF, KPSS y ACF.
- ACF/PACF se muestran por separado después de `d=1` y después de
  `d=1,D=1`, para no mezclar la selección regular con la estacional.
- Los residuos se revisan con serie temporal, ACF, Ljung-Box, histograma,
  Jarque-Bera y gráfico Q-Q.
- El mejor pronóstico se selecciona principalmente por RMSE en prueba, sin
  ignorar AIC/BIC ni el diagnóstico residual.
"""
    ),
    code(
        """
from pathlib import Path
import sys

import pandas as pd
from IPython.display import Image, display

RAIZ = Path.cwd().resolve()
if RAIZ.name == "notebooks":
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ / "src"))

from modelado_s1_s2_s6 import ejecutar_modelado_fronteras

resultados, comparativo = ejecutar_modelado_fronteras(
    guardar=True,
    generar_figuras=True,
)
DIR_RESULTADOS = RAIZ / "data" / "processed" / "resultados"
DIR_IMG = RAIZ / "informe" / "img" / "final"
metricas = pd.read_csv(DIR_RESULTADOS / "metricas_fronteras.csv")
estacionariedad = pd.read_csv(
    DIR_RESULTADOS / "estacionariedad_fronteras.csv"
)

validacion = pd.DataFrame({
    "serie": ["S1", "S2", "S3"],
    "meses_total": [len(resultados[n]["serie"]) for n in resultados],
    "meses_train": [len(resultados[n]["train"]) for n in resultados],
    "meses_test": [len(resultados[n]["test"]) for n in resultados],
    "ceros_train": [
        resultados[n]["resumen"]["ceros_train"] for n in resultados
    ],
    "ceros_test": [
        resultados[n]["resumen"]["ceros_test"] for n in resultados
    ],
})
validacion
"""
    ),
    md(
        """
## S1 — La Aurora

La Aurora es la frontera aérea principal. Su fuerza estacional es 0.559 y la
de tendencia 0.811. La correlación media-desviación prepandemia baja de 0.889
en nivel a -0.209 después del logaritmo, por lo que la transformación elimina
la relación positiva entre nivel y amplitud. La forma multiplicativa es la
descomposición descriptiva preferida.
"""
    ),
    code(
        """
display(Image(filename=str(DIR_IMG / "s1_serie_particion.png")))
display(Image(filename=str(DIR_IMG / "s1_descomposicion.png")))
display(Image(filename=str(DIR_IMG / "s1_varianza.png")))
"""
    ),
    md(
        """
ADF y KPSS coinciden en estacionariedad después de `d=1`. ACF y PACF no
muestran un corte limpio en el primer rezago y conservan picos aislados en 5 y
7 por el choque pandémico. Se comparan órdenes bajos `(1,1,0)`, `(0,1,1)` y
`(1,1,1)`, además de un SARIMA anual.
"""
    ),
    code(
        """
display(
    estacionariedad.loc[
        estacionariedad["serie"] == "S1_la_aurora",
        ["transformacion", "p_ADF", "p_KPSS", "veredicto"],
    ].round(4)
)
display(Image(filename=str(DIR_IMG / "s1_acf_pacf.png")))
"""
    ),
    code(
        """
display(
    metricas.loc[
        metricas["serie"] == "S1_la_aurora",
        [
            "modelo", "AIC", "BIC", "MAE", "RMSE", "MAPE",
            "Ljung_Box_p", "Jarque_Bera_p", "mejor_modelo",
        ],
    ].sort_values("RMSE").round(4)
)
display(Image(filename=str(DIR_IMG / "s1_pronosticos.png")))
display(Image(filename=str(DIR_IMG / "s1_rmse_modelos.png")))
display(Image(filename=str(DIR_IMG / "s1_residuos.png")))
"""
    ),
    md(
        """
ARIMA(1,1,1) obtiene el menor RMSE de S1 (38,249). Ljung-Box no rechaza
autocorrelación al 5% (`p=0.074`), pero Jarque-Bera rechaza normalidad por las
colas generadas durante la pandemia.
"""
    ),
    md(
        """
## S2 — Valle Nuevo

Valle Nuevo tiene fuerza de tendencia 0.766 y fuerza estacional 0.311. La
relación media-desviación es más débil (0.310), por lo que se prefiere la
descomposición aditiva. El logaritmo elimina la asociación positiva entre
nivel y amplitud, aunque el choque de 2020 permanece visible.
"""
    ),
    code(
        """
display(Image(filename=str(DIR_IMG / "s2_serie_particion.png")))
display(Image(filename=str(DIR_IMG / "s2_descomposicion.png")))
display(Image(filename=str(DIR_IMG / "s2_varianza.png")))
"""
    ),
    md(
        """
Con `d=1`, ADF y KPSS indican estacionariedad. ACF y PACF muestran una señal
negativa significativa en lag 1, lo que motiva contrastar AR(1), MA(1) y su
combinación antes de agregar la parte estacional.
"""
    ),
    code(
        """
display(
    estacionariedad.loc[
        estacionariedad["serie"] == "S2_valle_nuevo",
        ["transformacion", "p_ADF", "p_KPSS", "veredicto"],
    ].round(4)
)
display(Image(filename=str(DIR_IMG / "s2_acf_pacf.png")))
"""
    ),
    code(
        """
display(
    metricas.loc[
        metricas["serie"] == "S2_valle_nuevo",
        [
            "modelo", "AIC", "BIC", "MAE", "RMSE", "MAPE",
            "Ljung_Box_p", "Jarque_Bera_p", "mejor_modelo",
        ],
    ].sort_values("RMSE").round(4)
)
display(Image(filename=str(DIR_IMG / "s2_pronosticos.png")))
display(Image(filename=str(DIR_IMG / "s2_rmse_modelos.png")))
display(Image(filename=str(DIR_IMG / "s2_residuos.png")))
"""
    ),
    md(
        """
Prophet obtiene el menor RMSE de S2 (23,187), pero sus residuos conservan
autocorrelación. El MAPE supera 100% porque algunos meses observados son muy
pequeños; por eso la selección se basa en RMSE.
"""
    ),
    md(
        """
## S3 — San Cristóbal

San Cristóbal completa el Top 3. Tiene fuerza de tendencia 0.707 y fuerza
estacional 0.399. La correlación media-desviación prepandemia es 0.529, por lo
que se prefiere una lectura multiplicativa; después del logaritmo baja a
-0.468.
"""
    ),
    code(
        """
display(Image(filename=str(DIR_IMG / "s3_serie_particion.png")))
display(Image(filename=str(DIR_IMG / "s3_descomposicion.png")))
display(Image(filename=str(DIR_IMG / "s3_varianza.png")))
"""
    ),
    md(
        """
S3 requiere `d=1,D=1`: la primera diferencia regular no basta según ADF, pero
la combinación regular y estacional obtiene acuerdo con KPSS. La señal
principal de ACF/PACF tras `d=1` está en lag 1; se comparan AR(1), MA(1), su
combinación y un SARIMA anual.
"""
    ),
    code(
        """
display(
    estacionariedad.loc[
        estacionariedad["serie"] == "S3_san_cristobal",
        ["transformacion", "p_ADF", "p_KPSS", "veredicto"],
    ].round(4)
)
display(Image(filename=str(DIR_IMG / "s3_acf_pacf.png")))
"""
    ),
    code(
        """
display(
    metricas.loc[
        metricas["serie"] == "S3_san_cristobal",
        [
            "modelo", "AIC", "BIC", "MAE", "RMSE", "MAPE",
            "Ljung_Box_p", "Jarque_Bera_p", "mejor_modelo",
        ],
    ].sort_values("RMSE").round(4)
)
display(Image(filename=str(DIR_IMG / "s3_pronosticos.png")))
display(Image(filename=str(DIR_IMG / "s3_rmse_modelos.png")))
display(Image(filename=str(DIR_IMG / "s3_residuos.png")))
"""
    ),
    md(
        """
Prophet obtiene el menor RMSE de S3 (10,437). ARIMA(1,1,0), el ARIMA con
menor error, no deja residuos de ruido blanco (`p_Ljung-Box=0.033`) ni
normales (`p_Jarque-Bera<0.001`).
"""
    ),
    md(
        """
## Comparación estadística de Fronteras

La evidencia usa la misma escala y período para las tres series:

- Fuerza estacional sobre la descomposición aditiva del entrenamiento.
- Pendiente de tendencia y CAGR entre 2009 y 2019.
- Coeficiente de variación y desviación de log-diferencias prepandemia.
- Caída anual 2020 vs 2019 y recuperación respecto al promedio de 2019.
"""
    ),
    code(
        """
columnas = [
    "frontera", "fuerza_estacional", "fuerza_tendencia",
    "pendiente_tendencia_relativa_pct_mes", "cagr_2009_2019_pct",
    "coeficiente_variacion_2009_2019",
    "desviacion_log_diferencias_2009_2019",
    "caida_2020_vs_2019_pct",
    "fecha_primera_recuperacion_mensual",
    "meses_primera_recuperacion_mensual",
    "fecha_recuperacion_sostenida_media_movil_2019",
]
display(comparativo[columnas].round(4))
"""
    ),
    md(
        """
### Respuestas

1. **Mayor estacionalidad: La Aurora** (0.559).
2. **Mayor crecimiento relativo: San Cristóbal**, con CAGR 12.95% y pendiente
   relativa mensual 0.984%.
3. **Mayor volatilidad mes a mes: Valle Nuevo**, según la desviación de
   log-diferencias (0.369). San Cristóbal tiene el mayor coeficiente de
   variación (0.522), por lo que es el más disperso respecto a su propio nivel.
4. **Más afectada por la pandemia: Valle Nuevo**, con caída de 80.72% y el
   retorno mensual más tardío al promedio de 2019, en diciembre de 2022.
   Ninguna frontera ha sostenido todavía una media móvil de 12 meses al nivel
   promedio de 2019 hasta junio de 2026.
"""
    ),
    md(
        """
## Conclusión del Bloque B

Las tres series de Fronteras quedaron analizadas con el mismo contrato
metodológico y la misma tabla de resultados. La Aurora es la más estacional,
San Cristóbal crecía más rápido antes de la pandemia y Valle Nuevo muestra la
mayor volatilidad mensual y el mayor impacto pandémico. Ningún algoritmo gana
en todos los puntos de entrada: ARIMA fue mejor en S1 y Prophet en S2 y S3.
"""
    ),
]

nbf.write(nb, SALIDA)
print(f"Notebook creado: {SALIDA}")
