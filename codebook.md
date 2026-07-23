# Codebook

Diccionario de variables del proyecto. Cubre el dataset crudo, el dataset
limpio que produce el pipeline y las series de tiempo finales.

---

## 1. Dataset crudo — `data/raw/Base_Migracion_2009-2026jun.xlsx`

Registros de ingreso de viajeros internacionales a Guatemala. El archivo trae
dos hojas: `Datos` (los registros) y `Notas` (documentación de la fuente).

**Formato largo:** cada fila es una combinación única de mes, vía, frontera,
país/agrupación y tipo de viajero, con la cantidad de personas en `Viajero`.
No hay filas de total ni doble conteo: las categorías de tipo de viajero son
independientes entre sí.

| Variable | Tipo | Medición | Descripción | Valores / notas |
|---|---|---|---|---|
| `Año` | int | Intervalo | Año de ingreso al país | 2009 – 2026 (2026 solo hasta junio) |
| `Mes cod` | int | Ordinal | Codificación numérica del mes | 1 – 12 |
| `Mes` | str | Ordinal | Nombre abreviado del mes | Ene, Feb, Mar, … |
| `Vía` | str | Nominal | Vía de entrada al país | Aérea, Terrestre, Marítima |
| `Frontera` | str | Nominal | Puesto fronterizo de ingreso | 22 valores, con código numérico como prefijo (ej. `01 La Aurora`) |
| `País` | str | Nominal | País de procedencia (hasta 2022) o agrupación de mercado (desde 2023) | 235 valores distintos en todo el período — ver quiebre §1.1 |
| `Región` | str | Nominal | Clasificación usada para reportes nacionales | ej. EUROPA, OTROS EUROPEOS |
| `Región dos` | str | Nominal | Agrupa varias categorías de `Región` en continentes o grandes áreas | 11 valores (ej. América Del Centro, Europa, Asia) |
| `Regiones OMT` | str | Nominal | Subregión según la Organización Mundial del Turismo | ej. EUROPA MERIDIONAL, ÁFRICA CENTRAL |
| `MCEO` | str | Nominal | Mercado o agrupación comercial estratégica; clasificación de mercados objetivo | ej. `04 EUROPA`, `08 OTROS` |
| `Agrupación Residencia` | str | Nominal | Región donde reside el viajero | ej. Europa, Resto del Mundo |
| `Tipo de Viajero` | str | Nominal | Categoría del viajero según su estadía | Turista, Excursionista, Viajero, Cruceristas |
| `Viajero` | float | Razón | **Medida.** Cantidad de personas | Admite decimales — ver §1.2 |

### 1.1 Definición de `Tipo de Viajero`

| Categoría | Definición | Disponibilidad |
|---|---|---|
| **Turista** | Pernocta al menos una noche en el país | Todo el período |
| **Excursionista** | Visita sin pernoctar (mismo día) | Todo el período |
| **Viajero** | Cruza la frontera sin calificar como visitante: trabajo fronterizo, tránsito, carga, tripulación, comercio de alta frecuencia. **No se contabiliza como visitante** | Todo el período, pero redefinido en 2023 |
| **Cruceristas** | Pasajeros de crucero | **Solo hasta 2022.** Desde 2023 se miden por fuente portuaria externa y no figuran |

### 1.2 Advertencias de la fuente

- **`Viajero` admite decimales.** Son estimaciones expandidas de encuesta, no
  conteos exactos. No se redondean.
- **Quiebre metodológico 2022→2023.** El tramo 2023+ proviene del sistema
  depurado del INGUAT (metodología de boletín): excluye compradores fronterizos
  frecuentes y ajusta arribos marítimos. Por eso `Viajero` baja de ~1.06M (2022)
  a ~0.33M (2023) por reclasificación, no por caída real de turismo.
- **Cambio de granularidad en `País` desde 2023.** De 2009 a 2022 la columna trae
  país individual (226 posibles). Desde 2023 la fuente reporta por agrupación de
  mercado (27 grupos, con etiquetas como *Otros Países de Europa* o *Resto del
  Mundo*). Los mercados principales siguen siendo comparables como serie.
- **`Cruceristas` contamina las columnas `País` y `Región dos`**, donde aparece
  como si fuera un país o una región. Es una categoría de tipo de viajero
  colocada en el nivel equivocado.
