"""Extracción y análisis comparativo de características catch22.

Las filas de las matrices representan series temporales y las columnas las 22
características canónicas. Toda comparación multivariada debe realizarse sobre
la matriz estandarizada para que las escalas de las características no dominen
el PCA, el clustering ni las distancias.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pycatch22
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


SEED = 42
N_CARACTERISTICAS = 22


def _como_vector_finito(serie):
    """Convierte una serie univariada a un vector numérico finito."""
    if isinstance(serie, pd.Series):
        valores = serie.to_numpy(dtype=float)
    else:
        valores = np.asarray(serie, dtype=float)

    if valores.ndim != 1:
        raise ValueError("La serie debe ser unidimensional.")
    if len(valores) < 3:
        raise ValueError("La serie debe contener al menos tres observaciones.")
    if not np.isfinite(valores).all():
        raise ValueError("La serie contiene valores faltantes o infinitos.")
    if np.ptp(valores) == 0:
        raise ValueError("catch22 no admite una serie constante.")
    return valores


def _validar_matriz(matriz, minimo_filas=1):
    """Valida una matriz numérica antes de los análisis multivariados."""
    if not isinstance(matriz, pd.DataFrame):
        raise TypeError("matriz debe ser un pandas.DataFrame.")
    if matriz.shape[0] < minimo_filas:
        raise ValueError(
            f"La matriz debe contener al menos {minimo_filas} filas."
        )
    if matriz.shape[1] == 0:
        raise ValueError("La matriz debe contener al menos una característica.")
    if matriz.index.has_duplicates:
        raise ValueError("Los nombres de las series no pueden repetirse.")
    if matriz.columns.has_duplicates:
        raise ValueError("Los nombres de las características no pueden repetirse.")

    try:
        valores = matriz.to_numpy(dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("La matriz debe contener únicamente valores numéricos.") from error
    if not np.isfinite(valores).all():
        raise ValueError("La matriz contiene valores faltantes o infinitos.")
    return valores


def extraer_catch22(serie):
    """Extrae las 22 características catch22 de una serie univariada."""
    valores = _como_vector_finito(serie)
    resultado = pycatch22.catch22_all(valores.tolist(), catch24=False)
    nombres = resultado.get("names", [])
    caracteristicas = resultado.get("values", [])

    if len(nombres) != N_CARACTERISTICAS or len(caracteristicas) != N_CARACTERISTICAS:
        raise RuntimeError("pycatch22 no devolvió exactamente 22 características.")
    if len(set(nombres)) != N_CARACTERISTICAS:
        raise RuntimeError("pycatch22 devolvió nombres de características repetidos.")

    valores_extraidos = np.asarray(caracteristicas, dtype=float)
    if not np.isfinite(valores_extraidos).all():
        raise ValueError("catch22 produjo características faltantes o infinitas.")
    return dict(zip(nombres, valores_extraidos.tolist()))


def construir_matriz_catch22(series):
    """Construye la matriz series × características conservando los nombres."""
    if not isinstance(series, dict) or not series:
        raise ValueError("series debe ser un diccionario no vacío.")

    filas = {
        nombre: extraer_catch22(serie)
        for nombre, serie in series.items()
    }
    matriz = pd.DataFrame.from_dict(filas, orient="index")
    matriz.index.name = "serie"

    if matriz.shape != (len(series), N_CARACTERISTICAS):
        raise RuntimeError("La matriz catch22 no tiene la forma esperada.")
    _validar_matriz(matriz)
    return matriz


def estandarizar_matriz(matriz):
    """Estandariza cada característica y conserva etiquetas de filas/columnas."""
    valores = _validar_matriz(matriz, minimo_filas=2)
    escalador = StandardScaler()
    estandarizada = escalador.fit_transform(valores)
    return pd.DataFrame(
        estandarizada,
        index=matriz.index.copy(),
        columns=matriz.columns.copy(),
    ).rename_axis(index=matriz.index.name, columns=matriz.columns.name)


def calcular_pca(matriz_estandarizada, n_componentes=2):
    """Calcula PCA y devuelve coordenadas, cargas y varianza explicada."""
    valores = _validar_matriz(matriz_estandarizada, minimo_filas=2)
    maximo = min(valores.shape)
    if not isinstance(n_componentes, int) or not 1 <= n_componentes <= maximo:
        raise ValueError(
            f"n_componentes debe ser un entero entre 1 y {maximo}."
        )

    modelo = PCA(n_components=n_componentes)
    coordenadas = modelo.fit_transform(valores)
    nombres = [f"PC{indice}" for indice in range(1, n_componentes + 1)]

    return {
        "modelo": modelo,
        "coordenadas": pd.DataFrame(
            coordenadas,
            index=matriz_estandarizada.index.copy(),
            columns=nombres,
        ).rename_axis(index=matriz_estandarizada.index.name),
        "cargas": pd.DataFrame(
            modelo.components_.T,
            index=matriz_estandarizada.columns.copy(),
            columns=nombres,
        ).rename_axis(index="caracteristica"),
        "varianza_explicada": pd.Series(
            modelo.explained_variance_ratio_,
            index=nombres,
            name="proporcion_varianza",
        ),
    }


def calcular_clustering(matriz_estandarizada, k=None, seed=SEED):
    """Agrupa las series con K-means y opcionalmente elige ``k`` por silhouette."""
    valores = _validar_matriz(matriz_estandarizada, minimo_filas=3)
    n_series = len(matriz_estandarizada)
    candidatos = range(2, min(5, n_series - 1) + 1)
    puntajes = {}

    for candidato in candidatos:
        modelo_candidato = KMeans(
            n_clusters=candidato,
            random_state=seed,
            n_init=20,
        )
        etiquetas = modelo_candidato.fit_predict(valores)
        puntajes[candidato] = float(silhouette_score(valores, etiquetas))

    if k is None:
        if not puntajes:
            raise ValueError("No hay suficientes series para elegir k automáticamente.")
        k = max(puntajes, key=puntajes.get)
    elif not isinstance(k, int) or not 2 <= k < n_series:
        raise ValueError(f"k debe ser un entero entre 2 y {n_series - 1}.")

    modelo = KMeans(n_clusters=k, random_state=seed, n_init=20)
    etiquetas = modelo.fit_predict(valores)
    if k not in puntajes:
        puntajes[k] = float(silhouette_score(valores, etiquetas))

    return {
        "modelo": modelo,
        "k": k,
        "etiquetas": pd.Series(
            etiquetas,
            index=matriz_estandarizada.index.copy(),
            name="cluster",
            dtype=int,
        ),
        "silhouette": puntajes[k],
        "silhouette_por_k": pd.Series(
            puntajes,
            name="silhouette",
            dtype=float,
        ).sort_index(),
    }


def matriz_correlacion(matriz_estandarizada):
    """Calcula correlaciones de Pearson entre características catch22."""
    _validar_matriz(matriz_estandarizada, minimo_filas=2)
    return matriz_estandarizada.corr()


def matriz_distancias(matriz_estandarizada, metrica="euclidean"):
    """Calcula las distancias entre pares de series en el espacio estandarizado."""
    valores = _validar_matriz(matriz_estandarizada, minimo_filas=2)
    if not isinstance(metrica, str) or not metrica.strip():
        raise ValueError("metrica debe ser un nombre de distancia válido.")

    try:
        distancias = squareform(pdist(valores, metric=metrica))
    except (TypeError, ValueError) as error:
        raise ValueError(f"Métrica de distancia no válida: {metrica}") from error
    return pd.DataFrame(
        distancias,
        index=matriz_estandarizada.index.copy(),
        columns=matriz_estandarizada.index.copy(),
    ).rename_axis(
        index=matriz_estandarizada.index.name,
        columns=matriz_estandarizada.index.name,
    )


def graficar_heatmap(matriz_estandarizada, ruta_salida=None):
    """Grafica la matriz estandarizada y opcionalmente guarda la figura."""
    _validar_matriz(matriz_estandarizada, minimo_filas=2)
    ancho = max(12, 0.55 * matriz_estandarizada.shape[1])
    alto = max(4.5, 0.65 * matriz_estandarizada.shape[0])
    figura, eje = plt.subplots(figsize=(ancho, alto))
    sns.heatmap(
        matriz_estandarizada,
        cmap="vlag",
        center=0,
        linewidths=0.25,
        cbar_kws={"label": "Valor estandarizado"},
        ax=eje,
    )
    eje.set_title("Características catch22 estandarizadas por serie")
    eje.set_xlabel("Característica catch22")
    eje.set_ylabel("Serie")
    eje.tick_params(axis="x", labelrotation=75)
    figura.tight_layout()

    if ruta_salida is not None:
        ruta = Path(ruta_salida)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        figura.savefig(ruta, dpi=150, bbox_inches="tight")
    return figura, eje
