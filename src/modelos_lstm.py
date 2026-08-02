import random

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras


SEED = 42


def fijar_semillas(seed=SEED):
    """Fija las semillas utilizadas por Python, NumPy y TensorFlow."""
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def crear_ventanas(valores_escalados, lookback):
    """Convierte una serie en pares supervisados con forma apta para LSTM."""
    if not isinstance(lookback, int) or lookback <= 0:
        raise ValueError("lookback debe ser un entero positivo.")

    valores = np.asarray(valores_escalados, dtype=float).reshape(-1)
    if not np.isfinite(valores).all():
        raise ValueError("valores_escalados contiene faltantes o infinitos.")
    if len(valores) <= lookback:
        raise ValueError(
            "Se necesitan más observaciones que el tamaño de lookback."
        )

    X, y = [], []
    for indice in range(lookback, len(valores)):
        X.append(valores[indice - lookback:indice])
        y.append(valores[indice])

    return (
        np.asarray(X, dtype=float).reshape(-1, lookback, 1),
        np.asarray(y, dtype=float),
    )


def construir_modelo(lookback, unidades, capas=1, dropout=0.0):
    """Construye bloques LSTM, dropout opcional y una salida ``Dense(1)``."""
    if not isinstance(lookback, int) or lookback <= 0:
        raise ValueError("lookback debe ser un entero positivo.")
    if not isinstance(unidades, int) or unidades <= 0:
        raise ValueError("unidades debe ser un entero positivo.")
    if not isinstance(capas, int) or capas <= 0:
        raise ValueError("capas debe ser un entero positivo.")
    if not 0.0 <= dropout < 1.0:
        raise ValueError("dropout debe estar en el intervalo [0, 1).")

    modelo = keras.Sequential()
    modelo.add(keras.layers.Input(shape=(lookback, 1)))
    for indice_capa in range(capas):
        es_ultima = indice_capa == capas - 1
        modelo.add(
            keras.layers.LSTM(
                unidades,
                return_sequences=not es_ultima,
            )
        )
        if dropout > 0:
            modelo.add(keras.layers.Dropout(dropout))

    modelo.add(keras.layers.Dense(1))
    modelo.compile(optimizer="adam", loss="mse")
    return modelo


def crear_ventanas_catch22(valores_escalados, catch22_features, lookback):
    """Concatena una firma catch22 de 22 valores a cada paso de la ventana."""
    X_objetivo, y = crear_ventanas(valores_escalados, lookback)
    caracteristicas = np.asarray(catch22_features, dtype=float).reshape(-1)
    if caracteristicas.size != 22:
        raise ValueError("catch22_features debe contener exactamente 22 valores.")
    if not np.isfinite(caracteristicas).all():
        raise ValueError("catch22_features contiene valores faltantes o infinitos.")

    contexto = np.broadcast_to(
        caracteristicas,
        (len(X_objetivo), lookback, caracteristicas.size),
    )
    return np.concatenate([X_objetivo, contexto], axis=2), y


def construir_modelo_multivariado(
    lookback,
    n_caracteristicas,
    unidades,
    capas=1,
    dropout=0.0,
):
    """Construye una LSTM para entradas con variable objetivo y rasgos catch22."""
    if not isinstance(n_caracteristicas, int) or n_caracteristicas <= 1:
        raise ValueError("n_caracteristicas debe ser un entero mayor que uno.")
    if not isinstance(lookback, int) or lookback <= 0:
        raise ValueError("lookback debe ser un entero positivo.")
    if not isinstance(unidades, int) or unidades <= 0:
        raise ValueError("unidades debe ser un entero positivo.")
    if not isinstance(capas, int) or capas <= 0:
        raise ValueError("capas debe ser un entero positivo.")
    if not 0.0 <= dropout < 1.0:
        raise ValueError("dropout debe estar en el intervalo [0, 1).")

    modelo = keras.Sequential()
    modelo.add(keras.layers.Input(shape=(lookback, n_caracteristicas)))
    for indice_capa in range(capas):
        es_ultima = indice_capa == capas - 1
        modelo.add(
            keras.layers.LSTM(
                unidades,
                return_sequences=not es_ultima,
            )
        )
        if dropout > 0:
            modelo.add(keras.layers.Dropout(dropout))

    modelo.add(keras.layers.Dense(1))
    modelo.compile(optimizer="adam", loss="mse")
    return modelo


