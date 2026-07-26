import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.gofplots import qqplot
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose

import config
from evaluacion_modelos import (
    construir_resultado,
    diagnosticar_residuos,
    graficar_real_pronostico,
    tabla_comparativa,
)
from modelos_arima import (
    ajustar_candidatos_arima,
    sugerir_auto_arima,
    transformar_serie,
)
from modelos_prophet import ajustar_y_pronosticar_prophet
from utils_ts import (
    cargar_serie,
    fuerza_estacional,
    fuerza_tendencia,
    partir_train_test,
    test_estacionariedad,
)


DIR_RESULTADOS = config.DIR_RESULTADOS
DIR_IMG = config.RAIZ / "informe" / "img" / "final"

ESPECIFICACIONES = {
    "S1_la_aurora": {
        "etiqueta": "S1 — La Aurora",
        "transformacion": "log",
        "archivo": "s1",
    },
    "S2_valle_nuevo": {
        "etiqueta": "S2 — Valle Nuevo",
        "transformacion": "log",
        "archivo": "s2",
    },
    "S3_san_cristobal": {
        "etiqueta": "S3 — San Cristóbal",
        "transformacion": "log",
        "archivo": "s3",
    },
    "S6_guatemala": {
        "etiqueta": "S6 — Guatemala",
        "transformacion": "log1p",
        "archivo": "s6",
    },
}

ARIMA_110 = {
    "nombre": "ARIMA(1,1,0)",
    "orden": (1, 1, 0),
    "orden_estacional": (0, 0, 0, 0),
}
ARIMA_011 = {
    "nombre": "ARIMA(0,1,1)",
    "orden": (0, 1, 1),
    "orden_estacional": (0, 0, 0, 0),
}
ARIMA_111 = {
    "nombre": "ARIMA(1,1,1)",
    "orden": (1, 1, 1),
    "orden_estacional": (0, 0, 0, 0),
}
SARIMA_111_011 = {
    "nombre": "SARIMA(1,1,1)(0,1,1,12)",
    "orden": (1, 1, 1),
    "orden_estacional": (0, 1, 1, 12),
}
SARIMA_211_110 = {
    "nombre": "SARIMA(2,1,1)(1,1,0,12)",
    "orden": (2, 1, 1),
    "orden_estacional": (1, 1, 0, 12),
}

CANDIDATOS_POR_SERIE = {
    "S1_la_aurora": [ARIMA_110, ARIMA_011, ARIMA_111, SARIMA_111_011],
    "S2_valle_nuevo": [ARIMA_110, ARIMA_011, ARIMA_111, SARIMA_111_011],
    "S3_san_cristobal": [ARIMA_110, ARIMA_011, ARIMA_111, SARIMA_111_011],
    "S6_guatemala": [ARIMA_111, SARIMA_111_011, SARIMA_211_110],
}

RAZONAMIENTO_ORDENES = {
    "S1_la_aurora": (
        "Tras d=1 no hay un corte limpio en el primer rezago; ACF y PACF "
        "conservan picos aislados en 5 y 7 por el choque pandémico. Se "
        "comparan p,q bajos (1,0), (0,1) y (1,1), más un SARIMA anual."
    ),
    "S2_valle_nuevo": (
        "Tras d=1, ACF y PACF muestran un pico negativo significativo en "
        "lag 1. Se contrastan ARIMA(1,1,0), ARIMA(0,1,1) y ARIMA(1,1,1); "
        "la estacionalidad moderada motiva un candidato SARIMA."
    ),
    "S3_san_cristobal": (
        "Tras d=1, ACF y PACF presentan su señal principal negativa en lag "
        "1. Por eso se comparan términos AR(1), MA(1), su combinación y un "
        "SARIMA anual para verificar si la estacionalidad agrega valor."
    ),
    "S6_guatemala": (
        "Se conserva la especificación ya integrada para S6, fuera del "
        "comparativo de Fronteras."
    ),
}

NOMBRES_S1_S2_S6 = ("S1_la_aurora", "S2_valle_nuevo", "S6_guatemala")
NOMBRES_FRONTERAS = (
    "S1_la_aurora",
    "S2_valle_nuevo",
    "S3_san_cristobal",
)


# Convierte objetos de NumPy, pandas y tuplas a valores que JSON puede guardar.
def _serializable(valor):
    if isinstance(valor, dict):
        return {clave: _serializable(dato) for clave, dato in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_serializable(dato) for dato in valor]
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, (np.floating,)):
        return None if np.isnan(valor) else float(valor)
    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")
    return valor


