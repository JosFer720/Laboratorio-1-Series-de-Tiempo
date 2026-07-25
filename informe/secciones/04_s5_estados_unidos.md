# S5 — Estados Unidos

S5 representa el total mensual asociado con Estados Unidos dentro de la
categoría País. La serie contiene 210 meses, desde enero de 2009 hasta junio de
2026, y utiliza la misma partición de 147 meses de entrenamiento y 63 meses de
prueba. A partir de 2023 existe un cambio en la granularidad disponible de la
variable País, por lo que los movimientos posteriores deben interpretarse
teniendo presente esa limitación metodológica.

![S5: serie mensual y partición temporal](../img/final/s5_serie_particion.png)

Antes de la pandemia la serie ya mostraba crecimiento y un patrón mensual
marcado. Entre abril y agosto de 2020 aparecen cinco meses en cero, coherentes
con el cierre extraordinario de la movilidad. Después de 2021 la recuperación
es clara y, desde 2023, los valores suelen superar el nivel observado durante
buena parte del entrenamiento. Como el corte ocurre en marzo de 2021, los
modelos no alcanzan a aprender completamente ese nuevo nivel.

## Tendencia y estacionalidad

![S5: descomposición del entrenamiento](../img/final/s5_descomposicion.png)

S5 presenta una fuerza de tendencia de 0.709 y una fuerza estacional de 0.704.
Ambos componentes tienen una presencia parecida: existe un crecimiento de
fondo, pero también picos y valles mensuales bastante repetitivos. El cierre
de 2020 rompe temporalmente los dos patrones y aumenta de forma visible el
componente residual.

![S5: media y variación móvil](../img/final/s5_varianza.png)

Debido a los cinco meses en cero no se utilizó el logaritmo convencional. En su
lugar se aplicó `log1p`, que admite cero y se comporta de manera similar al
logaritmo para valores grandes. Esta elección permite conservar la información
del cierre pandémico sin reemplazarla artificialmente.

## Estacionariedad y selección de órdenes

| Transformación | p ADF | p KPSS | Lectura |
|---|---:|---:|---|
| Nivel | 0.0208 | 0.1000 | Estacionaria según ambas pruebas |
| `log1p` | 0.0821 | 0.1000 | Resultado mixto |
| `log1p` con `d=1` | 0.0487 | 0.1000 | Estacionaria según ambas pruebas |
| `log1p` con `D=1` | 0.9286 | 0.0616 | Resultado mixto |
| `log1p` con `d=1` y `D=1` | <0.0001 | 0.1000 | Estacionaria según ambas pruebas |

Aunque el nivel original pasa ambas pruebas, la transformación `log1p` sin
diferenciar deja una lectura mixta. Después de aplicar `d=1`, ADF y KPSS
coinciden en estacionariedad. La diferencia estacional se incluyó en algunos
candidatos porque la ACF y la PACF muestran señales anuales, pero se mantuvo
ARIMA(1,1,1) como comparación para no imponer una diferenciación estacional
que pudiera resultar excesiva.

![S5: ACF y PACF](../img/final/s5_acf_pacf.png)

La sugerencia acotada de `auto_arima` fue (0,1,0) con componente estacional
(0,1,0,12). Esta opción se comparó con ARIMA(1,1,1) y dos SARIMA propuestos a
partir de los primeros rezagos y del patrón anual.

## Comparación de modelos y pronóstico

| Modelo | AIC | BIC | MAE | RMSE | MAPE |
|---|---:|---:|---:|---:|---:|
| ARIMA(1,1,1) | 431.91 | 440.82 | 22,975 | 26,794 | 47.08% |
| Prophet | N/A | N/A | 30,362 | 34,044 | 61.31% |
| Holt-Winters | N/A | N/A | 31,255 | 34,099 | 65.24% |
| Suavizamiento exponencial simple | N/A | N/A | 32,302 | 36,174 | 64.28% |
| auto_arima(0,1,0)(0,1,0,12) | 401.66 | 404.55 | 34,755 | 38,985 | 77.78% |
| SARIMA(1,1,1)(0,1,1,12) | 376.88 | 388.03 | 36,709 | 40,429 | 78.86% |
| Seasonal Naive | N/A | N/A | 40,733 | 43,733 | 88.69% |
| SARIMA(2,1,1)(1,1,0,12) | 366.87 | 380.80 | 227.3 billones | 1.35 mil billones | No interpretable |

![S5: comparación de pronósticos](../img/final/s5_pronosticos.png)

ARIMA(1,1,1) obtuvo el menor RMSE, con 26,794 viajeros, y un MAE de 22,975.
También presentó el MAPE más bajo, aunque 47.08% continúa siendo un error
considerable. La gráfica muestra la causa: el modelo mantiene un nivel cercano
a 25 mil viajeros, mientras la serie observada llega con frecuencia a valores
entre 50 mil y 70 mil durante los últimos años.

![S5: RMSE por modelo](../img/final/s5_rmse_modelos.png)

La figura omite de su escala al SARIMA(2,1,1)(1,1,0,12) porque generó
pronósticos explosivos que impedían distinguir los demás resultados. El modelo
no se borró: permanece en la tabla como evidencia de que fue inestable. Aunque
obtuvo el AIC más bajo entre los ARIMA/SARIMA, su comportamiento fuera de
muestra fue completamente inadecuado.

## Diagnóstico de residuos

![S5: diagnóstico del candidato ARIMA](../img/final/s5_residuos.png)

Los residuos de ARIMA(1,1,1) obtuvieron un valor cercano a `p=0.001` en la
prueba resumida de Ljung-Box, por lo que todavía conservan autocorrelación en
el rezago revisado. El modelo se mantiene como el candidato con menor RMSE,
pero el diagnóstico confirma que no explica toda la estructura temporal. El
error elevado y la subestimación persistente muestran que el cambio de nivel
pospandemia sigue siendo la principal limitación del pronóstico.