def pronosticar_recursivo(modelo, escalador, ultima_ventana, pasos):
    """Genera un pronóstico recursivo multi-step y lo devuelve desescalado."""
    if not isinstance(pasos, int) or pasos < 0:
        raise ValueError("pasos debe ser un entero mayor o igual que cero.")

    ventana = np.asarray(ultima_ventana, dtype=float).reshape(-1).copy()
    if ventana.size == 0:
        raise ValueError("ultima_ventana no puede estar vacía.")
    if not np.isfinite(ventana).all():
        raise ValueError("ultima_ventana contiene faltantes o infinitos.")
    if pasos == 0:
        return np.array([], dtype=float)

    predicciones = []
    for _ in range(pasos):
        entrada = ventana.reshape(1, len(ventana), 1)
        pred_escalada = float(modelo.predict(entrada, verbose=0)[0, 0])
        predicciones.append(pred_escalada)
        ventana = np.append(ventana[1:], pred_escalada)

    return escalador.inverse_transform(
        np.asarray(predicciones, dtype=float).reshape(-1, 1)
    ).reshape(-1)


def pronosticar_recursivo_catch22(
    modelo,
    escalador,
    ultima_ventana,
    catch22_features,
    pasos,
):
    """Genera un pronóstico recursivo con una firma catch22 de contexto."""
    if not isinstance(pasos, int) or pasos < 0:
        raise ValueError("pasos debe ser un entero mayor o igual que cero.")
    ventana = np.asarray(ultima_ventana, dtype=float).reshape(-1).copy()
    caracteristicas = np.asarray(catch22_features, dtype=float).reshape(-1)
    if ventana.size == 0:
        raise ValueError("ultima_ventana no puede estar vacía.")
    if caracteristicas.size != 22:
        raise ValueError("catch22_features debe contener exactamente 22 valores.")
    if not np.isfinite(ventana).all() or not np.isfinite(caracteristicas).all():
        raise ValueError("La ventana y las características deben ser finitas.")
    if pasos == 0:
        return np.array([], dtype=float)

    contexto = np.broadcast_to(
        caracteristicas,
        (len(ventana), caracteristicas.size),
    )
    predicciones = []
    for _ in range(pasos):
        entrada_modelo = np.column_stack([ventana, contexto]).reshape(
            1,
            len(ventana),
            23,
        )
        pred_escalada = float(modelo.predict(entrada_modelo, verbose=0)[0, 0])
        predicciones.append(pred_escalada)
        ventana = np.append(ventana[1:], pred_escalada)

    return escalador.inverse_transform(
        np.asarray(predicciones, dtype=float).reshape(-1, 1)
    ).reshape(-1)


