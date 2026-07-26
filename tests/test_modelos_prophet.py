import unittest

import numpy as np
import pandas as pd

import config
from modelos_prophet import (
    ajustar_prophet,
    ajustar_y_pronosticar_prophet,
    convertir_a_prophet,
    pronosticar_prophet,
)


def cargar(nombre):
    ruta = config.DIR_SERIES / f"{nombre}.csv"
    datos = pd.read_csv(ruta, parse_dates=[config.COL_FECHA])
    serie = datos.set_index(config.COL_FECHA)[config.COL_VALOR]
    serie.index.freq = config.FRECUENCIA
    serie.name = nombre
    return serie


class ModelosProphetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s1 = cargar("S1_la_aurora")
        cls.s6 = cargar("S6_guatemala")
        cls.train = cls.s1.iloc[: config.N_TRAIN]
        cls.test = cls.s1.iloc[config.N_TRAIN :]

    def test_convertir_a_prophet_produce_columnas_ds_y(self):
        datos = convertir_a_prophet(self.train)
        self.assertListEqual(list(datos.columns), ["ds", "y"])
        self.assertEqual(len(datos), len(self.train))
        self.assertTrue((datos["ds"].to_numpy() == self.train.index.to_numpy()).all())

    def test_ajustar_prophet_admite_serie_con_ceros(self):
        resultado = ajustar_prophet(self.s6.iloc[: config.N_TRAIN], nombre_serie="S6_guatemala")
        self.assertEqual(resultado["modelo"], "Prophet")
        self.assertTrue(np.isnan(resultado["AIC"]))
        self.assertTrue(np.isnan(resultado["BIC"]))

    def test_pronostico_genera_el_horizonte_completo_y_no_negativo(self):
        resultado = ajustar_y_pronosticar_prophet(
            train=self.train,
            horizonte=config.N_TEST,
            indice_pronostico=self.test.index,
            nombre_serie="S1_la_aurora",
        )
        pronostico = resultado["pronostico"]
        self.assertEqual(len(pronostico), config.N_TEST)
        self.assertTrue(pronostico.index.equals(self.test.index))
        self.assertTrue(np.isfinite(pronostico).all())
        self.assertTrue((pronostico >= 0).all())

    def test_pronosticar_prophet_rechaza_indice_de_longitud_distinta(self):
        resultado = ajustar_prophet(self.train, nombre_serie="S1_la_aurora")
        with self.assertRaises(ValueError):
            pronosticar_prophet(
                resultado,
                horizonte=config.N_TEST,
                indice_pronostico=self.test.index[:-1],
            )

    def test_parametros_se_conservan_en_el_resultado(self):
        resultado = ajustar_prophet(
            self.train,
            nombre_serie="S1_la_aurora",
            estacionalidad_anual=True,
            modo_estacional="additive",
        )
        self.assertEqual(
            resultado["parametros"],
            {
                "crecimiento": "linear",
                "estacionalidad_anual": True,
                "modo_estacional": "additive",
            },
        )

    def test_modo_estacional_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            ajustar_prophet(self.train, modo_estacional="otro")


if __name__ == "__main__":
    unittest.main()
