import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_VENV = RAIZ / ".venv"
REQUIREMENTS = RAIZ / "requirements.txt"

# El ejecutable de python dentro del venv cambia segun el sistema operativo.
if sys.platform == "win32":
    PYTHON_VENV = DIR_VENV / "Scripts" / "python.exe"
else:
    PYTHON_VENV = DIR_VENV / "bin" / "python"

print("=" * 60)
print("ETAPA 0 | SETUP DEL ENTORNO")
print("=" * 60)


def crear_con_venv():
    resultado = subprocess.run(
        [sys.executable, "-m", "venv", str(DIR_VENV)],
        capture_output=True, text=True,
    )
    return resultado.returncode == 0, resultado.stderr


def crear_con_virtualenv():
    print("[plan B]   instalando virtualenv en el area del usuario ...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--user",
         "--break-system-packages", "--quiet", "virtualenv"],
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "virtualenv", str(DIR_VENV)],
        check=True,
    )


# --- Crear el venv (si no existe) ---
if PYTHON_VENV.exists():
    print(f"[ok]       ya existe un venv en {DIR_VENV}")
else:
    print(f"[creando]  entorno virtual en {DIR_VENV} ...")
    ok, error = crear_con_venv()

    if ok:
        print("[ok]       venv creado")
    else:
        print("[aviso]    el modulo `venv` fallo (falta ensurepip / python3-venv)")
        try:
            crear_con_virtualenv()
            print("[ok]       venv creado con virtualenv")
        except subprocess.CalledProcessError:
            print("\n[FALLO]    no se pudo crear el entorno virtual.")
            print("           Opciones:")
            print("             sudo apt install python3-venv      (Debian/Ubuntu/WSL)")
            print("             pip install --user virtualenv      (sin permisos de admin)")
            print(f"\n           Error original de venv:\n{error}")
            sys.exit(1)

# --- Instalar dependencias dentro del venv ---
print(f"[instalando] dependencias de {REQUIREMENTS.name} ...")
subprocess.run([str(PYTHON_VENV), "-m", "pip", "install", "--upgrade", "--quiet", "pip"], check=True)
subprocess.run([str(PYTHON_VENV), "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)
print("[ok]       dependencias instaladas")

print("\nListo. Activa el venv y corre el pipeline:")
if sys.platform == "win32":
    print("    .venv\\Scripts\\activate")
    print("    python src\\run_pipeline.py")
else:
    print("    source .venv/bin/activate")
    print("    python src/run_pipeline.py")