def entrenar_lstm(
    train,
    test,
    lookback,
    unidades,
    capas=1,
    dropout=0.0,
    epochs=100,
    batch_size=16,
    seed=SEED,
):
    """Entrena con ``train`` y pronostica recursivamente el índice de ``test``."""
    if not isinstance(train, pd.Series) or not isinstance(test, pd.Series):
        raise TypeError("train y test deben ser objetos pandas.Series.")
    if train.empty or test.empty:
        raise ValueError("train y test deben contener observaciones.")
    if not train.index.is_monotonic_increasing:
        raise ValueError("El índice de train debe estar ordenado.")
    if not test.index.is_monotonic_increasing:
        raise ValueError("El índice de test debe estar ordenado.")
    if train.index.max() >= test.index.min():
        raise ValueError("El conjunto de prueba debe ser posterior a train.")
    if not np.isfinite(train.to_numpy(dtype=float)).all():
        raise ValueError("train contiene valores faltantes o infinitos.")
    if not np.isfinite(test.to_numpy(dtype=float)).all():
        raise ValueError("test contiene valores faltantes o infinitos.")
    if not isinstance(epochs, int) or epochs <= 0:
        raise ValueError("epochs debe ser un entero positivo.")
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size debe ser un entero positivo.")

    fijar_semillas(seed)
    escalador = MinMaxScaler(feature_range=(0, 1))
    train_escalado = escalador.fit_transform(
        train.to_numpy(dtype=float).reshape(-1, 1)
    ).reshape(-1)

    X, y = crear_ventanas(train_escalado, lookback)
    modelo = construir_modelo(
        lookback,
        unidades,
        capas=capas,
        dropout=dropout,
    )
    detencion_temprana = keras.callbacks.EarlyStopping(
        monitor="loss",
        patience=10,
        restore_best_weights=True,
    )
    historial = modelo.fit(
        X,
        y,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[detencion_temprana],
        verbose=0,
    )

    ultima_ventana = train_escalado[-lookback:]
    predicciones = pronosticar_recursivo(
        modelo,
        escalador,
        ultima_ventana,
        len(test),
    )
    y_pred = pd.Series(predicciones, index=test.index, name="y_pred")

    return {
        "modelo": modelo,
        "historial": historial,
        "escalador": escalador,
        "y_pred": y_pred,
    }


def entrenar_lstm_catch22(
    train,
    test,
    catch22_features,
    lookback,
    unidades,
    capas=1,
    dropout=0.0,
    epochs=100,
    batch_size=16,
    seed=SEED,
):
    """Entrena una LSTM con el valor objetivo y 22 rasgos catch22 por paso."""
    if not isinstance(train, pd.Series) or not isinstance(test, pd.Series):
        raise TypeError("train y test deben ser objetos pandas.Series.")
    if train.empty or test.empty:
        raise ValueError("train y test deben contener observaciones.")
    if not train.index.is_monotonic_increasing:
        raise ValueError("El índice de train debe estar ordenado.")
    if not test.index.is_monotonic_increasing:
        raise ValueError("El índice de test debe estar ordenado.")
    if train.index.max() >= test.index.min():
        raise ValueError("El conjunto de prueba debe ser posterior a train.")
    if not np.isfinite(train.to_numpy(dtype=float)).all():
        raise ValueError("train contiene valores faltantes o infinitos.")
    if not np.isfinite(test.to_numpy(dtype=float)).all():
        raise ValueError("test contiene valores faltantes o infinitos.")
    if not isinstance(epochs, int) or epochs <= 0:
        raise ValueError("epochs debe ser un entero positivo.")
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size debe ser un entero positivo.")

    fijar_semillas(seed)
    escalador = MinMaxScaler(feature_range=(0, 1))
    train_escalado = escalador.fit_transform(
        train.to_numpy(dtype=float).reshape(-1, 1)
    ).reshape(-1)
    X, y = crear_ventanas_catch22(
        train_escalado,
        catch22_features,
        lookback,
    )

    modelo = construir_modelo_multivariado(
        lookback,
        X.shape[2],
        unidades,
        capas=capas,
        dropout=dropout,
    )
    detencion_temprana = keras.callbacks.EarlyStopping(
        monitor="loss",
        patience=10,
        restore_best_weights=True,
    )
    historial = modelo.fit(
        X,
        y,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[detencion_temprana],
        verbose=0,
    )

    predicciones = pronosticar_recursivo_catch22(
        modelo=modelo,
        escalador=escalador,
        ultima_ventana=train_escalado[-lookback:],
        catch22_features=catch22_features,
        pasos=len(test),
    )
    y_pred = pd.Series(predicciones, index=test.index, name="y_pred")

    return {
        "modelo": modelo,
        "historial": historial,
        "escalador": escalador,
        "forma_entrenamiento": X.shape,
        "y_pred": y_pred,
    }
