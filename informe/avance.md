# Laboratorio 1 — Series de Tiempo: Avance

## 1. Descripción del dataset

El dataset `Base_Migracion_2009-2026jun.xlsx` contiene información sobre el ingreso de viajeros internacionales a Guatemala desde enero de 2009 hasta junio de 2026. En total, cuenta con 161,036 registros distribuidos en 210 meses consecutivos. Los datos fueron proporcionados únicamente con fines académicos y no corresponden a cifras oficiales del INGUAT ni del Instituto Guatemalteco de Migración.

La base de datos está organizada en formato largo, donde cada fila representa una combinación de la fecha, la vía de ingreso, la frontera, el país de residencia y el tipo de viajero. La variable `Viajero` registra la cantidad de personas para cada una de esas combinaciones.

| Variable | Descripción |
|---|---|
| `Año`, `Mes cod`, `Mes` | Fecha del registro |
| `Vía` | Medio de ingreso al país |
| `Frontera` | Puesto fronterizo de ingreso |
| `País` | País de residencia o agrupación de mercado |
| `Región`, `Región dos`, `Regiones OMT`, `MCEO`, `Agrupación Residencia` | Clasificaciones geográficas |
| `Tipo de Viajero` | Turista, Excursionista, Viajero o Cruceristas |
| `Viajero` | Cantidad de viajeros registrados |

## 2. Metodología

Como primer paso se realizó la lectura de la base de datos y se construyó una variable de fecha utilizando el año y el mes de cada registro. Posteriormente se llevó a cabo el proceso de limpieza, donde se unificaron diferentes formas de escribir algunos países, se verificó que no existieran valores nulos y se revisaron los registros repetidos. Aunque se encontraron algunas combinaciones repetidas, estas correspondían a diferencias en la variable `Agrupación Residencia`, por lo que no fue necesario eliminar ningún registro.

Después de la limpieza se construyeron las series de tiempo utilizando únicamente las categorías de Turista y Excursionista, ya que son las que mantienen un criterio consistente durante todo el período de estudio.

Para el análisis se seleccionaron dos categorías: fronteras y países de residencia. En ambos casos se trabajó con las tres categorías que registraron la mayor cantidad de viajeros, ya que permiten analizar tanto los principales puntos de ingreso al país como los mercados de origen con mayor participación.

Finalmente, los datos se dividieron en un conjunto de entrenamiento y otro de prueba utilizando una partición temporal del 70% y 30%, respectivamente.

| Conjunto | Período |
|----------|---------|
| Entrenamiento | Enero 2009 – Marzo 2021 |
| Prueba | Abril 2021 – Junio 2026 |

## 3. Aspectos importantes del dataset

Durante la exploración de la base de datos se identificaron algunas características que debían tomarse en cuenta antes de realizar el análisis.

| Aspecto | Descripción |
|---|---|
| Cambio metodológico en 2023 | A partir de 2023 cambia la forma en que se clasifican los viajeros, por lo que la categoría `Viajero` deja de ser comparable con los años anteriores. |
| Cambio en `País` | Desde 2023 algunos países pasan a registrarse como agrupaciones de mercado. |
| Cruceristas | Se manejan de forma diferente al resto de viajeros, por lo que no se utilizaron en el análisis. |
| Vía marítima | Bajo el filtro utilizado deja de registrar movimiento desde 2017, por lo que no se consideró para el análisis. |
| Valores decimales | La variable `Viajero` contiene estimaciones, por lo que puede presentar valores decimales. |
| Año 2026 | Solo incluye información hasta junio, por lo que no es comparable con años completos. |
| Pandemia | La caída registrada durante 2020 corresponde a un evento real, por lo que esos datos se conservaron. |

## 4. Análisis exploratorio

### 4.a Serie temporal del total mensual

Se puede ver que entre 2009 y 2019 la serie mantiene una tendencia de crecimiento y también presenta un patrón estacional, ya que los valores altos y bajos se repiten aproximadamente cada 12 meses, coincidiendo con las temporadas alta y baja del turismo. En marzo de 2020 ocurre una caída muy fuerte debido al cierre de fronteras por la pandemia y el valor más bajo se registra en mayo de 2020, con 9,779 viajeros, lo que equivale a solo el 2.8% del promedio histórico de 222,438 viajeros.

Después de ese punto, la serie empieza a recuperarse poco a poco durante 2021 y 2022. A partir de 2023 los datos se mantienen en un nivel diferente al que se observaba antes de la pandemia. Esto se debe a un cambio metodológico en el que dejaron de incluir a los compradores fronterizos frecuentes dentro de la categoría de `Viajero`. Sin embargo, como esta serie solo considera Turista y Excursionista, ese cambio tiene un efecto mucho menor que en la serie sin filtrar.

