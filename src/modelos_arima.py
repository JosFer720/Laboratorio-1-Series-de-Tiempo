import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX


TRANSFORMACIONES = {"ninguna", "log", "log1p"}


# Valida y transforma una serie sin modificar su índice temporal.
def transformar_serie(serie, transformacion="ninguna"):
    if transformacion not in TRANSFORMACIONES:
        raise ValueError(
            f"Transformación no válida: {transformacion}. "
            f"Use una de {sorted(TRANSFORMACIONES)}."
        )

    valores = pd.Series(serie, index=serie.index, dtype=float, name=serie.name)
    if valores.isna().any():
        raise ValueError("La serie contiene valores faltantes.")

    if transformacion == "log":
        if (valores <= 0).any():
            raise ValueError("La transformación log requiere valores positivos.")
        return np.log(valores)

    if transformacion == "log1p":
        if (valores < 0).any():
            raise ValueError("La transformación log1p no admite valores negativos.")
        return np.log1p(valores)

    return valores.copy()


# Devuelve los pronósticos a la escala original y evita valores negativos.
def invertir_transformacion(valores, transformacion="ninguna", indice=None):
    if transformacion not in TRANSFORMACIONES:
        raise ValueError(
            f"Transformación no válida: {transformacion}. "
            f"Use una de {sorted(TRANSFORMACIONES)}."
        )

    indice_salida = indice
    if indice_salida is None and hasattr(valores, "index"):
        indice_salida = valores.index

    salida = pd.Series(np.asarray(valores, dtype=float))
    if transformacion == "log":
        salida = np.exp(salida)
    elif transformacion == "log1p":
        salida = np.expm1(salida)

    salida = salida.clip(lower=0.0)
    if indice_salida is not None:
        if len(indice_salida) != len(salida):
            raise ValueError("El índice no coincide con el horizonte pronosticado.")
        salida.index = pd.DatetimeIndex(indice_salida)
    return salida


# Crea una etiqueta uniforme para candidatos ARIMA y SARIMA.
def nombre_modelo(orden, orden_estacional=(0, 0, 0, 0)):
    etiqueta = f"ARIMA{tuple(orden)}"
    if tuple(orden_estacional) != (0, 0, 0, 0):
        etiqueta = f"SARIMA{tuple(orden)}x{tuple(orden_estacional)}"
    return etiqueta


