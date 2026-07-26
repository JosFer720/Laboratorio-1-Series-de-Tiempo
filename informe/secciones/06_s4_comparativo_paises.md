# S4 y comparativo de Países

La versión canónica completa se encuentra en la sección 8 de
`informe/informe_final.md`. Este fragmento resume el análisis de S4–S6 para
facilitar el ensamblaje y la revisión cruzada.

## S4 — El Salvador

El Salvador conserva una categoría individual después del cambio de
granularidad de `País` de 2023, según las notas de la fuente. La serie tiene
210 meses, cinco ceros pandémicos en entrenamiento y utiliza `log1p`. Su
fuerza de tendencia es 0.783 y la estacional 0.402. En la escala transformada,
ADF y KPSS permiten `d=0`; se compararon ese candidato manual, alternativas
con `d=1`, SARIMA, `auto_arima`, Prophet, Holt-Winters, suavizamiento simple y
Seasonal Naive. Prophet obtuvo el menor RMSE: 59,455.

## Comparativo S4–S6

| País | Fuerza estacional | CAGR 2009–2019 | CV | Desv. log-diferencias | Caída 2020 vs 2019 |
|---|---:|---:|---:|---:|---:|
| El Salvador | 0.402 | 11.07% | 0.419 | 0.298 | 79.78% |
| Estados Unidos | 0.704 | 4.58% | 0.297 | 0.319 | 73.99% |
| Guatemala | 0.506 | 10.10% | 0.381 | 0.214 | 70.19% |

- Mayor estacionalidad: Estados Unidos.
- Mayor crecimiento prepandemia: El Salvador.
- Mayor volatilidad mes a mes: Estados Unidos; por dispersión relativa, El
  Salvador.
- Mayor caída pandémica: El Salvador.

Guatemala no puede compararse después de 2022 como país individual: sus 42
ceros posteriores son un cambio de reporte. Prophet se ejecutó correctamente
en S0–S6, por lo que no fue necesario activar el plan alternativo.