# Evalúa nivel, transformación y diferencias sin usar el período de prueba.
def evaluar_estacionariedad(train, transformacion):
    transformada = transformar_serie(train, transformacion)
    variantes = {
        "Nivel": train,
        transformacion: transformada,
        f"{transformacion} + d=1": transformada.diff().dropna(),
        f"{transformacion} + D=1": transformada.diff(12).dropna(),
        f"{transformacion} + d=1 + D=1": (
            transformada.diff().diff(12).dropna()
        ),
    }

    filas = []
    for nombre, valores in variantes.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            resultado = test_estacionariedad(
                valores,
                nombre=nombre,
                verbose=False,
            )
        filas.append(
            {
                "transformacion": nombre,
                "ADF": resultado["adf_estadistico"],
                "p_ADF": resultado["adf_p"],
                "KPSS": resultado["kpss_estadistico"],
                "p_KPSS": resultado["kpss_p"],
                "veredicto": resultado["veredicto"],
            }
        )
    return pd.DataFrame(filas)


# Adaptadores homogéneos de Holt-Winters, suavizamiento simple y Seasonal Naive.
# Conservan la misma partición, horizonte y formato de resultados que ARIMA y
# Prophet.
def ajustar_holt_winters(train, test):
    modelo = ExponentialSmoothing(
        train,
        trend="add",
        damped_trend=True,
        seasonal="add",
        seasonal_periods=config.PERIODO_ESTACIONAL,
        initialization_method="estimated",
    ).fit(optimized=True)
    pronostico = pd.Series(
        np.clip(modelo.forecast(len(test)), 0, None),
        index=test.index,
        name="Holt-Winters",
    )
    residuos = pd.Series(
        train.to_numpy() - np.asarray(modelo.fittedvalues),
        index=train.index,
        name="residuos_holt_winters",
    )
    return pronostico, residuos


def ajustar_suavizamiento_simple(train, test):
    modelo = SimpleExpSmoothing(
        train,
        initialization_method="estimated",
    ).fit(optimized=True)
    pronostico = pd.Series(
        np.clip(modelo.forecast(len(test)), 0, None),
        index=test.index,
        name="Suavizamiento exponencial simple",
    )
    residuos = pd.Series(
        train.to_numpy() - np.asarray(modelo.fittedvalues),
        index=train.index,
        name="residuos_ses",
    )
    return pronostico, residuos


def ajustar_seasonal_naive(train, test):
    patron = train.iloc[-config.PERIODO_ESTACIONAL :].to_numpy()
    valores = np.resize(patron, len(test))
    pronostico = pd.Series(
        valores,
        index=test.index,
        name="Seasonal Naive",
    )
    residuos = (
        train.iloc[config.PERIODO_ESTACIONAL :].to_numpy()
        - train.shift(config.PERIODO_ESTACIONAL).dropna().to_numpy()
    )
    return pronostico, pd.Series(residuos, name="residuos_seasonal_naive")


# Sugiere un orden automático acotado y evita duplicar candidatos manuales.
def preparar_candidatos(nombre_serie, train, transformacion):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sugerencia = sugerir_auto_arima(
            train,
            transformacion=transformacion,
            max_p=2,
            max_q=2,
            max_P=1,
            max_Q=1,
        )

    candidatos = [
        dict(candidato) for candidato in CANDIDATOS_POR_SERIE[nombre_serie]
    ]
    firma_auto = (
        tuple(sugerencia["orden"]),
        tuple(sugerencia["orden_estacional"]),
    )
    firmas = {
        (
            tuple(candidato["orden"]),
            tuple(candidato["orden_estacional"]),
        )
        for candidato in candidatos
    }
    if firma_auto not in firmas:
        candidatos.append(
            {
                "nombre": (
                    f"auto_arima{firma_auto[0]}x{firma_auto[1]}"
                ),
                "orden": firma_auto[0],
                "orden_estacional": firma_auto[1],
            }
        )
    return candidatos, sugerencia


