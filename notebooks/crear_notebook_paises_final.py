from pathlib import Path

import nbformat as nbf


RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "notebooks" / "04_series_paises.ipynb"


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
# 04 — Análisis completo de Países (S4–S6)

Este cuaderno presenta el análisis final de los tres países
con mayor acumulado de turistas y excursionistas: El Salvador, Estados Unidos
y Guatemala. Aplica la misma plantilla de S0–S3: descomposición,
estacionariedad, selección razonada de órdenes, ARIMA/SARIMA, `auto_arima`,
cuatro modelos alternativos, diagnóstico residual y pronóstico de los 63
meses de prueba.
"""
    ),
    md(
        """
## Advertencia metodológica sobre `País`

De 2009 a 2022 la fuente identifica países individuales; desde 2023 reporta
27 agrupaciones de mercado. Las notas del archivo confirman que **El Salvador
y Estados Unidos continúan como mercados individuales comparables**. Guatemala
deja de aparecer como categoría individual, por lo que sus 42 ceros entre
enero de 2023 y junio de 2026 son un cambio de reporte y no una desaparición
real del retorno de residentes.

Además, el sistema depurado de 2023 excluye o reclasifica algunos movimientos.
Por ello, incluso en los mercados comparables, el salto 2022–2023 combina
cambio real y cambio metodológico.
"""
    ),
    md(
        """
## Metodología común

- Frecuencia mensual (`MS`) y período estacional 12.
- Entrenamiento: enero de 2009 a marzo de 2021 (147 meses).
- Prueba: abril de 2021 a junio de 2026 (63 meses), sin barajar.
- Se usa `log1p` porque S4 y S5 contienen cinco ceros pandémicos y S6 tiene
  ceros posteriores en prueba.
- ADF, KPSS y ACF/PACF determinan `d`; `auto_arima` se contrasta con órdenes
  manuales y no sustituye su explicación.
- Los residuos se revisan con ACF, Ljung-Box, Jarque-Bera y Q-Q.
- El mejor modelo se selecciona por RMSE de prueba, considerando también
  MAE, MAPE, AIC/BIC y los diagnósticos.
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

from modelado_s1_s2_s6 import ejecutar_modelado_paises

resultados, comparativo, tabla_maestra = ejecutar_modelado_paises(
    guardar=True,
    generar_figuras=True,
)
DIR_RESULTADOS = RAIZ / "data" / "processed" / "resultados"
DIR_IMG = RAIZ / "informe" / "img" / "final"
metricas = pd.read_csv(DIR_RESULTADOS / "metricas_paises.csv")
estacionariedad = pd.read_csv(
    DIR_RESULTADOS / "estacionariedad_paises.csv"
)

validacion = pd.DataFrame({
    "serie": list(resultados),
    "meses_total": [len(r["serie"]) for r in resultados.values()],
    "meses_train": [len(r["train"]) for r in resultados.values()],
    "meses_test": [len(r["test"]) for r in resultados.values()],
    "ceros_train": [
        r["resumen"]["ceros_train"] for r in resultados.values()
    ],
    "ceros_test": [
        r["resumen"]["ceros_test"] for r in resultados.values()
    ],
})
validacion
"""
    ),
    md(
        """
## S4 — El Salvador

S4 tiene fuerza de tendencia 0.783 y fuerza estacional 0.402. Los cinco ceros
de abril–agosto de 2020 impiden una descomposición multiplicativa directa, de
modo que se usa la aditiva y `log1p` para estabilizar la varianza. La
correlación media-desviación prepandemia baja de 0.805 a -0.629 después de la
transformación.
"""
    ),
    code(
        """
display(Image(filename=str(DIR_IMG / "s4_serie_particion.png")))
display(Image(filename=str(DIR_IMG / "s4_descomposicion.png")))
display(Image(filename=str(DIR_IMG / "s4_varianza.png")))
"""
    ),
    md(
        """
El nivel original no es estacionario, pero `log1p` obtiene ADF `p<0.001` y
KPSS `p=0.10`; por ello `d=0` es suficiente en la serie transformada. La ACF
decae y la PACF se concentra en lag 1, lo que motiva ARIMA(1,0,0). También se
evalúan candidatos con `d=1`, un SARIMA anual y la propuesta automática
ARIMA(2,0,2).
"""
    ),
    code(
        """
