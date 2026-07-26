import unittest
from types import SimpleNamespace

import numpy as np
import pandas as pd

from modelado_s1_s2_s6 import (
    ESPECIFICACIONES,
    NOMBRES_PAISES,
    calcular_comparativo_paises,
    construir_tabla_maestra,
)


class ModeladoPaisesTest(unittest.TestCase):
    def test_s4_s5_s6_estan_en_el_contrato(self):
        self.assertEqual(
            NOMBRES_PAISES,
            (
                "S4_el_salvador",
                "S5_estados_unidos",
                "S6_guatemala",
            ),
        )
        self.assertTrue(set(NOMBRES_PAISES).issubset(ESPECIFICACIONES))

    def test_comparativo_paises_usa_las_mismas_metricas(self):
        indice = pd.date_range("2009-01-01", "2026-06-01", freq="MS")
        resultados = {}
        for posicion, nombre in enumerate(NOMBRES_PAISES, start=1):
            eje = np.arange(len(indice), dtype=float)
            serie = pd.Series(
                1500
                + posicion * 100
                + eje * posicion
                + 120 * np.sin(2 * np.pi * eje / 12),
                index=indice,
                name=nombre,
            )
            resultados[nombre] = {
                "serie": serie,
                "descomposicion": SimpleNamespace(
                    trend=pd.Series(
                        1500 + posicion * 100 + eje * posicion,
                        index=indice,
                    )
                ),
                "resumen": {
                    "fuerza_estacional": 0.15 * posicion,
                    "fuerza_tendencia": 0.25 * posicion,
                },
            }

        tabla = calcular_comparativo_paises(resultados)

        self.assertEqual(len(tabla), 3)
        self.assertIn("pais", tabla)
        self.assertIn("cagr_2009_2019_pct", tabla)
        self.assertIn("meses_hasta_recuperacion_sostenida", tabla)
        self.assertEqual(set(tabla["ranking_estacionalidad"]), {1, 2, 3})

    def test_tabla_maestra_conserva_s0_s6_sin_duplicar_s5(self):
        def filas(series):
            return pd.DataFrame(
                [
                    {
                        "serie": serie,
                        "modelo": modelo,
                        "RMSE": rmse,
                        "mejor_modelo": False,
                    }
                    for serie in series
                    for modelo, rmse in [("A", 20.0), ("B", 10.0)]
                ]
            )

        s0_s5 = filas(["S0_total", "S5_estados_unidos"])
        fronteras = filas(
            ["S1_la_aurora", "S2_valle_nuevo", "S3_san_cristobal"]
        )
        paises = filas(
            ["S4_el_salvador", "S5_estados_unidos", "S6_guatemala"]
        )

        tabla = construir_tabla_maestra(s0_s5, fronteras, paises)

        self.assertEqual(tabla["serie"].nunique(), 7)
        self.assertEqual(len(tabla), 14)
        self.assertEqual(int(tabla["mejor_modelo"].sum()), 7)
        self.assertEqual(
            len(tabla[tabla["serie"].eq("S5_estados_unidos")]),
            2,
        )


if __name__ == "__main__":
    unittest.main()
