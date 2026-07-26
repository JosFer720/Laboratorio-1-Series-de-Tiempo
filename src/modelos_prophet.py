import logging

import numpy as np
import pandas as pd
from prophet import Prophet

logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


# Convierte una serie con índice de fechas al formato `ds`/`y` que exige Prophet.
def convertir_a_prophet(serie):
    if serie.isna().any():
        raise ValueError("La serie contiene valores faltantes.")
    return pd.DataFrame({"ds": serie.index, "y": serie.to_numpy(dtype=float)})


# Ajusta Prophet únicamente con el período de entrenamiento.
def ajustar_prophet(
    train,
    nombre_serie=None,
    estacionalidad_anual=True,
    modo_estacional="additive",
    crecimiento="linear",
):
    if modo_estacional not in {"additive", "multiplicative"}:
        raise ValueError(
            "modo_estacional debe ser 'additive' o 'multiplicative'."
        )

    datos = convertir_a_prophet(train)
    modelo = Prophet(
        growth=crecimiento,
        yearly_seasonality=estacionalidad_anual,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode=modo_estacional,
        uncertainty_samples=0,
    )
    modelo.fit(datos)

    ajustado = modelo.predict(datos)["yhat"].clip(lower=0).to_numpy()
    residuos = pd.Series(
        train.to_numpy(dtype=float) - ajustado,
        index=train.index,
        name=f"residuos_{nombre_serie or 'serie'}",
    )

    return {
        "serie": nombre_serie or getattr(train, "name", None),
        "modelo": "Prophet",
        "parametros": {
            "crecimiento": crecimiento,
            "estacionalidad_anual": estacionalidad_anual,
            "modo_estacional": modo_estacional,
        },
        "transformacion": "ninguna",
        "AIC": np.nan,
        "BIC": np.nan,
        "ajuste": modelo,
        "residuos": residuos,
    }


# Genera el pronóstico mensual alineado con el índice de prueba solicitado.
def pronosticar_prophet(resultado, horizonte, indice_pronostico):
    if horizonte <= 0:
        raise ValueError("El horizonte debe ser mayor que cero.")
    if len(indice_pronostico) != horizonte:
        raise ValueError(
            "El índice de pronóstico debe tener la misma longitud que el horizonte."
        )
    if "ajuste" not in resultado:
        raise ValueError("El resultado no contiene un modelo ajustado.")

    futuro = pd.DataFrame({"ds": pd.DatetimeIndex(indice_pronostico)})
    pronostico = pd.Series(
        resultado["ajuste"].predict(futuro)["yhat"].clip(lower=0).to_numpy(),
        index=pd.DatetimeIndex(indice_pronostico),
        name=resultado["modelo"],
    )
    return pronostico


# Ajusta y pronostica Prophet con una sola llamada, formato común de resultados.
def ajustar_y_pronosticar_prophet(
    train,
    horizonte,
    indice_pronostico,
    nombre_serie=None,
    estacionalidad_anual=True,
    modo_estacional="additive",
    crecimiento="linear",
):
    resultado = ajustar_prophet(
        train=train,
        nombre_serie=nombre_serie,
        estacionalidad_anual=estacionalidad_anual,
        modo_estacional=modo_estacional,
        crecimiento=crecimiento,
    )
    resultado["pronostico"] = pronosticar_prophet(
        resultado,
        horizonte=horizonte,
        indice_pronostico=indice_pronostico,
    )
    return resultado
