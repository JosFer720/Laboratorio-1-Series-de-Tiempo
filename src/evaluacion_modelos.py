from itertools import cycle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import jarque_bera
from statsmodels.stats.diagnostic import acorr_ljungbox


COLUMNAS_RESULTADOS = [
    "serie",
    "modelo",
    "parametros",
    "transformacion",
    "AIC",
    "BIC",
    "MAE",
    "RMSE",
    "MAPE",
    "Ljung_Box_p",
    "Jarque_Bera_p",
    "mejor_modelo",
]


# Convierte valores e índice a una serie numérica lista para comparar.
def _como_serie(valores, nombre):
    if isinstance(valores, pd.Series):
        serie = valores.astype(float).copy()
    else:
        serie = pd.Series(np.asarray(valores, dtype=float), name=nombre)

    if serie.empty:
        raise ValueError(f"{nombre} no puede estar vacío.")
    if not np.isfinite(serie.to_numpy()).all():
        raise ValueError(f"{nombre} contiene valores faltantes o infinitos.")
    return serie


# Comprueba que observaciones y pronósticos representen los mismos períodos.
def validar_alineacion(y_real, y_pred):
    real = _como_serie(y_real, "y_real")
    pred = _como_serie(y_pred, "y_pred")

    if len(real) != len(pred):
        raise ValueError("y_real y y_pred deben tener la misma longitud.")
    if isinstance(y_real, pd.Series) and isinstance(y_pred, pd.Series):
        if not real.index.equals(pred.index):
            raise ValueError("y_real y y_pred deben tener el mismo índice.")
    return real, pred


# Calcula MAPE ignorando únicamente períodos cuyo valor real es cero.
def calcular_mape_seguro(y_real, y_pred):
    real, pred = validar_alineacion(y_real, y_pred)
    mascara = real.to_numpy() != 0
    if not mascara.any():
        return np.nan
    errores = np.abs(
        (real.to_numpy()[mascara] - pred.to_numpy()[mascara])
        / real.to_numpy()[mascara]
    )
    return float(errores.mean() * 100)


# Resume el error de prueba con las métricas comunes del laboratorio.
def calcular_metricas(y_real, y_pred):
    real, pred = validar_alineacion(y_real, y_pred)
    error = real.to_numpy() - pred.to_numpy()
    return {
        "MAE": float(np.mean(np.abs(error))),
        "RMSE": float(np.sqrt(np.mean(error**2))),
        "MAPE": calcular_mape_seguro(real, pred),
    }


# Resume residuos y comprueba autocorrelación y normalidad.
def diagnosticar_residuos(residuos, lags=12):
    serie = pd.Series(residuos, dtype=float).replace(
        [np.inf, -np.inf], np.nan
    ).dropna()
    if len(serie) < 4:
        raise ValueError("Se necesitan al menos cuatro residuos válidos.")

    rezago = min(int(lags), max(1, len(serie) // 5))
    prueba = acorr_ljungbox(serie, lags=[rezago], return_df=True)
    normalidad = jarque_bera(serie)
    return {
        "n_residuos": int(len(serie)),
        "media_residuos": float(serie.mean()),
        "desviacion_residuos": float(serie.std(ddof=1)),
        "asimetria_residuos": float(serie.skew()),
        "curtosis_exceso_residuos": float(serie.kurt()),
        "Ljung_Box_lag": rezago,
        "Ljung_Box_p": float(prueba["lb_pvalue"].iloc[-1]),
        "Jarque_Bera_p": float(normalidad.pvalue),
    }


# Construye una fila homogénea con métricas, parámetros y diagnóstico.
def construir_resultado(
    serie,
    modelo,
    y_real,
    y_pred,
    parametros=None,
    transformacion="ninguna",
    aic=np.nan,
    bic=np.nan,
    residuos=None,
):
    metricas = calcular_metricas(y_real, y_pred)
    diagnostico = (
        diagnosticar_residuos(residuos)
        if residuos is not None
        else {"Ljung_Box_p": np.nan, "Jarque_Bera_p": np.nan}
    )
    return {
        "serie": serie,
        "modelo": modelo,
        "parametros": parametros or {},
        "transformacion": transformacion,
        "AIC": float(aic) if pd.notna(aic) else np.nan,
        "BIC": float(bic) if pd.notna(bic) else np.nan,
        **metricas,
        "Ljung_Box_p": diagnostico["Ljung_Box_p"],
        "Jarque_Bera_p": diagnostico["Jarque_Bera_p"],
        "mejor_modelo": False,
    }


# Ordena modelos por RMSE y marca el de menor error en cada serie.
def tabla_comparativa(resultados):
    tabla = pd.DataFrame(resultados)
    faltantes = [
        columna for columna in COLUMNAS_RESULTADOS if columna not in tabla
    ]
    for columna in faltantes:
        tabla[columna] = False if columna == "mejor_modelo" else np.nan

    if tabla.empty:
        return tabla[COLUMNAS_RESULTADOS]
    if tabla["RMSE"].isna().any():
        raise ValueError("Todos los modelos deben incluir RMSE.")

    tabla = tabla[COLUMNAS_RESULTADOS].copy()
    tabla["mejor_modelo"] = False
    indices_mejores = tabla.groupby("serie")["RMSE"].idxmin()
    tabla.loc[indices_mejores, "mejor_modelo"] = True
    return tabla.sort_values(
        ["serie", "RMSE", "modelo"], ignore_index=True
    )


# Une archivos de métricas y vuelve a elegir el mejor modelo por serie.
def combinar_metricas(rutas):
    rutas = [Path(ruta) for ruta in rutas]
    if not rutas:
        raise ValueError("Debe indicarse al menos un archivo de métricas.")

    tablas = []
    for ruta in rutas:
        if not ruta.exists():
            raise FileNotFoundError(f"No existe el archivo: {ruta}")
        tablas.append(pd.read_csv(ruta))
    return tabla_comparativa(pd.concat(tablas, ignore_index=True).to_dict("records"))


# Grafica valores reales y pronosticados sobre el mismo índice mensual.
def graficar_real_pronostico(
    y_real,
    pronosticos,
    titulo,
    ruta_salida=None,
):
    real = _como_serie(y_real, "y_real")
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(
        real.index,
        real.values,
        color="#20242b",
        linewidth=2.0,
        label="Observado",
    )

    colores = ["#2f6690", "#c44536", "#6a994e", "#6a4c93", "#d97706"]
    for color, (nombre, valores) in zip(cycle(colores), pronosticos.items()):
        _, pred = validar_alineacion(real, valores)
        ax.plot(
            pred.index,
            pred.values,
            linewidth=1.35,
            color=color,
            label=nombre,
        )

    ax.set_title(titulo)
    ax.set_xlabel("")
    ax.set_ylabel("Viajeros")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()

    if ruta_salida is not None:
        ruta = Path(ruta_salida)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
    return fig, ax
