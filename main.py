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
        xml_data = xml_data.lstrip()
        root = ET.fromstring(xml_data)

        # 🔍 Detectar automáticamente los namespaces del XML
        nsmap = {}
        for elem in root.iter():
            if elem.tag[0] == "{":
                uri, tag = elem.tag[1:].split("}")
                prefix = tag.split(":")[0]
                if "ubl" in uri or "Common" in uri or "oasis" in uri or "dian" in uri:
                    nsmap["cbc"] = uri.replace("CommonAggregateComponents", "CommonBasicComponents")
                    nsmap["cac"] = uri.replace("CommonBasicComponents", "CommonAggregateComponents")
                break

        # --- FACTURA ---
        factura = {
            "N_Documento": (root.findtext('.//cbc:ID', nsmap) or "0").strip(),
            "CUFE": (root.findtext('.//cbc:UUID', nsmap) or "").strip(),
            "Fecha_Documento": (root.findtext('.//cbc:IssueDate', nsmap) or "").strip(),
            "Nombre_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cbc:Name', nsmap) or "").strip(),
            "Nit_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cbc:ID', nsmap) or "").strip(),
            "Correo_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cbc:ElectronicMail', nsmap) or "").strip(),
            "Direccion_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cbc:StreetName', nsmap) or "").strip(),
            "Codigo_Ciudad_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cbc:CitySubdivisionName', nsmap) or "").strip(),
            "Telefono_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cbc:Telephone', nsmap) or "").strip(),
            "Contacto_Vendedor": (root.findtext('.//cac:AccountingSupplierParty//cac:Contact//cbc:Name', nsmap) or "").strip(),
            "Cantidad_Items": str(len(root.findall('.//cac:InvoiceLine', nsmap))),
            "Monto_Total": (root.findtext('.//cbc:LineExtensionAmount', nsmap) or "").strip(),
            "Monto_Sin_Impuestos": (root.findtext('.//cbc:TaxExclusiveAmount', nsmap) or "").strip(),
            "Monto_Con_Impuestos": (root.findtext('.//cbc:TaxInclusiveAmount', nsmap) or "").strip(),
            "Monto_Pagar": (root.findtext('.//cbc:PayableAmount', nsmap) or "").strip(),
            "Nombre_Comprador": (root.findtext('.//cac:AccountingCustomerParty//cbc:Name', nsmap) or "").strip(),
            "Nit_Comprador": (root.findtext('.//cac:AccountingCustomerParty//cbc:ID', nsmap) or "").strip(),
            "Moneda_Documento": (root.findtext('.//cbc:DocumentCurrencyCode', nsmap) or "").strip()
        }

        # --- ITEMS ---
        items = []
        for item in root.findall('.//cac:InvoiceLine', nsmap):
            descripcion = (item.findtext('.//cbc:Description', nsmap) or "").strip()
            id_item = (item.findtext('.//cbc:ID', nsmap) or "").strip()
            cantidad = (item.findtext('.//cbc:InvoicedQuantity', nsmap) or "").strip()
            monto1 = (item.findtext('.//cbc:LineExtensionAmount', nsmap) or "").strip()
            monto2 = (item.findtext('.//cbc:PriceAmount', nsmap) or "").strip()
            monto_base = (item.findtext('.//cbc:BaseQuantity', nsmap) or "").strip()

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

