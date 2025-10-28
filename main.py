from fastapi import FastAPI, Body, HTTPException
import xml.etree.ElementTree as ET
import re
from services.reglas_service import cargar_reglas
from services.cuenta_contable import obtener_cuenta_contable

app = FastAPI()

# Cargar reglas al iniciar
reglas_nit, reglas_puc = cargar_reglas()

def detectar_namespaces(xml_str):
    """
    Extrae todos los namespaces (prefijos -> URI) de un XML como diccionario.
    """
    pattern = re.compile(r'xmlns:([a-zA-Z0-9]+)="([^"]+)"')
    return dict(pattern.findall(xml_str))


@app.post("/cuenta_contable_xml/")
async def cuenta_contable_xml(xml_data: str = Body(..., media_type="application/xml")):
    try:
        xml_data = xml_data.strip()

        # 🔍 Detectar automáticamente los namespaces
        nsmap = detectar_namespaces(xml_data)
        if not nsmap:
            raise HTTPException(status_code=400, detail="No se detectaron namespaces en el XML")

        # Aseguramos prefijos esperados por UBL (cbc y cac)
        nsmap.setdefault("cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
        nsmap.setdefault("cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")

        root = ET.fromstring(xml_data)

        # --- FACTURA ---
        factura = {
            "N_Documento": (root.findtext(".//cbc:ID", namespaces=nsmap) or "").strip(),
            "CUFE": (root.findtext(".//cbc:UUID", namespaces=nsmap) or "").strip(),
            "Fecha_Documento": (root.findtext(".//cbc:IssueDate", namespaces=nsmap) or "").strip(),
            "Nombre_Vendedor": (root.findtext(".//cac:AccountingSupplierParty//cbc:Name", namespaces=nsmap) or "").strip(),
            "Nit_Vendedor": (root.findtext(".//cac:AccountingSupplierParty//cbc:ID", namespaces=nsmap) or "").strip(),
            "Correo_Vendedor": (root.findtext(".//cac:AccountingSupplierParty//cbc:ElectronicMail", namespaces=nsmap) or "").strip(),
            "Direccion_Vendedor": (root.findtext(".//cac:AccountingSupplierParty//cbc:StreetName", namespaces=nsmap) or "").strip(),
            "Codigo_Ciudad_Vendedor": (root.findtext(".//cac:AccountingSupplierParty//cbc:CitySubdivisionName", namespaces=nsmap) or "").strip(),
            "Telefono_Vendedor": (root.findtext(".//cac:AccountingSupplierParty//cbc:Telephone", namespaces=nsmap) or "").strip(),
            "Contacto_Vendedor": (root.findtext(".//cac:AccountingSupplierParty//cac:Contact//cbc:Name", namespaces=nsmap) or "").strip(),
            "Cantidad_Items": str(len(root.findall(".//cac:InvoiceLine", namespaces=nsmap))),
            "Monto_Total": (root.findtext(".//cbc:LineExtensionAmount", namespaces=nsmap) or "").strip(),
            "Monto_Sin_Impuestos": (root.findtext(".//cbc:TaxExclusiveAmount", namespaces=nsmap) or "").strip(),
            "Monto_Con_Impuestos": (root.findtext(".//cbc:TaxInclusiveAmount", namespaces=nsmap) or "").strip(),
            "Monto_Pagar": (root.findtext(".//cbc:PayableAmount", namespaces=nsmap) or "").strip(),
            "Nombre_Comprador": (root.findtext(".//cac:AccountingCustomerParty//cbc:Name", namespaces=nsmap) or "").strip(),
            "Nit_Comprador": (root.findtext(".//cac:AccountingCustomerParty//cbc:ID", namespaces=nsmap) or "").strip(),
            "Moneda_Documento": (root.findtext(".//cbc:DocumentCurrencyCode", namespaces=nsmap) or "").strip()
        }

        # --- ITEMS ---
        items = []
        for item in root.findall(".//cac:InvoiceLine", namespaces=nsmap):
            descripcion = (item.findtext(".//cbc:Description", namespaces=nsmap) or "").strip()
            id_item = (item.findtext(".//cbc:ID", namespaces=nsmap) or "").strip()
            cantidad = (item.findtext(".//cbc:InvoicedQuantity", namespaces=nsmap) or "").strip()
            monto1 = (item.findtext(".//cbc:LineExtensionAmount", namespaces=nsmap) or "").strip()
            monto2 = (item.findtext(".//cbc:PriceAmount", namespaces=nsmap) or "").strip()
            monto_base = (item.findtext(".//cbc:BaseQuantity", namespaces=nsmap) or "").strip()

            cuenta = obtener_cuenta_contable(
                {"Descripcion_Item": descripcion},
                factura["Nit_Vendedor"],
                reglas_nit,
                reglas_puc
            )

            keycontable = f"{factura['Nit_Comprador']}_{factura['Nit_Vendedor']}_{descripcion}"

            items.append({
                "Id_Item": id_item,
                "Cantidad_Item": cantidad,
                "Monto1_Item": monto1,
                "Monto2_Item": monto2,
                "MontoBase_Item": monto_base,
                "Descripcion_Item": descripcion,
                "cuentacontable": cuenta,
                "keycontable": keycontable
            })

        return {"factura": factura, "items": items}

    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar XML: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