# Ejecuta todos los modelos exigidos para una serie y devuelve evidencia.
def modelar_serie(nombre_serie):
    especificacion = ESPECIFICACIONES[nombre_serie]
    serie = cargar_serie(nombre_serie)
    train, test = partir_train_test(serie)
    transformacion = especificacion["transformacion"]

    estacionariedad = evaluar_estacionariedad(train, transformacion)
    candidatos, sugerencia = preparar_candidatos(
        nombre_serie,
        train,
        transformacion,
    )
    resultados_arima = ajustar_candidatos_arima(
        train=train,
        candidatos=candidatos,
        horizonte=len(test),
        indice_pronostico=test.index,
        transformacion=transformacion,
        nombre_serie=nombre_serie,
        continuar_si_falla=False,
    )

    filas = []
    pronosticos = {}
    residuos = {}
    for resultado in resultados_arima:
        nombre = resultado["modelo"]
        pronosticos[nombre] = resultado["pronostico"]
        residuos[nombre] = resultado["residuos"]
        filas.append(
            construir_resultado(
                serie=nombre_serie,
                modelo=nombre,
                y_real=test,
                y_pred=resultado["pronostico"],
                parametros=resultado["parametros"],
                transformacion=transformacion,
                aic=resultado["AIC"],
                bic=resultado["BIC"],
                residuos=resultado["residuos"],
            )
        )

    resultado_prophet = ajustar_y_pronosticar_prophet(
        train=train,
        horizonte=len(test),
        indice_pronostico=test.index,
        nombre_serie=nombre_serie,
    )
    hw_pronostico, hw_residuos = ajustar_holt_winters(train, test)
    ses_pronostico, ses_residuos = ajustar_suavizamiento_simple(train, test)
    sn_pronostico, sn_residuos = ajustar_seasonal_naive(train, test)

    alternativos = {
        "Prophet": (
            (resultado_prophet["pronostico"], resultado_prophet["residuos"]),
            resultado_prophet["parametros"],
        ),
        "Holt-Winters": (
            (hw_pronostico, hw_residuos),
            {
                "tendencia": "aditiva amortiguada",
                "estacionalidad": "aditiva",
                "periodo": 12,
            },
        ),
        "Suavizamiento exponencial simple": (
            (ses_pronostico, ses_residuos),
            {"tendencia": None, "estacionalidad": None},
        ),
        "Seasonal Naive": (
            (sn_pronostico, sn_residuos),
            {"rezago": 12},
        ),
    }
    for nombre, ((pronostico, residuo), parametros) in alternativos.items():
        pronosticos[nombre] = pronostico
        residuos[nombre] = residuo
        filas.append(
            construir_resultado(
                serie=nombre_serie,
                modelo=nombre,
                y_real=test,
                y_pred=pronostico,
                parametros=parametros,
                transformacion="ninguna",
                residuos=residuo,
            )
        )

    tabla = tabla_comparativa(filas)
    mejor = tabla.loc[tabla["mejor_modelo"]].iloc[0]
    descomposicion = seasonal_decompose(
        train,
        model="additive",
        period=config.PERIODO_ESTACIONAL,
    )
    descomposicion_multiplicativa = (
        seasonal_decompose(
            train,
            model="multiplicative",
            period=config.PERIODO_ESTACIONAL,
        )
        if (train > 0).all()
        else None
    )

    prepandemia = train[train.index.year <= 2019]
    anual_nivel = prepandemia.groupby(prepandemia.index.year).agg(
        ["mean", "std"]
    )
    transformada_pre = transformar_serie(prepandemia, transformacion)
    anual_transformada = transformada_pre.groupby(
        transformada_pre.index.year
    ).agg(["mean", "std"])
    correlacion_nivel = float(
        anual_nivel["mean"].corr(anual_nivel["std"])
    )
    correlacion_transformada = float(
        anual_transformada["mean"].corr(anual_transformada["std"])
    )
    modelo_descomposicion = (
        "multiplicative"
        if descomposicion_multiplicativa is not None
        and correlacion_nivel >= 0.5
        else "additive"
    )

    resumen = {
        "serie": nombre_serie,
        "etiqueta": especificacion["etiqueta"],
        "inicio": serie.index.min(),
        "fin": serie.index.max(),
        "frecuencia": "mensual (m=12)",
        "n_total": len(serie),
        "n_train": len(train),
        "n_test": len(test),
        "inicio_train": train.index.min(),
        "fin_train": train.index.max(),
        "inicio_test": test.index.min(),
        "fin_test": test.index.max(),
        "min_train": float(train.min()),
        "max_train": float(train.max()),
        "media_train": float(train.mean()),
        "media_test": float(test.mean()),
        "ceros_train": int((train == 0).sum()),
        "ceros_test": int((test == 0).sum()),
        "fuerza_estacional": float(fuerza_estacional(descomposicion)),
        "fuerza_tendencia": float(fuerza_tendencia(descomposicion)),
        "correlacion_media_desviacion_nivel": correlacion_nivel,
        "correlacion_media_desviacion_transformada": correlacion_transformada,
        "modelo_descomposicion_preferido": modelo_descomposicion,
        "transformacion": transformacion,
        "razonamiento_ordenes": RAZONAMIENTO_ORDENES[nombre_serie],
        "orden_auto": sugerencia["orden"],
        "orden_estacional_auto": sugerencia["orden_estacional"],
        "mejor_modelo": mejor["modelo"],
        "mejor_MAE": float(mejor["MAE"]),
        "mejor_RMSE": float(mejor["RMSE"]),
        "mejor_MAPE": float(mejor["MAPE"]) if pd.notna(mejor["MAPE"]) else None,
    }
    return {
        "serie": serie,
        "train": train,
        "test": test,
        "estacionariedad": estacionariedad,
        "descomposicion": descomposicion,
        "descomposicion_multiplicativa": descomposicion_multiplicativa,
        "tabla": tabla,
        "pronosticos": pronosticos,
        "residuos": residuos,
        "resumen": resumen,
    }


