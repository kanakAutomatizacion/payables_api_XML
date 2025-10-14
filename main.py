from fastapi import FastAPI, HTTPException, Header
from models import DatosEntrada
from services.reglas_service import cargar_reglas, recargar_reglas
from services.cuenta_contable import obtener_cuenta_contable

# Inicializar la app
app = FastAPI()

# Cargar reglas al iniciar la API
reglas_nit, reglas_puc = cargar_reglas()

@app.get("/")
async def root():
    return {"mensaje": "Bienvenido a la API de Payablea 🚀"}

@app.post("/cuenta_contable/")
async def asignar_cuenta(data: DatosEntrada):
    """
    Asigna cuentas contables basadas en los datos de la factura y las reglas configuradas.
    """
    factura = data.factura
    items = data.items
    resultados = []

    for item in items:
        cuenta = obtener_cuenta_contable(
            item.model_dump(),
            factura.Nit_Vendedor,
            reglas_nit,
            reglas_puc
        )
        item_resultado = item.model_dump()
        item_resultado["Cuenta_Contable"] = cuenta
        resultados.append(item_resultado)

    # Retornar todo el JSON original, pero con items actualizados
    return {
        "factura": factura.model_dump(),
        "items": resultados
    }

@app.post("/reload_reglas/")
async def reload_rules(x_api_key: str = Header(None)):
    """
    Recarga las reglas desde los archivos JSON (requiere API key).
    """
    if x_api_key != "mi_clave_secreta":
        raise HTTPException(status_code=401, detail="Acceso no autorizado")

    global reglas_nit, reglas_puc
    reglas_nit, reglas_puc = recargar_reglas()

    return {
        "mensaje": "Reglas recargadas correctamente",
        "total_nit": len(reglas_nit),
        "total_puc": len(reglas_puc)
    }

@app.post("/reload_reglas/")
async def reload_rules(x_api_key: str = Header(None)):
    """
    Recarga las reglas desde los archivos JSON (requiere API key).
    """
    if x_api_key != "mi_clave_secreta":
        raise HTTPException(status_code=401, detail="Acceso no autorizado")

    global reglas_nit, reglas_puc
    reglas_nit, reglas_puc = recargar_reglas()

    return {
        "mensaje": "Reglas recargadas correctamente",
        "total_nit": len(reglas_nit),
        "total_puc": len(reglas_puc)
    }
