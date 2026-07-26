# Laboratorio 1 — Series de Tiempo

**CC3084 · Data Science · Universidad del Valle de Guatemala · Semestre II, 2026**

Análisis y pronóstico del ingreso de viajeros internacionales a Guatemala
(enero 2009 – junio 2026) a partir de los registros mensuales de migración.

## Estructura del proyecto

```
.
├── data/
│   ├── raw/                  # datos crudos (fuente de verdad, nunca se modifican)
│   │   └── Base_Migracion_2009-2026jun.xlsx
│   └── processed/            # datos generados por el pipeline (reproducibles)
│       └── series/           # las series mensuales finales (esto SÍ se versiona)
├── notebooks/                # cuadernos de análisis
├── src/                      # pipeline de datos y utilidades
├── informe/                  # informe del avance y el informe final
├── codebook.md               # diccionario de variables
├── requirements.txt          # dependencias
└── README.md
```

## Cómo correrlo

**1. Preparar el entorno** (una sola vez). Se corre con el python del sistema;
crea `.venv/` e instala las dependencias:

```
python src/00_init.py
```

**2. Activar el entorno** (una vez por terminal):

```
source .venv/bin/activate        # macOS / Linux / WSL
.venv\Scripts\activate           # Windows
```

**3. Correr el pipeline completo:**

```
python src/run_pipeline.py
```

O una etapa a la vez (cada script es independiente):

```
python src/01_ingesta.py     # .xlsx -> CSV con columna de fecha
python src/02_limpieza.py    # tipado, normalización, reporte de nulos y duplicados
python src/03_series.py      # construye y exporta las series mensuales
```

Siempre desde la raíz del proyecto, con el entorno activado.

> **Si `python src/00_init.py` falla al crear el entorno:** en Debian/Ubuntu/WSL
> el módulo `venv` viene incompleto (falta `ensurepip`). El script lo detecta y
> cae automáticamente a `virtualenv`. Si aun así falla, instálalo a mano con
> `pip install --user virtualenv`.

## El conjunto de datos

| | |
|---|---|
| **Cobertura** | enero 2009 – junio 2026 · **210 meses consecutivos, sin huecos** |
| **Registros** | 161,036 |
| **Formato** | largo — una fila por combinación de mes, vía, frontera, país y tipo de viajero |
| **Medida** | `Viajero` (cantidad de personas) |

Ver [`codebook.md`](codebook.md) para la definición de cada variable.

### Quiebres conocidos de la fuente

El dataset combina tres tramos de origen distinto, y eso deja costuras que
condicionan todo el análisis:

1. **Quiebre metodológico 2022→2023.** Desde 2023 la fuente es el sistema
   depurado del INGUAT, que excluye compradores fronterizos frecuentes. La
   categoría `Viajero` cae de ~1.06M a ~0.33M por reclasificación, **no** por
   una caída real de turismo.
2. **Cambio de granularidad en `País` desde 2023.** Hasta 2022 se reporta país
   individual (226 valores); desde 2023, agrupación de mercado (27 grupos). Los
   nombres principales no siempre se conservan: Guatemala deja de aparecer
   como categoría individual desde enero de 2023 y su serie queda en cero. Los
   países pequeños también pueden quedar absorbidos en grupos de mercado.
3. **Vía Marítima pierde detalle desde 2017** por un cambio de registro.
4. **Cruceristas solo existe hasta 2022**; desde 2023 se miden por fuente
   portuaria externa y no figuran.
5. **`Viajero` tiene decimales**: son estimaciones expandidas de encuesta, no
   conteos exactos.
6. **2026 cubre solo enero–junio**, así que su total anual no es comparable con
   el de años completos.
7. **Pandemia:** colapso en marzo 2020 y piso durante 2020–2021 (~27% de 2019),
   con recuperación en 2022.

## Decisiones de análisis

Las tres decisiones que condicionan cómo se construyen las series. Viven en
`src/config.py` para que apliquen igual en todo el proyecto.

### Categorías analizadas

Además de la serie obligatoria (total mensual), el enunciado pide elegir dos
categorías. Se eligieron **Fronteras (Top 3)** y **Países de residencia (Top 3)**:

- **Fronteras** conserva el contraste entre vía aérea y vía terrestre —La Aurora
  es el aeropuerto internacional, Valle Nuevo y San Cristóbal son puestos
  terrestres— y las tres series están completas: **ningún mes vacío en los 210**.
  Es además directamente accionable: indica dónde invertir en capacidad e
  infraestructura de atención.
- **Países** permite seguir los principales lugares de residencia. El cambio de
  granularidad de 2023 se documenta por separado porque afecta especialmente a
  Guatemala.

Las dos categorías son **ortogonales**: una mide *de dónde vienen* los viajeros
y la otra *por dónde entran*. Eso evita que ambas respondan la misma pregunta y
enriquece el análisis comparativo.

#### Por qué no se usó "Vías de ingreso"

Fue la primera opción, pero **no es viable junto con el filtro de visitantes**.
Al quedarse solo con Turista + Excursionista, la serie **Marítima vale cero
exacto desde 2017**: 114 de los 210 meses en cero.

