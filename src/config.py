from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_SERIES = DIR_PROCESSED / "series"

RUTA_CRUDA   = DIR_RAW / "Base_Migracion_2009-2026jun.xlsx"  # entrada, nunca se modifica
HOJA_DATOS   = "Datos"
RUTA_INGESTA = DIR_PROCESSED / "01_ingesta.csv"        # <- 01_ingesta.py
RUTA_LIMPIO  = DIR_PROCESSED / "migracion_limpio.csv"  # <- 02_limpieza.py (dataset final)

COLUMNAS_CRUDAS = [
    "Año", "Mes cod", "Mes", "Vía", "Frontera", "País", "Región",
    "Región dos", "Regiones OMT", "MCEO", "Agrupación Residencia",
    "Tipo de Viajero", "Viajero",
]

N_FILAS_CRUDAS = 161036
N_MESES = 210           
FRECUENCIA = "MS"       
PERIODO_ESTACIONAL = 12 

PROPORCION_TRAIN = 0.70
N_TRAIN = int(N_MESES * PROPORCION_TRAIN)   # 147
N_TEST = N_MESES - N_TRAIN                  # 63

TIPOS_VISITANTE = ["Turista", "Excursionista"]

VALOR_CONTAMINANTE = "Cruceristas"

PAIS_EXCLUIDO = "Guatemala"
TOP_PAISES = ["El Salvador", "Estados Unidos de América", "Honduras"]

TOP_FRONTERAS = ["01 La Aurora", "07 Valle Nuevo", "09 San Cristóbal"]

SERIES = {
    "S0_total":           (None, None),
    "S1_la_aurora":       ("Frontera", "01 La Aurora"),
    "S2_valle_nuevo":     ("Frontera", "07 Valle Nuevo"),
    "S3_san_cristobal":   ("Frontera", "09 San Cristóbal"),
    "S4_el_salvador":     ("País", "El Salvador"),
    "S5_estados_unidos":  ("País", "Estados Unidos de América"),
    "S6_honduras":        ("País", "Honduras"),
}

SERIE_CONTEXTO = "S0_total_todos_tipos"

COL_FECHA = "fecha"
COL_VALOR = "viajeros"
