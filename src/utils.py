import sys

import pandas as pd


def banner(titulo):
    """Imprime un titulo destacado para separar visualmente cada etapa."""
    print("=" * 60)
    print(titulo)
    print("=" * 60)


def cargar(ruta, **kwargs):
    """Carga un CSV informando de donde viene."""
    df = pd.read_csv(ruta, **kwargs)
    print(f"[cargado]  {ruta.name:28s} -> {df.shape[0]:>7} filas, {df.shape[1]} columnas")
    return df


def guardar(df, ruta):
    """Guarda un CSV informando a donde va."""
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
