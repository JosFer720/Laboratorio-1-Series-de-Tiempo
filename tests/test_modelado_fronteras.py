import unittest
from types import SimpleNamespace

import numpy as np
import pandas as pd

from modelado_s1_s2_s6 import (
    ESPECIFICACIONES,
    NOMBRES_FRONTERAS,
    calcular_comparativo_fronteras,
)


class ComparativoFronterasTest(unittest.TestCase):
    def test_s3_esta_en_el_contrato_de_modelado(self):
        self.assertIn("S3_san_cristobal", ESPECIFICACIONES)
        self.assertEqual(len(NOMBRES_FRONTERAS), 3)

    def test_comparativo_devuelve_metricas_y_rankings(self):
        indice = pd.date_range("2009-01-01", "2026-06-01", freq="MS")
        resultados = {}
        for posicion, nombre in enumerate(NOMBRES_FRONTERAS, start=1):
            eje = np.arange(len(indice), dtype=float)
            valores = (
                1000
                + posicion * 50
                + eje * posicion
                + 100 * np.sin(2 * np.pi * eje / 12)
            )
            serie = pd.Series(valores, index=indice, name=nombre)
            tendencia = pd.Series(
                1000 + posicion * 50 + eje * posicion,
                index=indice,
            )
            resultados[nombre] = {
                "serie": serie,
                "descomposicion": SimpleNamespace(trend=tendencia),
                "resumen": {
                    "fuerza_estacional": 0.2 * posicion,
                    "fuerza_tendencia": 0.3 * posicion,
                },
            }

        tabla = calcular_comparativo_fronteras(resultados)

        self.assertEqual(len(tabla), 3)
        self.assertEqual(set(tabla["ranking_estacionalidad"]), {1, 2, 3})
        self.assertIn("cagr_2009_2019_pct", tabla)
        self.assertIn("caida_2020_vs_2019_pct", tabla)
        self.assertIn("meses_primera_recuperacion_mensual", tabla)


if __name__ == "__main__":
    unittest.main()
