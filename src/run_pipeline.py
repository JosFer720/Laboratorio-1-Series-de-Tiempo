import subprocess
import sys
from pathlib import Path

DIR_SRC = Path(__file__).resolve().parent

ETAPAS = [
    "01_ingesta.py",
    "02_limpieza.py",
    "03_series.py",
]

for etapa in ETAPAS:
    print("\n" + "#" * 60, flush=True)
    print(f"# EJECUTANDO {etapa}", flush=True)
    print("#" * 60, flush=True)
    resultado = subprocess.run([sys.executable, str(DIR_SRC / etapa)])
    if resultado.returncode != 0:
        print(f"\n>>> El pipeline se detuvo en {etapa} (fallo una validacion).")
        sys.exit(resultado.returncode)

print("\n" + "#" * 60)
print("# PIPELINE COMPLETO: series en data/processed/series/")
print("#" * 60)
