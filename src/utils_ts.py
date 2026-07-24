import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, kpss

import config

PANDEMIA = ("2020-03-01", "2020-12-01")

def cargar_serie(nombre):
    ruta = config.DIR_SERIES / f"{nombre}.csv"
    if not ruta.exists():
        disponibles = sorted(p.stem for p in config.DIR_SERIES.glob("*.csv"))
        raise FileNotFoundError(
            f"No existe la serie '{nombre}'. Corre `python src/03_series.py`.\n"
            f"Disponibles: {disponibles}"
        )

    df = pd.read_csv(ruta, parse_dates=[config.COL_FECHA])
    serie = df.set_index(config.COL_FECHA)[config.COL_VALOR]
    serie.index.freq = config.FRECUENCIA
    serie.name = nombre
    return serie


def partir_train_test(serie):
    return serie.iloc[:config.N_TRAIN], serie.iloc[config.N_TRAIN:]


# Grafica la serie y resalta el cierre por pandemia.
def graficar_serie(serie, titulo=None, marcar_pandemia=True, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(13, 4))

    ax.plot(serie.index, serie.values, linewidth=1.4)
    if marcar_pandemia:
        ax.axvspan(pd.Timestamp(PANDEMIA[0]), pd.Timestamp(PANDEMIA[1]),
                   alpha=0.15, color="red", label="cierre por pandemia")
        ax.legend(loc="upper left", fontsize=9)

    ax.set_title(titulo or serie.name)
    ax.set_xlabel("")
    ax.set_ylabel("viajeros")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    return ax


def descomponer(serie, modelo="additive", graficar=True):
    if modelo == "multiplicative" and (serie <= 0).any():
        print(f"[aviso] {serie.name}: tiene ceros, no admite descomposicion "
              "multiplicativa. Se usa aditiva.")
        modelo = "additive"

    resultado = seasonal_decompose(serie, model=modelo,
                                   period=config.PERIODO_ESTACIONAL)
    if graficar:
        fig = resultado.plot()
        fig.set_size_inches(13, 8)
        fig.suptitle(f"{serie.name} — descomposicion {modelo}", y=1.01)
        plt.tight_layout()
    return resultado


def fuerza_estacional(resultado):
    resid = resultado.resid.dropna()
    estacional = resultado.seasonal.loc[resid.index]
    return max(0.0, 1 - resid.var() / (resid + estacional).var())


def fuerza_tendencia(resultado):
    resid = resultado.resid.dropna()
    tendencia = resultado.trend.loc[resid.index]
    return max(0.0, 1 - resid.var() / (resid + tendencia).var())


def test_estacionariedad(serie, nombre=None, verbose=True):
    serie = serie.dropna()
    nombre = nombre or serie.name

    adf = adfuller(serie, autolag="AIC")
    kpss_stat, kpss_p, *_ = kpss(serie, regression="c", nlags="auto")

    adf_estacionaria = adf[1] < 0.05
    kpss_estacionaria = kpss_p >= 0.05

    if adf_estacionaria and kpss_estacionaria:
        veredicto = "estacionaria (ambas pruebas coinciden)"
    elif not adf_estacionaria and not kpss_estacionaria:
        veredicto = "NO estacionaria (ambas pruebas coinciden)"
    elif adf_estacionaria:
        veredicto = "resultado mixto: ADF dice estacionaria, KPSS no"
    else:
        veredicto = "resultado mixto: KPSS dice estacionaria, ADF no"

    resultado = {
        "serie": nombre,
        "adf_estadistico": adf[0], "adf_p": adf[1],
        "adf_rezagos": adf[2], "adf_observaciones": adf[3],
        "adf_valores_criticos": adf[4],
        "kpss_estadistico": kpss_stat, "kpss_p": kpss_p,
        "adf_estacionaria": adf_estacionaria,
        "kpss_estacionaria": kpss_estacionaria,
        "veredicto": veredicto,
    }

    if verbose:
        print(f"--- estacionariedad: {nombre} ---")
        print(f"  ADF : estadistico={adf[0]:>8.4f}  p={adf[1]:.4f}  "
              f"rezagos={adf[2]}  "
              f"-> {'estacionaria' if adf_estacionaria else 'NO estacionaria'}")
        print(f"  KPSS: estadistico={kpss_stat:>8.4f}  p={kpss_p:.4f}  "
              f"-> {'estacionaria' if kpss_estacionaria else 'NO estacionaria'}")
        print(f"  => {veredicto}")

    return resultado


def graficar_acf_pacf(serie, lags=36):
    serie = serie.dropna()
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    plot_acf(serie, lags=lags, ax=axes[0])
    plot_pacf(serie, lags=lags, ax=axes[1], method="ywm")
    axes[0].set_title(f"ACF — {serie.name}  (sugiere q)")
    axes[1].set_title(f"PACF — {serie.name}  (sugiere p)")
    plt.tight_layout()
    return axes


def evaluar_modelo(y_real, y_pred):
    y_real = np.asarray(y_real, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    error = y_real - y_pred
    mae = np.mean(np.abs(error))
    rmse = np.sqrt(np.mean(error ** 2))
    mape = (np.mean(np.abs(error / y_real)) * 100
            if (y_real != 0).all() else np.nan)

    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


def tabla_comparativa(modelos, serie=None):
    COLUMNAS = ["serie", "modelo", "AIC", "BIC", "MAE", "RMSE", "MAPE"]

    filas = []
    for nombre, metricas in modelos.items():
        fila = {"serie": serie, "modelo": nombre}
        fila.update({c: metricas.get(c, np.nan) for c in COLUMNAS[2:]})
        filas.append(fila)

    return (pd.DataFrame(filas, columns=COLUMNAS)
            .sort_values("RMSE")
            .reset_index(drop=True))