La causa está en la fuente: desde 2017 los arribos marítimos se registran casi
exclusivamente como *Cruceristas*, que no son visitantes bajo el criterio de D3
y que además desaparecen del dataset a partir de 2023. Una serie con diez años
consecutivos de ceros no admite descomposición, prueba de Dickey-Fuller ni
modelado ARIMA, así que la categoría se descartó y se documentó el hallazgo.

### Top 3 literal y caso especial de `Guatemala`

Por volumen acumulado sobre Turista + Excursionista, el Top 3 es El Salvador
(14.1M), **Guatemala (13.9M)** y Estados Unidos (7.0M). Para seguir
literalmente el criterio del enunciado,
estas son las tres series de la categoría Países. No obstante, los registros
bajo `Guatemala` corresponden principalmente a **residentes guatemaltecos que
regresan al país**, por lo que se analizan como movilidad de retorno y no como
turismo extranjero. Además, Guatemala deja de aparecer como categoría
individual desde enero de 2023, por lo que S6 tiene 42 meses consecutivos en
cero hasta junio de 2026. Ese tramo es un quiebre de registro, no una
desaparición real del movimiento de residentes.

### Las series se construyen sobre `Turista + Excursionista`

El enunciado lo indica explícitamente: entre 2022 y 2023 la categoría `Viajero`
se redefine para excluir viajeros no turísticos de alta frecuencia, y cae de
forma artificial. **Turista + Excursionista** es la única combinación consistente
en todo el período, y es además la definición de *visitante* que usa la OMT.

La serie con todos los tipos se conserva aparte (`S0_total_todos_tipos`) solo
como gráfica de contexto en el análisis exploratorio, para mostrar el escalón
artificial de 2023 y justificar esta decisión.

## Las series construidas

Siete series mensuales (`MS`, período estacional 12), de enero 2009 a junio 2026:

| Archivo | Serie |
|---|---|
| `S0_total` | Total mensual de viajeros internacionales *(obligatoria)* |
| `S1_la_aurora`, `S2_valle_nuevo`, `S3_san_cristobal` | Top 3 fronteras de ingreso |
| `S4_el_salvador`, `S5_estados_unidos`, `S6_guatemala` | Top 3 países de residencia |

### Partición entrenamiento / prueba

Siguiendo la instrucción de ~70/30 **sobre el eje temporal** (nunca aleatoria,
porque barajar filtraría información del futuro hacia el pasado):

```
TRAIN: ene 2009 – mar 2021   (147 meses, 70%)
TEST : abr 2021 – jun 2026   ( 63 meses, 30%)
```

> Este corte deja el entrenamiento terminando en el piso de la pandemia y el
> conjunto de prueba cubriendo íntegramente la recuperación. Es consecuencia
> directa de aplicar la proporción pedida sobre este período, y se analiza
> explícitamente en el informe.

## Modelado reproducible

Los módulos comparan ARIMA/SARIMA, Prophet, Holt-Winters, suavizamiento
exponencial simple y Seasonal Naive. S1–S3 forman el análisis de Fronteras y
S4–S6 el análisis de Países; ambas categorías usan el mismo comparativo
estadístico.

Desde la raíz del proyecto, en macOS/Linux/WSL:

```bash
MPLCONFIGDIR=/tmp/matplotlib PYTHONPATH=src \
  .venv/bin/python src/modelado_s0_s5.py

MPLCONFIGDIR=/tmp/matplotlib PYTHONPATH=src \
  .venv/bin/python src/modelado_fronteras.py

MPLCONFIGDIR=/tmp/matplotlib PYTHONPATH=src \
  .venv/bin/python src/modelado_paises.py

MPLCONFIGDIR=/tmp/matplotlib PYTHONPATH=src \
  .venv/bin/python -m nbconvert --execute --to notebook --inplace \
  --ExecutePreprocessor.timeout=600 notebooks/03_series_fronteras.ipynb

MPLCONFIGDIR=/tmp/matplotlib PYTHONPATH=src \
  .venv/bin/python -m nbconvert --execute --to notebook --inplace \
  --ExecutePreprocessor.timeout=600 notebooks/04_series_paises.ipynb
```

En PowerShell de Windows, con el entorno activado:

```powershell
$env:PYTHONPATH = "src"
$env:MPLCONFIGDIR = Join-Path $env:TEMP "lab1-matplotlib"
python src/modelado_s0_s5.py
python src/modelado_fronteras.py
python src/modelado_paises.py
python -m nbconvert --execute --to notebook --inplace `
  --ExecutePreprocessor.timeout=600 notebooks/03_series_fronteras.ipynb
python -m nbconvert --execute --to notebook --inplace `
  --ExecutePreprocessor.timeout=600 notebooks/04_series_paises.ipynb
```

Las pruebas completas se ejecutan con:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Los resultados quedan en `data/processed/resultados/`, las figuras en
`informe/img/final/` y el análisis narrativo en `informe/informe_final.md`.
Para Fronteras, los archivos principales son `metricas_fronteras.csv`,
`estacionariedad_fronteras.csv`, `pronosticos_fronteras.csv`,
`comparativo_fronteras.csv` y `resumen_fronteras.json`.
Para Países se generan los cinco archivos equivalentes con sufijo `_paises`,
además de `metricas_maestras.csv`, que consolida los 64 ajustes de S0–S6 sin
duplicar S5.
