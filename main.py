from fastapi import FastAPI, Body, HTTPException
import xml.etree.ElementTree as ET
from services.reglas_service import cargar_reglas
from services.cuenta_contable import obtener_cuenta_contable

app = FastAPI()

# Cargar reglas
reglas_nit, reglas_puc = cargar_reglas()

@app.post("/cuenta_contable_xml/")
async def cuenta_contable_xml(xml_data: str = Body(..., media_type="application/xml")):
    try:
        xml_data = xml_data.lstrip()  # eliminar espacios o saltos antes del <?xml
        root = ET.fromstring(xml_data)

        # --- Namespaces comunes de las facturas electrónicas UBL ---
        ns = {
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        }

        # --- FACTURA ---
        factura = {
            "N_Documento": (root.findtext('.//cbc:ID', namespaces=ns) or "").strip(),
            "CUFE": (root.findtext('.//cbc:UUID', namespaces=ns) or "").strip(),
            "Fecha_Documento": (root.findtext('.//cbc:IssueDate', namespaces=ns) or "").strip(),
            "Nombre_Vendedor": (root.findtext('.//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name', namespaces=ns) or "").strip(),
            "Nit_Vendedor": (root.findtext('.//cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID', namespaces=ns) or "").strip(),
            "Correo_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cbc:ElectronicMail', namespaces=ns) or "").strip(),
            "Direccion_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cac:Address/cbc:StreetName', namespaces=ns) or "").strip(),
            "Codigo_Ciudad_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cac:Address/cbc:CitySubdivisionName', namespaces=ns) or "").strip(),
            "Telefono_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cbc:Telephone', namespaces=ns) or "").strip(),
            "Contacto_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cac:Contact/cbc:Name', namespaces=ns) or "").strip(),
            "Cantidad_Items": str(len(root.findall('.//cac:InvoiceLine', namespaces=ns))),
            "Monto_Total": (root.findtext('.//cbc:LineExtensionAmount', namespaces=ns) or "").strip(),
            "Monto_Sin_Impuestos": (root.findtext('.//cbc:TaxExclusiveAmount', namespaces=ns) or "").strip(),
            "Monto_Con_Impuestos": (root.findtext('.//cbc:TaxInclusiveAmount', namespaces=ns) or "").strip(),
            "Monto_Pagar": (root.findtext('.//cbc:PayableAmount', namespaces=ns) or "").strip(),
            "Nombre_Comprador": (root.findtext('.//cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name', namespaces=ns) or "").strip(),
            "Nit_Comprador": (root.findtext('.//cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID', namespaces=ns) or "").strip(),
            "Moneda_Documento": (root.findtext('.//cbc:DocumentCurrencyCode', namespaces=ns) or "").strip()
        }

        # --- ITEMS ---
        items = []
        for item in root.findall('.//cac:InvoiceLine', ns):
            descripcion = (item.findtext('.//cbc:Description', ns) or "").strip()
            id_item = (item.findtext('.//cbc:ID', ns) or "").strip()
            cantidad = (item.findtext('.//cbc:InvoicedQuantity', ns) or "").strip()
            monto1 = (item.findtext('.//cbc:LineExtensionAmount', ns) or "").strip()
            monto2 = (item.findtext('.//cbc:PriceAmount', ns) or "").strip()
            monto_base = (item.findtext('.//cbc:BaseQuantity', ns) or "").strip()

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

