import sys

import pandas as pd


# Muestra el encabezado de cada etapa.
def banner(titulo):
    print("=" * 60)
    print(titulo)
    print("=" * 60)


# Carga un CSV y muestra sus dimensiones.
def cargar(ruta, **kwargs):
    df = pd.read_csv(ruta, **kwargs)
    print(f"[cargado]  {ruta.name:28s} -> {df.shape[0]:>7} filas, {df.shape[1]} columnas")
    return df


# Guarda un CSV y muestra sus dimensiones.
def guardar(df, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False)
    print(f"[guardado] {ruta.name:28s} <- {df.shape[0]:>7} filas, {df.shape[1]} columnas")


def afirmar(condicion, mensaje):
    if condicion:
        print(f"[ok]       {mensaje}")
    else:
        print(f"[FALLO]    {mensaje}")
        sys.exit(1)


def meses_consecutivos(fechas):
    unicas = pd.DatetimeIndex(sorted(pd.unique(fechas)))
    esperadas = pd.date_range(unicas.min(), unicas.max(), freq="MS")
    faltantes = esperadas.difference(unicas)
    return len(faltantes) == 0, faltantes
