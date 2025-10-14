import json
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent / "reglas"
CUENTA_POR_DEFECTO = "51959501"

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
    return None  # 🔹 antes devolvías la cuenta por defecto aquí


def obtener_cuenta_contable(factura, reglas_nit, reglas_puc):
    """
    Determina la cuenta contable:
    1. Primero por NIT
    2. Si no existe, por palabras clave del concepto
    3. Si no hay coincidencia, usa la cuenta por defecto
    """
    nit = factura.get("Nit_Vendedor")
    descripcion = factura.get("Descripcion_Item", "")

    # 1️⃣ Intentar buscar por NIT
    cuenta = buscar_por_nit(nit, reglas_nit)
    if cuenta:
        return cuenta

    # 2️⃣ Intentar buscar por palabras clave
    cuenta = buscar_por_palabras(descripcion, reglas_puc)
    if cuenta:
        return cuenta

    # 3️⃣ Si no encuentra nada, usar la cuenta por defecto
    return CUENTA_POR_DEFECTO


def recargar_reglas():
    """Recarga las reglas en caliente."""
    return cargar_reglas()
