import json
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent / "reglas"
CUENTA_POR_DEFECTO = "51959501"

REGLAS_NIT = {}
REGLAS_PUC = {}
def cargar_reglas():
    """Carga las reglas desde los archivos JSON."""
    with open(BASE_PATH / "nit_rules.json", "r", encoding="utf-8") as f:
        reglas_nit = json.load(f)
    with open(BASE_PATH / "puc_rules.json", "r", encoding="utf-8") as f:
        reglas_puc = json.load(f)
    return reglas_nit, reglas_puc

def buscar_por_nit(nit, reglas_nit):
    """Busca la cuenta contable por NIT."""
    return reglas_nit.get(nit)

def buscar_por_palabras(descripcion, reglas_puc):
    """Busca la cuenta contable por palabras clave en la descripción."""
    descripcion_lower = descripcion.lower()
    for cuenta, datos in reglas_puc.items():
        for palabra in datos["palabras_clave"]:
            if palabra.lower() in descripcion_lower:
                return cuenta
    return CUENTA_POR_DEFECTO


def recargar_reglas():
    """Recarga las reglas en caliente."""
    return cargar_reglas()
