from fastapi import FastAPI, HTTPException, Header, Request
import xmltodict
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

    for item in items:
        cuenta = obtener_cuenta_contable(
            item.model_dump(),
            factura.Nit_Vendedor,
            reglas_nit,
            reglas_puc
        )
        item.cuentacontable = cuenta

    return {
        "factura": factura.model_dump(),
        "items": [item.model_dump() for item in items]
    }


@app.post("/cuenta_contable_xml/")
async def asignar_cuenta_desde_xml(request: Request):
    """
    Recibe un XML, lo convierte a JSON y aplica las reglas contables.
    """
    try:
        # 🔹 Leer el cuerpo XML
        xml_data = await request.body()
        data_dict = xmltodict.parse(xml_data)

        # 🔹 Extraer factura e items (ajusta si tus tags se llaman diferente)
        factura = data_dict.get("factura", {})
        items = data_dict.get("factura", {}).get("items", {}).get("item", [])

        # Asegurar que `items` sea una lista
        if isinstance(items, dict):
            items = [items]

        # 🔹 Procesar cada item
        for item in items:
            descripcion = item.get("Descripcion_Item", "")
            nit_vendedor = factura.get("Nit_Vendedor", "")
            cuenta = obtener_cuenta_contable(
                item,
                nit_vendedor,
                reglas_nit,
                reglas_puc
            )
            item["cuentacontable"] = cuenta

        return {
            "factura": factura,
            "items": items
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar XML: {str(e)}")


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