# Guarda figuras descriptivas, diagnósticos y comparación de pronósticos.
def guardar_figuras(resultado):
    DIR_IMG.mkdir(parents=True, exist_ok=True)
    serie = resultado["serie"]
    train = resultado["train"]
    test = resultado["test"]
    resumen = resultado["resumen"]
    prefijo = ESPECIFICACIONES[resumen["serie"]]["archivo"]
    etiqueta = resumen["etiqueta"]
    transformacion = resumen["transformacion"]

    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(serie.index, serie, color="#2f6690", linewidth=1.4)
    ax.axvspan(
        pd.Timestamp("2020-03-01"),
        pd.Timestamp("2021-12-01"),
        color="#d9a441",
        alpha=0.2,
        label="Pandemia y restricciones",
    )
    ax.axvline(
        test.index.min(),
        color="#b23a48",
        linestyle="--",
        linewidth=1.5,
        label="Inicio de prueba",
    )
    ax.set_title(f"{etiqueta}: serie mensual y partición temporal")
    ax.set_ylabel("Viajeros")
    ax.set_xlabel("")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(DIR_IMG / f"{prefijo}_serie_particion.png", dpi=150)
    plt.close(fig)

    componentes_aditivos = [
        (train, "Observada", "#2f6690"),
        (resultado["descomposicion"].trend, "Tendencia", "#c44536"),
        (
            resultado["descomposicion"].seasonal,
            "Estacionalidad",
            "#6a994e",
        ),
        (resultado["descomposicion"].resid, "Residuo", "#6c757d"),
    ]
    multiplicativa = resultado["descomposicion_multiplicativa"]
    componentes_multiplicativos = (
        [
            (train, "Observada", "#2f6690"),
            (multiplicativa.trend, "Tendencia", "#c44536"),
            (multiplicativa.seasonal, "Estacionalidad", "#6a994e"),
            (multiplicativa.resid, "Residuo", "#6c757d"),
        ]
        if multiplicativa is not None
        else None
    )
    columnas = 2 if componentes_multiplicativos is not None else 1
    fig, axes = plt.subplots(
        4,
        columnas,
        figsize=(14 if columnas == 2 else 12, 10),
        sharex=True,
        squeeze=False,
    )
    for fila, (datos, nombre, color) in enumerate(componentes_aditivos):
        axes[fila, 0].plot(datos.index, datos, color=color, linewidth=1.0)
        axes[fila, 0].set_ylabel(nombre)
        axes[fila, 0].grid(alpha=0.22)
    axes[0, 0].set_title("Descomposición aditiva")
    if componentes_multiplicativos is not None:
        for fila, (datos, nombre, color) in enumerate(
            componentes_multiplicativos
        ):
            axes[fila, 1].plot(
                datos.index,
                datos,
                color=color,
                linewidth=1.0,
            )
            axes[fila, 1].set_ylabel(nombre)
            axes[fila, 1].grid(alpha=0.22)
        axes[0, 1].set_title("Descomposición multiplicativa")
    preferida = {
        "additive": "aditiva",
        "multiplicative": "multiplicativa",
    }[resumen["modelo_descomposicion_preferido"]]
    fig.suptitle(
        (
            f"{etiqueta}: comparación de descomposiciones "
            f"(preferida: {preferida})"
        ),
        y=0.995,
    )
    fig.tight_layout()
    fig.savefig(DIR_IMG / f"{prefijo}_descomposicion.png", dpi=150)
    plt.close(fig)

    transformada = transformar_serie(train, transformacion)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, datos, nombre, color in [
        (axes[0], train, "Nivel original", "#2f6690"),
        (
            axes[1],
            transformada,
            f"Transformación {transformacion}",
            "#6a994e",
        ),
    ]:
        ax.plot(datos.index, datos, color=color, alpha=0.65, linewidth=0.9)
        ax.plot(
            datos.rolling(12).mean(),
            color="#20242b",
            linewidth=1.35,
            label="Media móvil 12m",
        )
        ax.plot(
            datos.rolling(12).std(),
            color="#c44536",
            linewidth=1.15,
            label="Desviación móvil 12m",
        )
        ax.set_title(nombre)
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8)
    fig.suptitle(f"{etiqueta}: media y variación móvil", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(
        DIR_IMG / f"{prefijo}_varianza.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    regular = transformada.diff().dropna()
    regular_estacional = regular.diff(12).dropna()
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    plot_acf(regular, lags=36, ax=axes[0, 0])
    plot_pacf(regular, lags=36, ax=axes[0, 1], method="ywm")
    plot_acf(regular_estacional, lags=36, ax=axes[1, 0])
    plot_pacf(
        regular_estacional,
        lags=36,
        ax=axes[1, 1],
        method="ywm",
    )
    axes[0, 0].set_title("ACF después de d=1")
    axes[0, 1].set_title("PACF después de d=1")
    axes[1, 0].set_title("ACF después de d=1 y D=1")
    axes[1, 1].set_title("PACF después de d=1 y D=1")
    fig.suptitle(f"{etiqueta}: ACF y PACF del entrenamiento", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(
        DIR_IMG / f"{prefijo}_acf_pacf.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    mejores_nombres = resultado["tabla"].head(4)["modelo"].tolist()
    pronosticos_grafica = {
        nombre: resultado["pronosticos"][nombre]
        for nombre in mejores_nombres
    }
    fig, _ = graficar_real_pronostico(
        test,
        pronosticos_grafica,
        f"{etiqueta}: observado y pronósticos en prueba",
        DIR_IMG / f"{prefijo}_pronosticos.png",
    )
    plt.close(fig)

    tabla_completa = resultado["tabla"].sort_values("RMSE", ascending=True)
    limite_estable = tabla_completa["RMSE"].median() * 10
    tabla_ordenada = tabla_completa[
        tabla_completa["RMSE"] <= limite_estable
    ].copy()
    inestables = tabla_completa[
        tabla_completa["RMSE"] > limite_estable
    ]
    fig, ax = plt.subplots(figsize=(10, 5))
    colores = [
        "#2f6690" if valor else "#9bb7cc"
        for valor in tabla_ordenada["mejor_modelo"]
    ]
    ax.barh(
        tabla_ordenada["modelo"],
        tabla_ordenada["RMSE"],
        color=colores,
    )
    ax.invert_yaxis()
    ax.set_title(f"{etiqueta}: RMSE por modelo")
    ax.set_xlabel("RMSE en los 63 meses de prueba")
    ax.grid(axis="x", alpha=0.25)
    for barra, valor in zip(ax.patches, tabla_ordenada["RMSE"]):
        ax.text(
            valor,
            barra.get_y() + barra.get_height() / 2,
            f" {valor:,.0f}",
            va="center",
            fontsize=8,
        )
    if not inestables.empty:
        nombres = ", ".join(inestables["modelo"].astype(str))
        ax.text(
            0,
            -0.16,
            (
                "Candidato inestable omitido de la escala visual: "
                f"{nombres}. Su error permanece en la tabla."
            ),
            transform=ax.transAxes,
            fontsize=8,
            color="#6c757d",
        )
    fig.tight_layout()
    fig.savefig(
        DIR_IMG / f"{prefijo}_rmse_modelos.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    candidatos_arima = resultado["tabla"][
        resultado["tabla"]["AIC"].notna()
    ].sort_values("RMSE")
    mejor_arima = candidatos_arima.iloc[0]["modelo"]
    residuo = pd.Series(resultado["residuos"][mejor_arima]).dropna()
    diagnostico = diagnosticar_residuos(residuo)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    axes[0, 0].plot(
        residuo.index,
        residuo,
        color="#6c757d",
        linewidth=1.0,
    )
    axes[0, 0].axhline(0, color="#20242b", linewidth=0.9)
    axes[0, 0].set_title(f"Residuos de {mejor_arima}")
    axes[0, 0].grid(alpha=0.22)
    plot_acf(
        residuo,
        lags=min(36, len(residuo) // 2 - 1),
        ax=axes[0, 1],
    )
    axes[0, 1].set_title(
        f"ACF de residuos · Ljung-Box p={diagnostico['Ljung_Box_p']:.3f}"
    )
    axes[1, 0].hist(
        residuo,
        bins=16,
        color="#9bb7cc",
        edgecolor="white",
    )
    axes[1, 0].set_title(
        (
            "Distribución de residuos · "
            f"Jarque-Bera p={diagnostico['Jarque_Bera_p']:.3f}"
        )
    )
    axes[1, 0].grid(axis="y", alpha=0.22)
    qqplot(residuo, line="45", ax=axes[1, 1], fit=True)
    axes[1, 1].set_title("Gráfico Q-Q de normalidad")
    fig.suptitle(f"{etiqueta}: diagnóstico del candidato ARIMA", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(
        DIR_IMG / f"{prefijo}_residuos.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)


# Calcula la evidencia homogénea solicitada para comparar las tres fronteras.
def calcular_comparativo_fronteras(resultados):
    filas = []
    for nombre in NOMBRES_FRONTERAS:
        resultado = resultados[nombre]
        serie = resultado["serie"]
        tendencia = resultado["descomposicion"].trend.dropna()
        tendencia_pre = tendencia[tendencia.index.year <= 2019]
        eje = np.arange(len(tendencia_pre), dtype=float)
        pendiente = float(np.polyfit(eje, tendencia_pre.to_numpy(), 1)[0])
        pendiente_relativa = float(
            pendiente / tendencia_pre.mean() * 100
        )

        pre = serie[
            (serie.index >= "2009-01-01")
            & (serie.index <= "2019-12-01")
        ]
        total_2009 = float(pre[pre.index.year == 2009].sum())
        total_2019 = float(pre[pre.index.year == 2019].sum())
        cagr = float((total_2019 / total_2009) ** (1 / 10) - 1) * 100
        cv = float(pre.std(ddof=1) / pre.mean())
        volatilidad_log = float(np.log(pre).diff().dropna().std(ddof=1))

        total_2020 = float(serie[serie.index.year == 2020].sum())
        caida = float((1 - total_2020 / total_2019) * 100)
        nivel_2019 = float(pre[pre.index.year == 2019].mean())
        recuperaciones_mensuales = serie[
            (serie.index > "2020-03-01") & (serie >= nivel_2019)
        ]
        primera_recuperacion = (
            recuperaciones_mensuales.index.min()
            if not recuperaciones_mensuales.empty
            else pd.NaT
        )
        meses_primera_recuperacion = (
            (
                (primera_recuperacion.year - 2020) * 12
                + primera_recuperacion.month
                - 3
            )
            if pd.notna(primera_recuperacion)
            else np.nan
        )
        media_movil = serie.rolling(12, min_periods=12).mean()
        recuperaciones = media_movil[
            (media_movil.index > "2020-03-01")
            & (media_movil >= nivel_2019)
        ]
        fecha_recuperacion = (
            recuperaciones.index.min()
            if not recuperaciones.empty
            else pd.NaT
        )
        meses_recuperacion_sostenida = (
            (
                (fecha_recuperacion.year - 2020) * 12
                + fecha_recuperacion.month
                - 3
            )
            if pd.notna(fecha_recuperacion)
            else np.nan
        )

        filas.append(
            {
                "serie": nombre,
                "frontera": ESPECIFICACIONES[nombre]["etiqueta"].split("—")[
                    -1
                ].strip(),
                "fuerza_estacional": resultado["resumen"][
                    "fuerza_estacional"
                ],
                "fuerza_tendencia": resultado["resumen"][
                    "fuerza_tendencia"
                ],
                "pendiente_tendencia_viajeros_mes": pendiente,
                "pendiente_tendencia_relativa_pct_mes": pendiente_relativa,
                "cagr_2009_2019_pct": cagr,
                "coeficiente_variacion_2009_2019": cv,
                "desviacion_log_diferencias_2009_2019": volatilidad_log,
                "caida_2020_vs_2019_pct": caida,
                "fecha_primera_recuperacion_mensual": primera_recuperacion,
                "meses_primera_recuperacion_mensual": (
                    meses_primera_recuperacion
                ),
                "fecha_recuperacion_sostenida_media_movil_2019": (
                    fecha_recuperacion
                ),
                "meses_hasta_recuperacion_sostenida": (
                    meses_recuperacion_sostenida
                ),
            }
        )

    tabla = pd.DataFrame(filas)
    tabla["ranking_estacionalidad"] = (
        tabla["fuerza_estacional"].rank(ascending=False, method="min").astype(int)
    )
    tabla["ranking_crecimiento"] = (
        tabla["cagr_2009_2019_pct"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    tabla["ranking_volatilidad"] = (
        tabla["desviacion_log_diferencias_2009_2019"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    tabla["ranking_caida_pandemia"] = (
        tabla["caida_2020_vs_2019_pct"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    return tabla


def _ejecutar_modelado(nombres, sufijo, guardar=True, generar_figuras=True):
    resultados = {
        nombre: modelar_serie(nombre)
        for nombre in nombres
    }

    if guardar:
        DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
        metricas = pd.concat(
            [resultado["tabla"] for resultado in resultados.values()],
            ignore_index=True,
        )
        metricas.to_csv(
            DIR_RESULTADOS / f"metricas_{sufijo}.csv",
            index=False,
        )

        estacionariedad = pd.concat(
            [
                resultado["estacionariedad"].assign(serie=nombre)
                for nombre, resultado in resultados.items()
            ],
            ignore_index=True,
        )
        columnas = ["serie"] + [
            columna
            for columna in estacionariedad.columns
            if columna != "serie"
        ]
        estacionariedad[columnas].to_csv(
            DIR_RESULTADOS / f"estacionariedad_{sufijo}.csv",
            index=False,
        )

        pronosticos = []
        for nombre, resultado in resultados.items():
            for modelo, valores in resultado["pronosticos"].items():
                pronosticos.append(
                    pd.DataFrame(
                        {
                            "fecha": resultado["test"].index,
                            "serie": nombre,
                            "modelo": modelo,
                            "observado": resultado["test"].to_numpy(),
                            "pronostico": valores.to_numpy(),
                        }
                    )
                )
        pd.concat(pronosticos, ignore_index=True).to_csv(
            DIR_RESULTADOS / f"pronosticos_{sufijo}.csv",
            index=False,
        )

        resumen = {
            nombre: _serializable(resultado["resumen"])
            for nombre, resultado in resultados.items()
        }
        (DIR_RESULTADOS / f"resumen_{sufijo}.json").write_text(
            json.dumps(resumen, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if generar_figuras:
        for resultado in resultados.values():
            guardar_figuras(resultado)

    return resultados


def ejecutar_modelado_s1_s2_s6(guardar=True, generar_figuras=True):
    return _ejecutar_modelado(
        NOMBRES_S1_S2_S6,
        "s1_s2_s6",
        guardar=guardar,
        generar_figuras=generar_figuras,
    )


def ejecutar_modelado_fronteras(guardar=True, generar_figuras=True):
    resultados = _ejecutar_modelado(
        NOMBRES_FRONTERAS,
        "fronteras",
        guardar=guardar,
        generar_figuras=generar_figuras,
    )
    comparativo = calcular_comparativo_fronteras(resultados)
    if guardar:
        comparativo.to_csv(
            DIR_RESULTADOS / "comparativo_fronteras.csv",
            index=False,
        )
    return resultados, comparativo


if __name__ == "__main__":
    salida, comparativo = ejecutar_modelado_fronteras()
    for nombre, resultado in salida.items():
        mejor = resultado["tabla"].loc[
            resultado["tabla"]["mejor_modelo"]
        ].iloc[0]
        print(
            f"{nombre}: {mejor['modelo']} · "
            f"MAE={mejor['MAE']:.2f} · RMSE={mejor['RMSE']:.2f}"
        )
    print("\nComparativo de Fronteras:")
    print(comparativo.to_string(index=False))