display(
    estacionariedad.loc[
        estacionariedad["serie"] == "S4_el_salvador",
        ["transformacion", "p_ADF", "p_KPSS", "veredicto"],
    ].round(4)
)
display(Image(filename=str(DIR_IMG / "s4_acf_pacf.png")))
"""
    ),
    code(
        """
display(
    metricas.loc[
        metricas["serie"] == "S4_el_salvador",
        [
            "modelo", "AIC", "BIC", "MAE", "RMSE", "MAPE",
            "Ljung_Box_p", "Jarque_Bera_p", "mejor_modelo",
        ],
    ].sort_values("RMSE").round(4)
)
display(Image(filename=str(DIR_IMG / "s4_pronosticos.png")))
display(Image(filename=str(DIR_IMG / "s4_rmse_modelos.png")))
display(Image(filename=str(DIR_IMG / "s4_residuos.png")))
"""
    ),
    md(
        """
Prophet obtiene el menor RMSE de S4 (59,455). Ningún modelo reproduce por
completo la recuperación posterior al piso incluido al final del
entrenamiento. El SARIMA estacional genera pronósticos explosivos pese a su
AIC bajo, evidencia de que AIC/BIC no bastan para elegir un pronóstico.
"""
    ),
    md(
        """
## S5 — Estados Unidos

S5 presenta la mayor fuerza estacional de Países (0.704) y fuerza de tendencia
0.709. Sus cinco ceros pandémicos también obligan a preferir descomposición
aditiva y `log1p`; la correlación media-desviación baja de 0.898 a -0.163.
"""
    ),
    code(
        """
display(Image(filename=str(DIR_IMG / "s5_serie_particion.png")))
display(Image(filename=str(DIR_IMG / "s5_descomposicion.png")))
display(Image(filename=str(DIR_IMG / "s5_varianza.png")))
"""
    ),
    md(
        """
En `log1p` las pruebas son mixtas, pero después de `d=1` ADF y KPSS coinciden
en estacionariedad. Como ACF/PACF no muestran un corte corto inequívoco, se
comparan AR(1), MA(1), ARMA(1,1) y un SARIMA anual.
"""
    ),
    code(
        """
display(
    estacionariedad.loc[
        estacionariedad["serie"] == "S5_estados_unidos",
        ["transformacion", "p_ADF", "p_KPSS", "veredicto"],
    ].round(4)
)
display(Image(filename=str(DIR_IMG / "s5_acf_pacf.png")))
"""
    ),
    code(
        """
display(
    metricas.loc[
        metricas["serie"] == "S5_estados_unidos",
        [
            "modelo", "AIC", "BIC", "MAE", "RMSE", "MAPE",
            "Ljung_Box_p", "Jarque_Bera_p", "mejor_modelo",
        ],
    ].sort_values("RMSE").round(4)
)
display(Image(filename=str(DIR_IMG / "s5_pronosticos.png")))
display(Image(filename=str(DIR_IMG / "s5_rmse_modelos.png")))
display(Image(filename=str(DIR_IMG / "s5_residuos.png")))
"""
    ),
    md(
        """
ARIMA(1,1,1) obtiene el menor RMSE de S5 (26,794). Sus residuos todavía
conservan autocorrelación (`p_Ljung-Box=0.0015`) y no son normales, por lo que
se selecciona como el mejor de los candidatos evaluados, no como un modelo
perfectamente especificado.
"""
    ),
    md(
        """
## S6 — Guatemala

S6 representa principalmente el retorno de residentes guatemaltecos. Tiene
fuerza de tendencia 0.840 y fuerza estacional 0.506 en entrenamiento. La
descomposición multiplicativa es descriptivamente preferida y `log1p` reduce
la correlación media-desviación de 0.830 a -0.592.
"""
    ),
    code(
        """
display(Image(filename=str(DIR_IMG / "s6_serie_particion.png")))
display(Image(filename=str(DIR_IMG / "s6_descomposicion.png")))
display(Image(filename=str(DIR_IMG / "s6_varianza.png")))
"""
    ),
    md(
        """
S6 requiere `d=1`: ADF y KPSS coinciden después de la primera diferencia. La
PACF conserva señal en lag 2 y la ACF en lag 12, por lo que se agrega un
candidato con `p=2` y candidatos SARIMA al contraste de órdenes cortos.
"""
    ),
    code(
        """