- **Vía Marítima pierde detalle desde 2017** por un cambio en el registro.
- **2026 cubre solo enero–junio.**
- Tres tramos de fuente: 2009–2020 respaldos históricos; 2021–2022 entrega del
  IGM con caracterización; 2023–jun 2026 sistema depurado del INGUAT.

---

## 2. Dataset limpio — `data/processed/migracion_limpio.csv`

Generado por `src/01_ingesta.py` → `src/02_limpieza.py`. Conserva las 13
variables del crudo y agrega la columna de fecha.

| Variable | Tipo | Descripción |
|---|---|---|
| `fecha` | datetime64 | **Derivada.** Primer día del mes, construida a partir de `Año` + `Mes cod`. Es el índice temporal de todas las series |
| *(las 13 del crudo)* | | Ver §1 |

### Reglas de limpieza aplicadas

- Se construyó `fecha` como inicio de mes (`MS`) a partir de `Año` y `Mes cod`.
- `Viajero` se tipó a `float` **conservando los decimales** (§1.2).
- Se normalizó el texto de las columnas categóricas (espacios sobrantes y
  capitalización inconsistente).
- Se validó que existan **210 meses consecutivos sin huecos**: un mes faltante
  rompería la descomposición estacional y las pruebas de estacionariedad más
  adelante, y el error aparecería tarde y sin un mensaje claro.
- Los nulos y duplicados se **cuentan y reportan**, no se eliminan a ciegas. El
  tratamiento de cada caso es una decisión de análisis que se documenta en el
  análisis exploratorio, no un supuesto oculto del pipeline.
- `Cruceristas` se **etiqueta** como valor contaminante en `País` y `Región dos`,
  pero no se borra del dataset: se excluye al construir las series de país, y se
  conserva para poder estudiarlo como tipo de viajero.

---

## 3. Series de tiempo — `data/processed/series/*.csv`

Generadas por `src/03_series.py`. Cada archivo tiene el mismo esquema:

| Variable | Tipo | Descripción |
|---|---|---|
| `fecha` | datetime64 | Primer día del mes. 210 valores consecutivos, de 2009-01-01 a 2026-06-01 |
| `viajeros` | float | Suma mensual de `Viajero` para la categoría de la serie |

**Frecuencia:** mensual (`MS`) · **Período estacional:** 12

Todas las series se construyen sobre **`Turista + Excursionista`** (visitantes),
por el quiebre de la categoría `Viajero` descrito en §1.2.

| Archivo | Contenido | Filtro aplicado |
|---|---|---|
| `S0_total.csv` | Total mensual de viajeros internacionales *(serie obligatoria)* | ninguno |
| `S1_aerea.csv` | Ingresos por vía aérea | `Vía = Aérea` |
| `S2_terrestre.csv` | Ingresos por vía terrestre | `Vía = Terrestre` |
| `S3_maritima.csv` | Ingresos por vía marítima | `Vía = Marítima` |
| `S4_el_salvador.csv` | Residentes de El Salvador | `País = El Salvador` |
| `S5_estados_unidos.csv` | Residentes de Estados Unidos | `País = Estados Unidos de América` |
| `S6_honduras.csv` | Residentes de Honduras | `País = Honduras` |
| `S0_total_todos_tipos.csv` | **Auxiliar.** Total con *todos* los tipos de viajero | ninguno (sin filtro de tipo) |

`S0_total_todos_tipos` no es una de las siete series del enunciado. Existe solo
para la gráfica de contexto del análisis exploratorio: muestra el escalón
artificial de 2023 y justifica la decisión de trabajar con visitantes.

### Criterio de selección del Top 3 de países

Basado en el **total acumulado durante todo el período**, como pide el enunciado
(no en un año específico). Por acumulado el Top 3 sería El Salvador, Guatemala y
Estados Unidos, pero **`Guatemala` se excluye**: son residentes guatemaltecos
retornando, no turismo receptivo. Ver la justificación completa en el `README.md`.

### Partición entrenamiento / prueba

Temporal, nunca aleatoria. Definida una sola vez en `src/config.py` (`N_TRAIN`)
para que las siete series se partan de forma idéntica:

| Conjunto | Rango | Meses | Proporción |
|---|---|---|---|
| Entrenamiento | ene 2009 – mar 2021 | 147 | 70% |
| Prueba | abr 2021 – jun 2026 | 63 | 30% |
