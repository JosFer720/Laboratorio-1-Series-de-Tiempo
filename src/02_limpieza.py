import unicodedata

import pandas as pd

import config
from utils import banner, cargar, guardar, afirmar, meses_consecutivos

CATEGORICAS = [
    "Mes", "Vía", "Frontera", "País", "Región", "Región dos",
    "Regiones OMT", "MCEO", "Agrupación Residencia", "Tipo de Viajero",
]

# Clave que la fuente declara unica en la hoja "Notas" del crudo.
CLAVE_DECLARADA = ["fecha", "Vía", "Frontera", "País", "Tipo de Viajero"]


def llave_texto(valor):
    """Reduce un texto a su forma comparable: sin tildes, sin case, sin espacios."""
    sin_tildes = unicodedata.normalize("NFKD", str(valor).strip().lower())
    return sin_tildes.encode("ascii", "ignore").decode()


def unificar_variantes(serie):
    frecuencias = serie.value_counts()
    grupos = {}
    for valor in frecuencias.index:
        grupos.setdefault(llave_texto(valor), []).append(valor)

    # value_counts ya viene ordenado de mayor a menor, asi que el primero
    # de cada grupo es el mas frecuente.
    mapeo = {
        variante: variantes[0]
        for variantes in grupos.values() if len(variantes) > 1
        for variante in variantes[1:]
    }
    return serie.replace(mapeo), mapeo


banner("ETAPA 2 | LIMPIEZA Y AUDITORIA")

df = cargar(config.RUTA_INGESTA, parse_dates=[config.COL_FECHA])

afirmar(
    list(df.columns) == [config.COL_FECHA] + config.COLUMNAS_CRUDAS,
    "la entrada trae las columnas esperadas de la etapa 1",
)

filas_entrada = len(df)

print("\n--- valores faltantes ---")
nulos = df.isna().sum()
if nulos.sum() == 0:
    print("[ok]       no hay valores faltantes en ninguna columna")
else:
    print(nulos[nulos > 0].to_string())

print("\n--- normalizacion de texto ---")
for col in CATEGORICAS:
    df[col] = df[col].str.strip()

total_corregidas = 0
for col in CATEGORICAS:
    antes = df[col].nunique()
    df[col], mapeo = unificar_variantes(df[col])
    if mapeo:
        total_corregidas += len(mapeo)
        print(f"[unificado] {col}: {antes} -> {df[col].nunique()} categorias")
        for variante, canonico in mapeo.items():
            print(f"            '{variante}' -> '{canonico}'")

if total_corregidas == 0:
    print("[ok]       no se encontraron variantes de capitalizacion")
else:
    print(f"[ok]       {total_corregidas} variantes unificadas")

print("\n--- duplicados ---")
dup_exactos = df.duplicated().sum()
dup_clave = df.duplicated(subset=CLAVE_DECLARADA).sum()
dup_clave_ext = df.duplicated(subset=CLAVE_DECLARADA + ["Agrupación Residencia"]).sum()

print(f"           filas identicas en todas sus columnas : {dup_exactos}")
print(f"           repiten la clave declarada por la fuente: {dup_clave}")
print(f"           repiten esa clave + Agrupación Residencia: {dup_clave_ext}")

afirmar(dup_exactos == 0, "no hay filas duplicadas exactas")
afirmar(
    dup_clave_ext == 0,
    "la clave real (clave declarada + Agrupación Residencia) es unica: "
    "las repeticiones son desagregaciones, no duplicados",
)

if dup_clave:
    afectadas = df[df.duplicated(subset=CLAVE_DECLARADA, keep=False)]
    anios = sorted(int(a) for a in afectadas[config.COL_FECHA].dt.year.unique())
    print(f"           -> {len(afectadas)} filas afectadas, "
          f"{afectadas['Viajero'].sum():,.0f} viajeros, "
          f"anios {anios}")
    print("           -> se CONSERVAN: borrarlas perderia viajeros reales")

print("\n--- medida (Viajero) ---")
df["Viajero"] = pd.to_numeric(df["Viajero"], errors="coerce")
afirmar(df["Viajero"].notna().all(), "todos los valores de Viajero son numericos")
afirmar((df["Viajero"] >= 0).all(), "no hay cantidades negativas")

decimales = (df["Viajero"] % 1 != 0).sum()
print(f"           rango: {df['Viajero'].min():,.0f} a {df['Viajero'].max():,.0f}")
print(f"           ceros: {(df['Viajero'] == 0).sum()}")
print(f"           con decimales: {decimales} ({decimales / len(df):.1%}) "
      "-> estimaciones expandidas de encuesta, se conservan")

print("\n--- categoria contaminante ---")
for col in ["País", "Región dos"]:
    n = (df[col] == config.VALOR_CONTAMINANTE).sum()
    print(f"           '{config.VALOR_CONTAMINANTE}' aparece en {col}: {n} filas")
print("           -> se excluye al construir series por pais/region (03_series.py)")

print("\n--- validacion de salida ---")
afirmar(len(df) == filas_entrada, f"no se perdio ninguna fila ({filas_entrada})")

continua, faltantes = meses_consecutivos(df[config.COL_FECHA])
afirmar(continua, "los meses siguen siendo consecutivos")
afirmar(df[config.COL_FECHA].nunique() == config.N_MESES,
        f"se conservan los {config.N_MESES} meses")

visitantes = df[df["Tipo de Viajero"].isin(config.TIPOS_VISITANTE)]["Viajero"].sum()
print(f"\nTotal Turista + Excursionista: {visitantes:,.0f} "
      "(base de todas las series)")

guardar(df, config.RUTA_LIMPIO)
