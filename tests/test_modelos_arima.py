import unittest

import numpy as np
import pandas as pd

import config
from modelos_arima import (
    ajustar_y_pronosticar_arima,
    invertir_transformacion,
    sugerir_auto_arima,
    transformar_serie,
)


def cargar(nombre):
    ruta = config.DIR_SERIES / f"{nombre}.csv"
    datos = pd.read_csv(ruta, parse_dates=[config.COL_FECHA])
    serie = datos.set_index(config.COL_FECHA)[config.COL_VALOR]
    serie.index.freq = config.FRECUENCIA
    serie.name = nombre
    return serie


class ModelosArimaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s0 = cargar("S0_total")
        cls.s6 = cargar("S6_guatemala")
        cls.train = cls.s0.iloc[:config.N_TRAIN]
        cls.test = cls.s0.iloc[config.N_TRAIN:]

    def test_log1p_admite_ceros_y_regresa_a_la_escala_original(self):
        transformada = transformar_serie(self.s6, "log1p")
        recuperada = invertir_transformacion(transformada, "log1p")

        self.assertTrue(np.allclose(recuperada, self.s6))
        self.assertTrue(recuperada.index.equals(self.s6.index))

    def test_log_rechaza_la_serie_con_ceros(self):
        with self.assertRaises(ValueError):
            transformar_serie(self.s6, "log")

    def test_arima_genera_el_horizonte_completo(self):
        resultado = ajustar_y_pronosticar_arima(
            train=self.train,
            orden=(1, 1, 1),
            horizonte=config.N_TEST,
            indice_pronostico=self.test.index,
            transformacion="log",
            nombre_serie="S0_total",
        )

        pronostico = resultado["pronostico"]
        self.assertEqual(len(pronostico), config.N_TEST)
        self.assertTrue(pronostico.index.equals(self.test.index))
        self.assertTrue(np.isfinite(pronostico).all())
        self.assertTrue((pronostico >= 0).all())
        self.assertTrue(np.isfinite(resultado["AIC"]))
        self.assertTrue(np.isfinite(resultado["BIC"]))

    def test_sarima_genera_el_horizonte_completo(self):
        resultado = ajustar_y_pronosticar_arima(
            train=self.train,
            orden=(1, 1, 1),
            orden_estacional=(0, 1, 1, 12),
            horizonte=config.N_TEST,
            indice_pronostico=self.test.index,
            transformacion="log",
            nombre_serie="S0_total",
        )

        pronostico = resultado["pronostico"]
        self.assertEqual(len(pronostico), config.N_TEST)
        self.assertTrue(pronostico.index.equals(self.test.index))
        self.assertEqual(
            resultado["parametros"]["orden_estacional"],
            (0, 1, 1, 12),
        )

    def test_auto_arima_devuelve_ordenes_y_metricas(self):
        resultado = sugerir_auto_arima(
            self.train,
            transformacion="log",
            max_p=1,
            max_q=1,
            max_P=1,
            max_Q=1,
        )

        self.assertEqual(len(resultado["orden"]), 3)
        self.assertEqual(len(resultado["orden_estacional"]), 4)
        self.assertTrue(np.isfinite(resultado["AIC"]))
        self.assertTrue(np.isfinite(resultado["BIC"]))


if __name__ == "__main__":
    unittest.main()
