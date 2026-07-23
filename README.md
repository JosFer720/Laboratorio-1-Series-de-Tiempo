# Laboratorio 1 — Series de Tiempo

**CC3084 · Data Science · Universidad del Valle de Guatemala · Semestre II, 2026**

Análisis y pronóstico del ingreso de viajeros internacionales a Guatemala
(enero 2009 – junio 2026) a partir de los registros mensuales de migración.

> **Nota sobre los datos:** son de **uso exclusivamente académico**. No corresponden
> a cifras oficiales del INGUAT ni del Instituto Guatemalteco de Migración.

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
python src/02_limpieza.py    # tipado, nulos, duplicados, filtro de visitantes
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
   mercados principales (El Salvador, EE.UU., Honduras, México) siguen siendo
   comparables como serie; los países pequeños quedan absorbidos.
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
categorías. Se eligieron **Vías de ingreso** y **Países de residencia (Top 3)**:

- **Vías** da tres series sin ambigüedad de selección y con contrastes fuertes:
  Terrestre domina en volumen, Aérea es la más estacional, y Marítima es
  pequeña, volátil y con un quiebre propio en 2017.
- **Países** es lo más accionable para INGUAT, y los mercados principales se
  mantienen comparables pese al cambio de granularidad de 2023.

### Se excluye `Guatemala` del Top 3 de países

Por volumen acumulado, el Top 3 sería El Salvador (16.2M), **Guatemala (14.8M)**
y Estados Unidos (7.0M). Pero los registros bajo `Guatemala` en la columna `País`
son **residentes guatemaltecos retornando al país**: no son turismo receptivo,
que es el fenómeno que se quiere modelar y sobre el que INGUAT toma decisiones.

Incluirlos mezclaría dos fenómenos con dinámicas distintas (turismo internacional
vs. movilidad de nacionales) en una misma serie. Por eso el Top 3 usado es
**El Salvador, Estados Unidos y Honduras**.

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
| `S1_aerea`, `S2_terrestre`, `S3_maritima` | Por vía de ingreso |
| `S4_el_salvador`, `S5_estados_unidos`, `S6_honduras` | Top 3 países de residencia |

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

## Equipo

| | Responsabilidad |
|---|---|
| Persona A | Pipeline de datos, serie total, integración del informe |
| Persona B | Análisis exploratorio, series de vías de ingreso |
| Persona C | Series de países de residencia, modelos alternativos |
