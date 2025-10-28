from fastapi import FastAPI, Body, HTTPException
import xml.etree.ElementTree as ET
from services.cuenta_contable import obtener_cuenta_contable
from services.reglas_service import cargar_reglas

app = FastAPI()

# Cargar las reglas
reglas_nit, reglas_puc = cargar_reglas()

@app.post("/cuenta_contable_xml/")
async def cuenta_contable_xml(xml_data: str = Body(..., media_type="application/xml")):
    try:
        xml_data = xml_data.lstrip()  # elimina espacios o saltos antes del <?xml
        root = ET.fromstring(xml_data)

        # --- Namespaces UBL ---
        ns = {
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        }

        # --- Extraer datos principales ---
        nit_vendedor = root.find('.//cbc:CompanyID', ns)
        nit_vendedor = nit_vendedor.text if nit_vendedor is not None else ""

        descripcion_items = []
        for item in root.findall('.//cac:InvoiceLine', ns):
            descripcion = item.find('.//cbc:Description', ns)
            descripcion_items.append(descripcion.text if descripcion is not None else "")

        # --- Generar salida ---
        items_result = []
        for desc in descripcion_items:
            cuenta = obtener_cuenta_contable(
                {"Descripcion_Item": desc},
                nit_vendedor,
                reglas_nit,
                reglas_puc
            )
            items_result.append({
                "Descripcion_Item": desc,
                "cuentacontable": cuenta
            })

        return {
            "factura": {"Nit_Vendedor": nit_vendedor},
            "items": items_result
        }

    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar XML: {e}")

