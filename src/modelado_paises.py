"""Punto de entrada reproducible para el análisis de países S4–S6."""

from modelado_s1_s2_s6 import ejecutar_modelado_paises


if __name__ == "__main__":
    resultados, comparativo, tabla_maestra = ejecutar_modelado_paises()
    for nombre, resultado in resultados.items():
        mejor = resultado["tabla"].loc[
            resultado["tabla"]["mejor_modelo"]
        ].iloc[0]
        print(
            f"{nombre}: {mejor['modelo']} · "
            f"MAE={mejor['MAE']:.2f} · RMSE={mejor['RMSE']:.2f}"
        )
    print("\nComparativo de Países:")
    print(comparativo.to_string(index=False))
    print(
        "\nTabla maestra: "
        f"{tabla_maestra['serie'].nunique()} series y "
        f"{len(tabla_maestra)} modelos."
    )
