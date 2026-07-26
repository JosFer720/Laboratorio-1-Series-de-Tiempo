# Metodología de modelado y evaluación

Para comparar las series bajo las mismas condiciones se mantuvo la partición
temporal definida desde el avance. Los primeros 147 meses, desde enero de 2009
hasta marzo de 2021, se utilizaron para estudiar el comportamiento de cada
serie y ajustar los modelos. Los 63 meses restantes, desde abril de 2021 hasta
junio de 2026, se reservaron para medir qué tan bien pronostica cada método.
Los datos no se mezclaron ni se ordenaron al azar, porque en una serie de
tiempo el orden de los meses es parte esencial de la información.

Antes de modelar se revisaron la tendencia, la estacionalidad, la estabilidad
de la media y la variación. Se compararon descomposiciones aditiva y
multiplicativa; la relación entre media y desviación anual prepandemia se usó
para justificar cuál describe mejor la amplitud. También se utilizaron las
pruebas ADF y KPSS, junto con gráficas ACF y PACF separadas después de `d=1` y
después de `d=1,D=1`, para proponer valores razonables de `p`, `d`, `q`, `P`,
`D` y `Q`. Estas
decisiones se tomaron únicamente con el período de entrenamiento, evitando
utilizar anticipadamente la información de prueba.

En cada serie se compararon al menos tres candidatos ARIMA o SARIMA, una
sugerencia acotada de `auto_arima`, Prophet, Holt-Winters, suavizamiento
exponencial simple y Seasonal Naive. Para todos los métodos se generaron
exactamente 63 pronósticos mensuales. El desempeño se midió con MAE y RMSE
sobre los mismos meses; MAPE se incluyó como referencia adicional cuando el
valor observado era distinto de cero. AIC y BIC se utilizaron solamente para
comparar candidatos ARIMA/SARIMA ajustados sobre la misma serie.

El mejor modelo de cada serie se eligió principalmente por su RMSE en prueba,
pero también se revisaron los residuos con su serie temporal, ACF, histograma,
gráfico Q-Q, Ljung-Box y Jarque-Bera. Esto es
importante porque un modelo puede ajustarse bien al entrenamiento y aun así
fallar al pronosticar. De hecho, el corte elegido deja buena parte de la
recuperación pospandemia dentro de la prueba; por eso los errores también
reflejan un cambio de comportamiento que los modelos no habían visto durante
su ajuste.

Para S0 y S1–S3 se aplicó una transformación logarítmica porque todos los
valores son positivos y la relación positiva entre nivel y amplitud disminuye
después de transformar. En S5 se utilizó `log1p`, ya que contiene cinco meses en
cero durante el cierre de 2020. Esta transformación permite conservar esos
meses sin sustituirlos ni eliminarlos. Finalmente, todos los pronósticos se
devolvieron a su escala original para que las métricas y gráficas pudieran
interpretarse directamente en cantidad de viajeros.

