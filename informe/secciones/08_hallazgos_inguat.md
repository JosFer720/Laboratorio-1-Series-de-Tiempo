# Hallazgos útiles para INGUAT

Los resultados de S0 y S5 permiten adelantar cuatro hallazgos prácticos. Estos
deberán contrastarse con las otras cinco series y ya cuentan con evidencia
directa en los pronósticos y métricas disponibles.

1. **La recuperación cambió el nivel de las series más rápido de lo que los
   modelos pudieron aprender.** Tanto en el total mensual como en Estados
   Unidos, los pronósticos quedan por debajo de los valores observados después
   de 2022. Para planificación operativa conviene actualizar los modelos con
   frecuencia y no depender durante varios años de un ajuste cerrado en marzo
   de 2021.

2. **Estados Unidos conserva un patrón mensual más marcado que el total.** La
   fuerza estacional estimada fue 0.704 para S5 y 0.467 para S0. Esto sugiere
   que la programación de campañas, personal y capacidad dirigida a este
   mercado puede beneficiarse de una planificación específica por mes, en
   lugar de aplicar únicamente el comportamiento promedio del turismo total.

3. **El modelo con menor error todavía puede ser insuficiente para decisiones
   de capacidad.** El mejor RMSE fue aproximadamente 139,549 viajeros en S0 y
   26,794 en S5. Estas diferencias son grandes frente al volumen mensual, por
   lo que los pronósticos deben acompañarse de escenarios o márgenes de
   seguridad cuando se utilicen para asignar recursos.

4. **AIC y BIC no deben usarse solos para elegir un modelo.** En ambas series
   hubo candidatos con un ajuste interno atractivo que pronosticaron peor. En
   S5, incluso apareció un SARIMA numéricamente inestable. La evaluación sobre
   meses no utilizados durante el ajuste y el diagnóstico de residuos son
   indispensables antes de convertir un modelo en una herramienta de
   planificación.

Además, desde 2023 debe mantenerse visible la advertencia sobre el cambio de
granularidad de la variable País. Una variación posterior a esa fecha puede
combinar un movimiento real de viajeros con una modificación en la forma de
registrar el origen, por lo que no conviene interpretarla automáticamente como
crecimiento o caída del mercado.