display(
    estacionariedad.loc[
        estacionariedad["serie"] == "S6_guatemala",
        ["transformacion", "p_ADF", "p_KPSS", "veredicto"],
    ].round(4)
)
display(Image(filename=str(DIR_IMG / "s6_acf_pacf.png")))
"""
    ),
    code(
        """
display(
    metricas.loc[
        metricas["serie"] == "S6_guatemala",
        [
            "modelo", "AIC", "BIC", "MAE", "RMSE", "MAPE",
            "Ljung_Box_p", "Jarque_Bera_p", "mejor_modelo",
        ],
    ].sort_values("RMSE").round(4)
)
display(Image(filename=str(DIR_IMG / "s6_pronosticos.png")))
display(Image(filename=str(DIR_IMG / "s6_rmse_modelos.png")))
display(Image(filename=str(DIR_IMG / "s6_residuos.png")))
"""
    ),
    md(
        """
SARIMA(1,1,1)(0,1,1,12) obtiene el menor RMSE (47,260) y Ljung-Box no
rechaza ruido blanco al 5% (`p=0.065`). El MAPE usa únicamente los 21 meses
de prueba distintos de cero: los 42 ceros metodológicos no deben interpretarse
como error porcentual de demanda turística.
"""
    ),
    md(
        """
## Comparación estadística de Países

Se emplean exactamente las métricas del comparativo de Fronteras: fuerza
estacional; pendiente y CAGR 2009–2019; coeficiente de variación y desviación
de log-diferencias; caída 2020 vs 2019 y meses de recuperación.
"""
    ),
    code(
        """
columnas = [
    "pais", "fuerza_estacional", "fuerza_tendencia",
    "pendiente_tendencia_relativa_pct_mes", "cagr_2009_2019_pct",
    "coeficiente_variacion_2009_2019",
    "desviacion_log_diferencias_2009_2019",
    "caida_2020_vs_2019_pct",
    "fecha_primera_recuperacion_mensual",
    "fecha_recuperacion_sostenida_media_movil_2019",
]
display(comparativo[columnas].round(4))
"""
    ),
    md(
        """
### Respuestas

1. **Mayor estacionalidad: Estados Unidos** (0.704).
2. **Mayor crecimiento relativo: El Salvador**, con CAGR 11.07% y pendiente
   relativa mensual 0.857%; Guatemala queda cerca, pero no es turismo
   extranjero y pierde comparabilidad desde 2023.
3. **Mayor volatilidad mensual: Estados Unidos**, según log-diferencias
   (0.319). El Salvador tiene el mayor coeficiente de variación (0.419).
4. **Más afectado por la pandemia: El Salvador**, con caída de 79.78%.
   Estados Unidos recupera antes el promedio mensual y la media móvil de
   12 meses. Guatemala no alcanza recuperación sostenida antes de que el
   cambio de granularidad vuelva la serie individual incompleta.
"""
    ),
    md(
        """
## Tabla maestra S0–S6 y verificación de Prophet
"""
    ),
    code(
        """
mejores = tabla_maestra.loc[
    tabla_maestra["mejor_modelo"],
    ["serie", "modelo", "AIC", "BIC", "MAE", "RMSE", "MAPE"],
]
display(mejores.round(4))

cobertura_prophet = (
    tabla_maestra.loc[tabla_maestra["modelo"].eq("Prophet"), "serie"]
    .drop_duplicates()
    .sort_values()
    .tolist()
)
print("Prophet ejecutado en:", ", ".join(cobertura_prophet))
assert len(cobertura_prophet) == 7
"""
    ),
    md(
        """
## Conclusión del análisis de Países

S4–S6 quedaron analizadas con el mismo contrato de las cuatro series
anteriores. Estados Unidos es el mercado más estacional y volátil mes a mes;
El Salvador crecía más rápido y sufrió la mayor caída de 2020. Los resultados
de Guatemala son útiles hasta 2022, pero sus ceros posteriores son una
limitación de granularidad. Prophet corrió en las siete series y no fue
necesario activar un plan alternativo de instalación.
"""
    ),
]

nbf.write(nb, SALIDA)
print(f"Notebook creado: {SALIDA}")
