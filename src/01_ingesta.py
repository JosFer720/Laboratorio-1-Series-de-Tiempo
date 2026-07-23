import pandas as pd

import config
from utils import banner, guardar, afirmar, meses_consecutivos

banner("ETAPA 1 | INGESTA DEL CRUDO")

print(f"[leyendo]  {config.RUTA_CRUDA.name} (hoja '{config.HOJA_DATOS}')")
print("           son ~118 MB de XML, puede tardar 1-2 minutos ...")
df = pd.read_excel(config.RUTA_CRUDA, sheet_name=config.HOJA_DATOS, engine="openpyxl")
print(f"[cargado]  {df.shape[0]:>7} filas, {df.shape[1]} columnas")

afirmar(
    list(df.columns) == config.COLUMNAS_CRUDAS,
    "el crudo trae exactamente las columnas esperadas",
)
afirmar(
    len(df) == config.N_FILAS_CRUDAS,
    f"el crudo trae {config.N_FILAS_CRUDAS} registros",
)
afirmar(
    df["Mes cod"].between(1, 12).all(),
    "todos los codigos de mes estan entre 1 y 12",
)

df.insert(0, config.COL_FECHA, pd.to_datetime(
    {"year": df["Año"], "month": df["Mes cod"], "day": 1}
))

continua, faltantes = meses_consecutivos(df[config.COL_FECHA])
afirmar(continua, f"los meses son consecutivos, sin huecos (faltarian: {list(faltantes)})")

n_meses = df[config.COL_FECHA].nunique()
afirmar(
    n_meses == config.N_MESES,
    f"hay {config.N_MESES} meses distintos (encontrados: {n_meses})",
)

print(f"\nCobertura: {df[config.COL_FECHA].min():%Y-%m} a {df[config.COL_FECHA].max():%Y-%m}")

guardar(df, config.RUTA_INGESTA)