### 4.b Top 10 países de residencia

El Top 3 por número acumulado de viajeros está formado por El Salvador con 14.1 millones, Guatemala con 13.9 millones y Estados Unidos con 7.0 millones. Sin embargo, en el caso de Guatemala esos registros corresponden a residentes guatemaltecos que regresan al país y no a turistas extranjeros. Por esa razón, para el análisis de las series de tiempo no se considera Guatemala y el Top 3 queda conformado por El Salvador, Estados Unidos y Honduras.

También se puede ver que existe una fuerte concentración regional, ya que los cuatro países con mayor cantidad de viajeros son El Salvador, Guatemala, Estados Unidos y Honduras. Esto indica que la mayor parte de los visitantes proviene de Centroamérica y Norteamérica, por lo que el mercado emisor no está muy diversificado.

### 4.c Top regiones

Se puede ver que Centroamérica concentra la mayor cantidad de viajeros, con 33.3 millones, lo que representa alrededor del 71% del total. En segundo lugar se encuentra América del Norte con 9.2 millones de viajeros, equivalente a cerca del 20%. En cambio, el resto de las regiones representan menos del 9% del total.

Estos resultados muestran que la mayor parte del turismo receptivo de Guatemala proviene de países cercanos, especialmente de la región centroamericana.

### 4.d Distribución por vía y frontera

Se puede ver que la vía terrestre concentra la mayor parte de los visitantes, con el 59.2% del total, seguida por la vía aérea con el 40.8%. En cambio, la vía marítima representa apenas el 0.2%, por lo que su participación es muy baja y no se consideró para el análisis.

A nivel de fronteras, La Aurora es el principal punto de ingreso al país con 19.0 millones de viajeros. Después se encuentran Valle Nuevo con 10.1 millones y San Cristóbal con 4.2 millones. Estas tres fronteras fueron seleccionadas para el análisis porque representan dos tipos de ingreso diferentes: el transporte aéreo y el terrestre, lo que permite comparar el comportamiento de ambos perfiles de viajeros.

### 4.e Nulos, duplicados y valores atípicos

No se encontraron valores nulos en la base de datos. Además, se identificaron 22 combinaciones que aparecen repetidas, pero estas no corresponden a duplicados, ya que se diferencian por la variable `Agrupación Residencia`. Por esa razón no fue necesario eliminar ningún registro.

La regla del IQR identificó como valores atípicos los meses comprendidos entre abril y agosto de 2020. Sin embargo, estos valores corresponden a la caída ocasionada por la pandemia, por lo que representan un evento real y se conservaron para el análisis.

### 4.f Estadísticos descriptivos

| Estadístico | Valor |
|---|---:|
| Media | 222,438 |
| Mediana | 227,606 |
| Desviación estándar | 84,725 |
| Mínimo | 9,779 |
| Máximo | 449,114 |

Se puede ver que la media de la serie es de 222,438 viajeros y la mediana es de 227,606, por lo que ambas medidas son bastante similares. Esto indica que la distribución de los datos no presenta una asimetría muy marcada, aunque los valores extremadamente bajos registrados durante la pandemia influyen en la distribución. Además, la desviación estándar es de 84,725 viajeros, lo que muestra una variabilidad importante en la serie.

También se puede ver que la serie que incluye todos los tipos de viajero presenta una caída importante a partir de 2023 debido al cambio metodológico. En cambio, la serie utilizada para el análisis, que solo considera Turista y Excursionista, mantiene un comportamiento consistente durante todo el período.

### 4.g Comportamiento durante y después de la pandemia

Se puede ver que en 2020 el total anual de viajeros disminuyó un 74.4% con respecto a 2019, al pasar de 4.13 millones a 1.06 millones de viajeros. La mayor caída se registró en mayo de 2020, cuando solo ingresaron 9,779 viajeros.

A partir de ese momento la recuperación fue gradual y no fue hasta diciembre de 2022 cuando la serie volvió a alcanzar un nivel similar al observado antes de la pandemia. Además, la partición de los datos utilizada para entrenar y evaluar los modelos se realiza en marzo de 2021, por lo que el conjunto de entrenamiento solo incluye el período de la caída y el inicio de la recuperación. Como consecuencia, es de esperarse que los modelos tengan dificultades para representar el comportamiento de la serie durante el período de recuperación incluido en el conjunto de prueba.
