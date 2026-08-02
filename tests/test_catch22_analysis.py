import tempfile
import unittest
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from catch22_analysis import (
    calcular_clustering,
    calcular_pca,
    construir_matriz_catch22,
    estandarizar_matriz,
    extraer_catch22,
    graficar_heatmap,
    matriz_correlacion,
    matriz_distancias,
)


class Catch22AnalysisTest(unittest.TestCase):
    def setUp(self):
        tiempo = np.arange(120, dtype=float)
        self.series = {
            "creciente": pd.Series(tiempo + 5 * np.sin(2 * np.pi * tiempo / 12)),
            "estacional": pd.Series(20 * np.sin(2 * np.pi * tiempo / 12)),
            "alternante": pd.Series(np.where(tiempo % 2 == 0, -10.0, 10.0)),
        }

    def test_extrae_exactamente_22_caracteristicas_finitas(self):
        resultado = extraer_catch22(self.series["creciente"])

        self.assertEqual(len(resultado), 22)
        self.assertEqual(len(set(resultado)), 22)
        self.assertTrue(np.isfinite(list(resultado.values())).all())

    def test_construye_y_estandariza_matriz_con_etiquetas(self):
        matriz = construir_matriz_catch22(self.series)
        estandarizada = estandarizar_matriz(matriz)

        self.assertEqual(matriz.shape, (3, 22))
        self.assertEqual(list(matriz.index), list(self.series))
        pd.testing.assert_index_equal(estandarizada.index, matriz.index)
        pd.testing.assert_index_equal(estandarizada.columns, matriz.columns)
        np.testing.assert_allclose(
            estandarizada.mean(axis=0).to_numpy(),
            np.zeros(22),
            atol=1e-12,
        )

    def test_pca_devuelve_coordenadas_cargas_y_varianza(self):
        matriz = pd.DataFrame(
            [[-2, -1, 0], [-1, 0, 1], [1, 0, -1], [2, 1, 0]],
            index=["S0", "S1", "S2", "S3"],
            columns=["f1", "f2", "f3"],
        )
        resultado = calcular_pca(matriz, n_componentes=2)

        self.assertEqual(resultado["coordenadas"].shape, (4, 2))
        self.assertEqual(resultado["cargas"].shape, (3, 2))
        self.assertEqual(len(resultado["varianza_explicada"]), 2)
        self.assertTrue((resultado["varianza_explicada"] >= 0).all())

    def test_clustering_automatico_elige_k_valido_y_alinea_etiquetas(self):
        matriz = pd.DataFrame(
            [
                [-5.0, -5.0],
                [-4.8, -5.1],
                [0.0, 0.1],
                [0.2, -0.1],
                [5.0, 5.0],
                [5.1, 4.8],
                [4.9, 5.2],
            ],
            index=[f"S{indice}" for indice in range(7)],
            columns=["f1", "f2"],
        )
        resultado = calcular_clustering(matriz)

        self.assertIn(resultado["k"], range(2, 6))
        self.assertEqual(len(resultado["etiquetas"]), 7)
        pd.testing.assert_index_equal(resultado["etiquetas"].index, matriz.index)
        self.assertTrue(-1 <= resultado["silhouette"] <= 1)

    def test_correlaciones_y_distancias_son_matrices_cuadradas(self):
        matriz = pd.DataFrame(
            [[-1.0, 0.5, 2.0], [0.0, -1.0, 1.0], [1.0, 0.5, -1.0]],
            index=["S0", "S1", "S2"],
            columns=["f1", "f2", "f3"],
        )
        correlaciones = matriz_correlacion(matriz)
        distancias = matriz_distancias(matriz)

        self.assertEqual(correlaciones.shape, (3, 3))
        self.assertEqual(distancias.shape, (3, 3))
        np.testing.assert_allclose(distancias, distancias.T)
        np.testing.assert_allclose(np.diag(distancias), np.zeros(3))

    def test_heatmap_guarda_una_figura(self):
        matriz = pd.DataFrame(
            [[-1.0, 0.0, 1.0], [1.0, 0.0, -1.0]],
            index=["S0", "S1"],
            columns=["f1", "f2", "f3"],
        )
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "heatmap.png"
            figura, _ = graficar_heatmap(matriz, ruta)
            self.assertTrue(ruta.exists())
            self.assertGreater(ruta.stat().st_size, 0)
            figura.clear()

    def test_rechaza_series_invalidas(self):
        with self.assertRaises(ValueError):
            extraer_catch22(pd.Series([1.0, np.nan, 3.0]))
        with self.assertRaises(ValueError):
            extraer_catch22(pd.Series([4.0, 4.0, 4.0]))


if __name__ == "__main__":
    unittest.main()
