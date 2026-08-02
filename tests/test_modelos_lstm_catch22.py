import unittest

import numpy as np
from sklearn.preprocessing import MinMaxScaler

from modelos_lstm import (
    crear_ventanas_catch22,
    pronosticar_recursivo_catch22,
)


class _ModeloPersistencia:
    def predict(self, entrada, verbose=0):
        return np.asarray([[entrada[0, -1, 0]]], dtype=float)


class ModelosLstmCatch22Test(unittest.TestCase):
    def setUp(self):
        self.valores = np.linspace(0.0, 1.0, 40)
        self.caracteristicas = np.linspace(-2.0, 2.0, 22)

    def test_ventanas_conservan_23_columnas(self):
        X, y = crear_ventanas_catch22(
            self.valores,
            self.caracteristicas,
            lookback=12,
        )

        self.assertEqual(X.shape, (28, 12, 23))
        self.assertEqual(y.shape, (28,))
        np.testing.assert_allclose(X[0, :, 0], self.valores[:12])
        np.testing.assert_allclose(
            X[0, :, 1:],
            np.tile(self.caracteristicas, (12, 1)),
        )
        self.assertEqual(y[0], self.valores[12])

    def test_pronostico_recursivo_reutiliza_contexto_sin_datos_futuros(self):
        escalador = MinMaxScaler().fit(np.arange(100, dtype=float).reshape(-1, 1))
        ultima_ventana = np.linspace(0.2, 0.8, 12)

        predicciones = pronosticar_recursivo_catch22(
            modelo=_ModeloPersistencia(),
            escalador=escalador,
            ultima_ventana=ultima_ventana,
            catch22_features=self.caracteristicas,
            pasos=4,
        )

        esperada = escalador.inverse_transform([[ultima_ventana[-1]]])[0, 0]
        np.testing.assert_allclose(predicciones, np.repeat(esperada, 4))

    def test_rechaza_una_firma_con_dimension_incorrecta(self):
        with self.assertRaises(ValueError):
            crear_ventanas_catch22(
                self.valores,
                np.ones(21),
                lookback=12,
            )

    def test_rechaza_caracteristicas_no_finitas(self):
        caracteristicas = self.caracteristicas.copy()
        caracteristicas[3] = np.nan
        with self.assertRaises(ValueError):
            crear_ventanas_catch22(
                self.valores,
                caracteristicas,
                lookback=12,
            )


if __name__ == "__main__":
    unittest.main()
