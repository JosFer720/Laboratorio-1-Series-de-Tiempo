# Laboratorio 2 — Deep Learning para Series de Tiempo

**CC3084 · Data Science · Universidad del Valle de Guatemala · Semestre II, 2026**

Predicción del ingreso mensual de viajeros internacionales a Guatemala mediante
redes LSTM y comparación multivariada de siete series de tiempo con
características catch22. El período analizado comprende de enero de 2009 a junio
de 2026.

## Informe final

El análisis completo, la metodología, las figuras, las tablas y la discusión de
resultados se encuentran en el
[`Informe del Laboratorio 2`](<informe/Informe Laboratorio 2. Series de Tiempo con LSTM.pdf>).

## Objetivos del laboratorio

El laboratorio retoma las siete series mensuales preparadas en el Laboratorio 1
y desarrolla dos líneas de trabajo complementarias:

1. Entrenar y comparar redes LSTM para `S0_total` y `S1_la_aurora`, usando una
   partición temporal común y contrastando el mejor resultado con los modelos
   clásicos seleccionados anteriormente.
2. Extraer las 22 características canónicas de catch22 para las siete series y
   analizarlas mediante estandarización, PCA, clustering, correlaciones y
   distancias. Finalmente, se evalúa si estas características mejoran el
   pronóstico LSTM de `S0_total`.

## Resultados principales

| Análisis | Resultado |
|---|---|
| LSTM para `S0_total` | La configuración de dos capas y ventana de 24 meses obtuvo un RMSE de **50,988.18**, frente a **139,548.64** de Prophet. |
| LSTM para `S1_la_aurora` | La misma configuración obtuvo un RMSE de **18,998.20**, frente a **38,249.07** de ARIMA(1,1,1). |
| PCA de catch22 | Los dos primeros componentes explican **68.70%** de la variabilidad estandarizada. |
| Clustering | K-means selecciona **dos grupos**, con silhouette de **0.3303**, y separa a `S6_guatemala` como la serie más atípica. |
| Distancias | `S0_total` y `S2_valle_nuevo` forman el par más cercano, con una distancia de **2.86**. |
| LSTM con catch22 | El modelo enriquecido alcanzó un RMSE de **67,734.70** y no superó al LSTM base de **50,988.18**. |

En ambas series modeladas, la mejor arquitectura fue `LSTM-2capas-w24`, con
ventana de 24 meses, dos capas de 64 unidades, dropout de 0.2, hasta 100 épocas y
lotes de 16 observaciones. La comparación catch22 también muestra que las
categorías administrativas de frontera y país no producen grupos naturales
bien separados: la dinámica temporal de cada serie resulta más informativa que
su etiqueta.

## Datos y diseño experimental

Las series se construyen sobre `Turista + Excursionista`, que conserva una
definición más consistente durante todo el período que la categoría general
`Viajero`. Cada serie contiene 210 observaciones mensuales consecutivas.

| Conjunto | Período | Meses | Proporción |
|---|---|---:|---:|
| Entrenamiento | enero de 2009 a marzo de 2021 | 147 | 70% |
| Prueba | abril de 2021 a junio de 2026 | 63 | 30% |

La partición se realiza sobre el eje temporal, sin barajar observaciones. Los
escaladores se ajustan solamente con entrenamiento y los pronósticos LSTM son
recursivos: después del primer paso, cada predicción se incorpora a la ventana
utilizada para estimar el mes siguiente.

Las siete series analizadas son:

| Identificador | Serie |
|---|---|
| `S0_total` | Total mensual de turistas y excursionistas |
| `S1_la_aurora` | Frontera La Aurora |
| `S2_valle_nuevo` | Frontera Valle Nuevo |
| `S3_san_cristobal` | Frontera San Cristóbal |
| `S4_el_salvador` | País de residencia El Salvador |
| `S5_estados_unidos` | País de residencia Estados Unidos |
| `S6_guatemala` | País de residencia Guatemala |

`S6_guatemala` contiene 42 ceros desde enero de 2023 porque Guatemala deja de
aparecer como país individual después del cambio de granularidad de la fuente.
Por eso, parte de su atipicidad representa un quiebre de registro y no solamente
una diferencia en el comportamiento de los viajeros.

## Estructura del proyecto

```text
.
├── data/
│   ├── raw/                         # fuente original sin modificar
│   └── processed/
│       ├── series/                  # siete series mensuales
│       └── resultados/              # métricas, pronósticos y matrices catch22
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_series_total.ipynb
│   ├── 03_series_fronteras.ipynb
│   ├── 04_modelado_s0_s5.ipynb
│   ├── 04_series_paises.ipynb
│   ├── 05_modelado_s1_s2_s6.ipynb
│   ├── 06_lstm_s0_s1.ipynb          # entrenamiento y comparación LSTM
│   └── 07_catch22.ipynb             # análisis catch22 y LSTM enriquecido
├── src/
│   ├── modelos_lstm.py              # utilidades para crear y evaluar las redes
│   ├── catch22_analysis.py          # extracción y análisis de características
│   └── ...                          # preparación y modelos clásicos heredados
├── informe/
│   ├── Informe Laboratorio 2. Series de Tiempo con LSTM.pdf
│   └── img/                         # figuras generadas por los análisis
├── tests/
├── codebook.md
├── requirements.txt
└── README.md
```

## Cómo reproducir el análisis

Desde la raíz del repositorio, primero se prepara y activa el entorno:

```powershell
python src/00_init.py
.venv\Scripts\activate
```

En macOS, Linux o WSL, la activación equivalente es:

```bash
source .venv/bin/activate
```

El pipeline heredado del Laboratorio 1 reconstruye los datos procesados y las
siete series mensuales:

```powershell
python src/run_pipeline.py
```

Después se ejecutan, en orden, los notebooks propios del Laboratorio 2:

```powershell
python -m jupyter nbconvert --execute --to notebook --inplace `
  --ExecutePreprocessor.timeout=1200 notebooks/06_lstm_s0_s1.ipynb

python -m jupyter nbconvert --execute --to notebook --inplace `
  --ExecutePreprocessor.timeout=1200 notebooks/07_catch22.ipynb
```

El proyecto fija `pycatch22==0.4.5` y utiliza semilla 42 para hacer reproducible
el entrenamiento dentro de las limitaciones de TensorFlow y del hardware
disponible.

## Archivos de resultados

Los principales artefactos reproducibles quedan en
`data/processed/resultados/`:

| Archivo | Contenido |
|---|---|
| `lstm_s0.csv` | métricas de las configuraciones LSTM para `S0_total` |
| `lstm_s1.csv` | métricas de las configuraciones LSTM para `S1_la_aurora` |
| `lstm_catch22_s0.csv` | comparación del LSTM base con el modelo enriquecido |
| `pronostico_lstm_catch22_s0.csv` | pronóstico de prueba del modelo con catch22 |
| `catch22_matriz.csv` | matriz de siete series por 22 características |
| `catch22_matriz_estandarizada.csv` | características utilizadas en el análisis multivariado |
| `catch22_pca_coordenadas.csv` | proyección PCA de las siete series |
| `catch22_pca_cargas.csv` | contribución de las características a los componentes |
| `catch22_clusters.csv` | asignación de clusters |
| `catch22_correlaciones.csv` | correlaciones entre características |
| `catch22_distancias.csv` | distancias euclidianas entre series |

Las figuras finales se encuentran en `informe/img/laboratorio2/` y el documento
de entrega está disponible en
[`informe/Informe Laboratorio 2. Series de Tiempo con LSTM.pdf`](<informe/Informe Laboratorio 2. Series de Tiempo con LSTM.pdf>).
