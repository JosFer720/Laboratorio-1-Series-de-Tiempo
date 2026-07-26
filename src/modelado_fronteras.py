from modelado_s1_s2_s6 import ejecutar_modelado_fronteras


if __name__ == "__main__":
    resultados, comparativo = ejecutar_modelado_fronteras()
    for nombre, resultado in resultados.items():
        mejor = resultado["tabla"].loc[
            resultado["tabla"]["mejor_modelo"]
        ].iloc[0]
        print(
            f"{nombre}: {mejor['modelo']} · "
            f"MAE={mejor['MAE']:.2f} · RMSE={mejor['RMSE']:.2f}"
        )
    print("\nComparativo de Fronteras:")
    print(comparativo.to_string(index=False))