# Ajusta un candidato y devuelve métricas, residuos y el objeto entrenado.
def ajustar_arima(
    train,
    orden,
    orden_estacional=(0, 0, 0, 0),
    transformacion="ninguna",
    tendencia=None,
    nombre_serie=None,
):
    orden = tuple(orden)
    orden_estacional = tuple(orden_estacional)
    if len(orden) != 3:
        raise ValueError("El orden ARIMA debe contener (p, d, q).")
    if len(orden_estacional) != 4:
        raise ValueError("El orden estacional debe contener (P, D, Q, m).")

    train_transformado = transformar_serie(train, transformacion)
    modelo = SARIMAX(
        train_transformado,
        order=orden,
        seasonal_order=orden_estacional,
        trend=tendencia,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ajuste = modelo.fit(disp=False)

    etiqueta = nombre_modelo(orden, orden_estacional)
    serie_nombre = nombre_serie or getattr(train, "name", None)
    residuos = pd.Series(
        ajuste.resid,
        index=train_transformado.index,
        name=f"residuos_{serie_nombre or 'serie'}",
    )
    burn_in = int(getattr(ajuste, "loglikelihood_burn", 0))
    if burn_in:
        residuos = residuos.iloc[burn_in:].copy()

    return {
        "serie": serie_nombre,
        "modelo": etiqueta,
        "parametros": {
            "orden": orden,
            "orden_estacional": orden_estacional,
            "tendencia": tendencia,
        },
        "transformacion": transformacion,
        "AIC": float(ajuste.aic),
        "BIC": float(ajuste.bic),
        "ajuste": ajuste,
        "residuos": residuos,
    }


# Genera un pronóstico en la escala original para un resultado ya ajustado.
def pronosticar_arima(resultado, horizonte, indice=None):
    if horizonte <= 0:
        raise ValueError("El horizonte debe ser mayor que cero.")
    if "ajuste" not in resultado:
        raise ValueError("El resultado no contiene un modelo ajustado.")

    pronostico_transformado = resultado["ajuste"].get_forecast(
        steps=horizonte
    ).predicted_mean
    pronostico = invertir_transformacion(
        pronostico_transformado,
        resultado["transformacion"],
        indice=indice,
    )
    pronostico.name = resultado["modelo"]
    return pronostico


# Ajusta y pronostica un candidato con una sola llamada.
def ajustar_y_pronosticar_arima(
    train,
    orden,
    horizonte,
    indice_pronostico=None,
    orden_estacional=(0, 0, 0, 0),
    transformacion="ninguna",
    tendencia=None,
    nombre_serie=None,
):
    resultado = ajustar_arima(
        train=train,
        orden=orden,
        orden_estacional=orden_estacional,
        transformacion=transformacion,
        tendencia=tendencia,
        nombre_serie=nombre_serie,
    )
    resultado["pronostico"] = pronosticar_arima(
        resultado,
        horizonte=horizonte,
        indice=indice_pronostico,
    )
    return resultado


# Ejecuta una lista pequeña de candidatos definidos por orden y estacionalidad.
def ajustar_candidatos_arima(
    train,
    candidatos,
    horizonte,
    indice_pronostico=None,
    transformacion="ninguna",
    nombre_serie=None,
    continuar_si_falla=True,
):
    resultados = []
    for candidato in candidatos:
        try:
            resultado = ajustar_y_pronosticar_arima(
                train=train,
                orden=candidato["orden"],
                orden_estacional=candidato.get(
                    "orden_estacional", (0, 0, 0, 0)
                ),
                horizonte=horizonte,
                indice_pronostico=indice_pronostico,
                transformacion=candidato.get(
                    "transformacion", transformacion
                ),
                tendencia=candidato.get("tendencia"),
                nombre_serie=nombre_serie,
            )
            if candidato.get("nombre"):
                resultado["modelo"] = candidato["nombre"]
                resultado["pronostico"].name = candidato["nombre"]
            resultados.append(resultado)
        except Exception as error:
            if not continuar_si_falla:
                raise
            resultados.append(
                {
                    "serie": nombre_serie or getattr(train, "name", None),
                    "modelo": candidato.get(
                        "nombre",
                        nombre_modelo(
                            candidato["orden"],
                            candidato.get(
                                "orden_estacional", (0, 0, 0, 0)
                            ),
                        ),
                    ),
                    "parametros": candidato,
                    "transformacion": candidato.get(
                        "transformacion", transformacion
                    ),
                    "AIC": np.nan,
                    "BIC": np.nan,
                    "error": str(error),
                }
            )
    return resultados


# Resume los candidatos sin incluir objetos pesados del ajuste.
def tabla_candidatos_arima(resultados):
    filas = []
    for resultado in resultados:
        filas.append(
            {
                "serie": resultado.get("serie"),
                "modelo": resultado.get("modelo"),
                "parametros": resultado.get("parametros"),
                "transformacion": resultado.get("transformacion"),
                "AIC": resultado.get("AIC", np.nan),
                "BIC": resultado.get("BIC", np.nan),
                "error": resultado.get("error"),
            }
        )
    return pd.DataFrame(filas).sort_values(
        ["error", "AIC"],
        na_position="last",
        ignore_index=True,
    )


# Obtiene una sugerencia automática que debe contrastarse con ACF y PACF.
def sugerir_auto_arima(
    train,
    transformacion="ninguna",
    estacional=True,
    periodo=12,
    max_p=3,
    max_q=3,
    max_P=2,
    max_Q=2,
):
    from pmdarima import auto_arima

    train_transformado = transformar_serie(train, transformacion)
    ajuste = auto_arima(
        train_transformado,
        seasonal=estacional,
        m=periodo if estacional else 1,
        start_p=0,
        start_q=0,
        max_p=max_p,
        max_q=max_q,
        start_P=0,
        start_Q=0,
        max_P=max_P,
        max_Q=max_Q,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore",
        trace=False,
    )
    return {
        "orden": tuple(ajuste.order),
        "orden_estacional": tuple(ajuste.seasonal_order),
        "AIC": float(ajuste.aic()),
        "BIC": float(ajuste.bic()),
        "transformacion": transformacion,
        "ajuste": ajuste,
    }
