import tempfile
import unittest
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from evaluacion_modelos import (
    calcular_mape_seguro,
    calcular_metricas,
    combinar_metricas,
    construir_resultado,
    diagnosticar_residuos,
    graficar_real_pronostico,
    tabla_comparativa,
    validar_alineacion,
)


class EvaluacionModelosTest(unittest.TestCase):
    def setUp(self):
        self.indice = pd.date_range("2021-01-01", periods=5, freq="MS")
        self.real = pd.Series([10, 20, 30, 40, 50], index=self.indice)
        self.pred = pd.Series([12, 18, 33, 39, 48], index=self.indice)

    def test_metricas_conocidas(self):
        resultado = calcular_metricas(self.real, self.pred)

        self.assertAlmostEqual(resultado["MAE"], 2.0)
        self.assertAlmostEqual(resultado["RMSE"], np.sqrt(4.4))
        self.assertAlmostEqual(resultado["MAPE"], 9.3)

    def test_mape_ignora_ceros_sin_dividir_por_cero(self):
        real = pd.Series([0, 10, 20])
        pred = pd.Series([7, 8, 22])

        self.assertAlmostEqual(calcular_mape_seguro(real, pred), 15.0)

    def test_mape_es_nan_si_todos_los_reales_son_cero(self):
        valor = calcular_mape_seguro(pd.Series([0, 0]), pd.Series([1, 2]))

        self.assertTrue(np.isnan(valor))

    def test_indices_distintos_no_se_comparan(self):
        pred = self.pred.copy()
        pred.index = pd.date_range("2022-01-01", periods=5, freq="MS")

        with self.assertRaises(ValueError):
            validar_alineacion(self.real, pred)

    def test_diagnostico_devuelve_ljung_box(self):
        residuos = pd.Series(
            [0.2, -0.1, 0.3, -0.2, 0.1, -0.4] * 5
        )
        resultado = diagnosticar_residuos(residuos, lags=6)

        self.assertEqual(resultado["n_residuos"], 30)
        self.assertTrue(0 <= resultado["Ljung_Box_p"] <= 1)

    def test_tabla_marca_un_mejor_modelo_por_serie(self):
        resultados = [
            construir_resultado(
                "S0", "Modelo A", self.real, self.pred
            ),
            construir_resultado(
                "S0", "Modelo B", self.real, self.real
            ),
        ]
        tabla = tabla_comparativa(resultados)

        self.assertEqual(int(tabla["mejor_modelo"].sum()), 1)
        self.assertEqual(
            tabla.loc[tabla["mejor_modelo"], "modelo"].iloc[0],
            "Modelo B",
        )

    def test_combina_archivos_y_recalcula_el_mejor(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta_a = Path(temporal) / "a.csv"
            ruta_b = Path(temporal) / "b.csv"
            tabla_comparativa([
                construir_resultado("S0", "A", self.real, self.pred)
            ]).to_csv(ruta_a, index=False)
            tabla_comparativa([
                construir_resultado("S1", "B", self.real, self.real)
            ]).to_csv(ruta_b, index=False)

            combinada = combinar_metricas([ruta_a, ruta_b])

        self.assertEqual(set(combinada["serie"]), {"S0", "S1"})
        self.assertEqual(int(combinada["mejor_modelo"].sum()), 2)

    def test_grafica_guarda_archivo(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "comparacion.png"
            figura, _ = graficar_real_pronostico(
                self.real,
                {"Modelo": self.pred},
                "Prueba",
                ruta,
            )
            self.assertTrue(ruta.exists())
            self.assertGreater(ruta.stat().st_size, 0)
            figura.clear()


if __name__ == "__main__":
    unittest.main()
