import pandas as pd

import config
from utils import banner, cargar, guardar, afirmar

banner("ETAPA 3 | CONSTRUCCION DE LAS SERIES")

df = cargar(config.RUTA_LIMPIO, parse_dates=[config.COL_FECHA])

CALENDARIO = pd.date_range(
    df[config.COL_FECHA].min(), df[config.COL_FECHA].max(), freq=config.FRECUENCIA
)
afirmar(len(CALENDARIO) == config.N_MESES, f"el calendario tiene {config.N_MESES} meses")


def construir(datos, columna, valor):
    """Agrega por mes y devuelve una serie alineada al calendario completo."""
    if columna is not None:
        datos = datos[datos[columna] == valor]
    serie = datos.groupby(config.COL_FECHA)["Viajero"].sum()
    return serie.reindex(CALENDARIO, fill_value=0.0)


def exportar(serie, nombre):
    """Guarda una serie como CSV de dos columnas y valida su forma."""
    afirmar(len(serie) == config.N_MESES, f"{nombre}: tiene {config.N_MESES} puntos")
    afirmar(serie.notna().all(), f"{nombre}: no tiene valores faltantes")
    afirmar((serie >= 0).all(), f"{nombre}: no tiene valores negativos")

    salida = serie.rename(config.COL_VALOR).rename_axis(config.COL_FECHA).reset_index()
    guardar(salida, config.DIR_SERIES / f"{nombre}.csv")

visitantes = df[df["Tipo de Viajero"].isin(config.TIPOS_VISITANTE)]
print(f"\n[filtro]   {len(visitantes):>7} de {len(df)} filas son "
      f"{' + '.join(config.TIPOS_VISITANTE)}")

print("\n--- series del analisis ---")
construidas = {}
for nombre, (columna, valor) in config.SERIES.items():
    serie = construir(visitantes, columna, valor)
    construidas[nombre] = serie
    exportar(serie, nombre)

print("\n--- serie auxiliar de contexto ---")
exportar(construir(df, None, None), config.SERIE_CONTEXTO)

print("\n--- validacion cruzada ---")
total = construidas["S0_total"]

todas_fronteras = construir(visitantes, None, None)
afirmar(
    abs(total.sum() - todas_fronteras.sum()) < 1,
    "S0 coincide con el total de visitantes del dataset",
)

for grupo, nombres in [
    ("fronteras", ["S1_la_aurora", "S2_valle_nuevo", "S3_san_cristobal"]),
    ("paises",    ["S4_el_salvador", "S5_estados_unidos", "S6_honduras"]),
]:
    suma = sum(construidas[n] for n in nombres)
    afirmar(
        (suma <= total + 1e-6).all(),
        f"las 3 series de {grupo} nunca superan al total mensual",
    )
    print(f"           {grupo}: {suma.sum():>12,.0f} de {total.sum():,.0f} "
          f"({suma.sum() / total.sum():.1%} del total)")

print("\n--- resumen de las series ---")
print(f"{'serie':22s} {'total':>14s} {'mediana':>11s} {'ceros':>7s}")
for nombre, serie in construidas.items():
    print(f"{nombre:22s} {serie.sum():>14,.0f} {serie.median():>11,.0f} "
          f"{int((serie == 0).sum()):>5}/210")

corte = CALENDARIO[config.N_TRAIN - 1]
print(f"\nParticion 70/30: train hasta {corte:%Y-%m} ({config.N_TRAIN} meses) | "
      f"test desde {CALENDARIO[config.N_TRAIN]:%Y-%m} ({config.N_TEST} meses)")
