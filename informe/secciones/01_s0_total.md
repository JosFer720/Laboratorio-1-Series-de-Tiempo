# S0 — Total mensual

La serie S0 representa el total mensual de turistas y excursionistas
registrados. Contiene 210 observaciones, desde enero de 2009 hasta junio de
2026. Los primeros 147 meses se utilizaron como entrenamiento y los 63 meses
finales como prueba. Esta división es especialmente exigente porque el período
de prueba comienza en abril de 2021, cuando la movilidad todavía estaba
recuperándose del cierre provocado por la pandemia.

![S0: serie mensual y partición temporal](../img/final/s0_serie_particion.png)

La gráfica permite apreciar tres etapas. Antes de 2020 existía un crecimiento
general acompañado por picos mensuales repetitivos. En 2020 ocurrió una caída
extraordinaria que no corresponde a la estacionalidad normal. Después del
corte de prueba la serie recuperó rápidamente niveles cercanos a los
anteriores, pero ese nuevo comportamiento apenas estaba comenzando cuando se
cerró el entrenamiento. Esto explica por qué los modelos tienden a quedarse
por debajo de los valores observados entre 2022 y 2026.

## Tendencia y estacionalidad

![S0: descomposición del entrenamiento](../img/final/s0_descomposicion.png)

La descomposición confirma que la tendencia es el componente dominante. Su
fuerza estimada fue 0.821, mientras que la fuerza estacional fue 0.467. En
palabras sencillas, el total venía creciendo de manera importante y, sobre ese
crecimiento, aparecían meses altos y bajos que se repetían. El residuo aumenta
alrededor de la pandemia porque una descomposición tradicional no puede
explicar por completo un cierre tan abrupto.

![S0: media y variación móvil](../img/final/s0_varianza.png)

Como S0 no contiene ceros, se aplicó logaritmo. La transformación reduce el
peso de los meses con volúmenes muy altos y permite analizar los cambios en
términos más relativos. Aun así, el quiebre de 2020 continúa siendo visible y
debe tratarse como un cambio real del contexto, no como un valor atípico que
deba eliminarse.

## Estacionariedad y selección de órdenes

| Transformación | p ADF | p KPSS | Lectura |
|---|---:|---:|---|
| Nivel | 0.1520 | 0.0763 | Resultado mixto |
| Logaritmo | 0.1156 | 0.1000 | Resultado mixto |
| Logaritmo con `d=1` | 0.0277 | 0.1000 | Estacionaria según ambas pruebas |
| Logaritmo con `D=1` | 0.9636 | 0.0294 | No estacionaria |
| Logaritmo con `d=1` y `D=1` | <0.0001 | 0.1000 | Estacionaria según ambas pruebas |

En la escala logarítmica sin diferenciar, ADF todavía detecta una posible raíz
unitaria. Después de aplicar una diferencia regular, ADF y KPSS coinciden en
que la serie es estacionaria. También se probó una diferencia estacional
porque la ACF mantiene señales alrededor del rezago 12; por esa razón se
compararon candidatos con `d=1` y otros con `d=1, D=1`, sin asumir que la
diferencia estacional debía utilizarse obligatoriamente.

![S0: ACF y PACF](../img/final/s0_acf_pacf.png)

La ACF y la PACF de la serie transformada y diferenciada muestran actividad en
los primeros rezagos y en la zona estacional. Esto justificó comenzar con
órdenes pequeños, como ARIMA(1,1,1), y contrastarlos con dos alternativas
SARIMA. También se incluyó la sugerencia acotada de `auto_arima`, que propuso
un orden regular (2,0,0) y uno estacional (1,0,1,12).

## Comparación de modelos y pronóstico

| Modelo | AIC | BIC | MAE | RMSE | MAPE |
|---|---:|---:|---:|---:|---:|
| Prophet | N/A | N/A | 132,305 | 139,549 | 60.89% |
| ARIMA(1,1,1) | 92.36 | 101.27 | 154,873 | 169,524 | 59.30% |
| Suavizamiento exponencial simple | N/A | N/A | 165,373 | 180,598 | 62.91% |
| Holt-Winters | N/A | N/A | 178,162 | 191,100 | 69.82% |
| auto_arima(2,0,0)(1,0,1,12) | 66.50 | 80.96 | 183,943 | 198,151 | 72.25% |
| Seasonal Naive | N/A | N/A | 207,322 | 219,664 | 84.91% |
| SARIMA(1,1,1)(0,1,1,12) | 70.45 | 81.60 | 213,008 | 227,938 | 84.09% |
| SARIMA(2,1,1)(1,1,0,12) | 62.80 | 76.74 | 222,190 | 241,914 | 84.57% |

![S0: comparación de pronósticos](../img/final/s0_pronosticos.png)

Prophet obtuvo el menor RMSE, con aproximadamente 139,549 viajeros, y el menor
MAE, con 132,305. Sin embargo, su MAPE de 60.89% sigue siendo elevado. La
gráfica confirma que incluso el mejor candidato subestima buena parte de la
recuperación. Por lo tanto, se selecciona Prophet únicamente como el mejor
dentro del conjunto evaluado, no como un modelo de alta precisión.

![S0: RMSE por modelo](../img/final/s0_rmse_modelos.png)

La comparación también muestra que el candidato con menor AIC no fue el que
mejor pronosticó. SARIMA(2,1,1)(1,1,0,12) obtuvo el AIC más bajo entre los
candidatos ARIMA/SARIMA, pero presentó el RMSE más alto de S0. Este resultado
refuerza la necesidad de revisar el desempeño fuera de muestra en lugar de
elegir un modelo únicamente por su ajuste interno.

## Diagnóstico de residuos

![S0: diagnóstico del candidato ARIMA](../img/final/s0_residuos.png)

Entre los candidatos ARIMA, ARIMA(1,1,1) obtuvo `p=0.082` en la prueba
resumida de Ljung-Box. Al nivel de 5% no se rechaza la ausencia de
autocorrelación, aunque el resultado no es especialmente amplio. Su error en
prueba fue superior al de Prophet y los residuos de Prophet sí conservaron
autocorrelación. La conclusión es que ningún modelo resuelve por completo el
cambio de nivel pospandemia: Prophet pronostica menos mal, mientras
ARIMA(1,1,1) presenta un diagnóstico residual más favorable.
