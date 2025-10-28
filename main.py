from fastapi import FastAPI, Body, HTTPException
import xml.etree.ElementTree as ET
import re
import base64
from services.reglas_service import cargar_reglas
from services.cuenta_contable import obtener_cuenta_contable

app = FastAPI()

# 🔹 Carga inicial de reglas
reglas_nit, reglas_puc = cargar_reglas()

# --- Funciones auxiliares ---
def detectar_namespaces(xml_str):
    pattern = re.compile(r'xmlns:([a-zA-Z0-9]+)="([^"]+)"')
    nsmap = dict(pattern.findall(xml_str))
    if None not in nsmap.values():
        nsmap.setdefault("cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
        nsmap.setdefault("cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    return nsmap

def buscar_texto(root, rutas, nsmap):
    for ruta in rutas:
        valor = root.findtext(ruta, namespaces=nsmap)
        if valor:
            return valor.strip()
    return ""

def extraer_factura_embebida(xml_root, nsmap):
    """
    Extrae la factura embebida dentro de un AttachedDocument, si existe.
    """
    try:
        embedded_data = xml_root.find(".//cbc:EmbeddedDocumentBinaryObject", namespaces=nsmap)
        if embedded_data is not None and embedded_data.text:
            factura_xml = base64.b64decode(embedded_data.text.encode("utf-8")).decode("utf-8")
            print("✅ Factura embebida extraída correctamente.")
            return factura_xml
        else:
            print("⚠️ No se encontró documento embebido en el AttachedDocument.")
            return None
    except Exception as e:
        print(f"⚠️ Error al extraer factura embebida: {e}")
        return None


# --- Endpoint principal ---
@app.post("/cuenta_contable_xml/")
async def cuenta_contable_xml(xml_data: str = Body(..., media_type="application/xml")):
    try:
        # Limpieza del XML
        xml_data = xml_data.encode('utf-8').decode('utf-8-sig').strip()

        # Detección de tipo de documento
        nsmap = detectar_namespaces(xml_data)
        root = ET.fromstring(xml_data)

        # Si es AttachedDocument, extraemos la factura embebida
        if "AttachedDocument" in root.tag:
            print("🧾 Detectado AttachedDocument — extrayendo factura embebida...")
            factura_embebida_xml = extraer_factura_embebida(root, nsmap)
            if factura_embebida_xml:
                xml_data = factura_embebida_xml
                nsmap = detectar_namespaces(xml_data)
                root = ET.fromstring(xml_data)
            else:
                raise HTTPException(status_code=400, detail="No se pudo extraer la factura embebida del AttachedDocument.")

        # ----------- FACTURA -----------
        factura = {
            "N_Documento": buscar_texto(root, [".//cbc:ID", ".//cbc:InvoiceID"], nsmap),
            "CUFE": buscar_texto(root, [".//cbc:UUID", ".//cbc:CUFE"], nsmap),
            "Fecha_Documento": buscar_texto(root, [".//cbc:IssueDate"], nsmap),
            "Nombre_Vendedor": buscar_texto(root, [
                ".//cac:AccountingSupplierParty//cbc:Name",
                ".//cac:AccountingSupplierParty//cac:Party//cac:PartyName//cbc:Name"
            ], nsmap),
            "Nit_Vendedor": buscar_texto(root, [
                ".//cac:AccountingSupplierParty//cbc:CompanyID",
                ".//cac:AccountingSupplierParty//cac:Party//cac:PartyIdentification//cbc:ID"
            ], nsmap),
            "Correo_Vendedor": buscar_texto(root, [
                ".//cac:AccountingSupplierParty//cac:Contact//cbc:ElectronicMail",
                ".//cac:AccountingSupplierParty//cbc:ElectronicMail"
            ], nsmap),
            "Direccion_Vendedor": buscar_texto(root, [
                ".//cac:AccountingSupplierParty//cac:PostalAddress//cbc:StreetName"
            ], nsmap),
            "Codigo_Ciudad_Vendedor": buscar_texto(root, [
                ".//cac:AccountingSupplierParty//cac:PostalAddress//cbc:CityName"
            ], nsmap),
            "Telefono_Vendedor": buscar_texto(root, [
                ".//cac:AccountingSupplierParty//cac:Contact//cbc:Telephone"
            ], nsmap),
            "Contacto_Vendedor": buscar_texto(root, [
                ".//cac:AccountingSupplierParty//cac:Contact//cbc:Name"
            ], nsmap),
            "Cantidad_Items": str(len(root.findall(".//cac:InvoiceLine", namespaces=nsmap))),
            "Monto_Total": buscar_texto(root, [".//cac:LegalMonetaryTotal//cbc:LineExtensionAmount"], nsmap),
            "Monto_Sin_Impuestos": buscar_texto(root, [".//cac:TaxTotal//cbc:TaxExclusiveAmount"], nsmap),
            "Monto_Con_Impuestos": buscar_texto(root, [".//cac:TaxTotal//cbc:TaxInclusiveAmount"], nsmap),
            "Monto_Pagar": buscar_texto(root, [".//cac:LegalMonetaryTotal//cbc:PayableAmount"], nsmap),
            "Nombre_Comprador": buscar_texto(root, [
                ".//cac:AccountingCustomerParty//cbc:Name",
                ".//cac:AccountingCustomerParty//cac:Party//cac:PartyName//cbc:Name"
            ], nsmap),
            "Nit_Comprador": buscar_texto(root, [
                ".//cac:AccountingCustomerParty//cbc:CompanyID",
                ".//cac:AccountingCustomerParty//cac:Party//cac:PartyIdentification//cbc:ID"
            ], nsmap),
            "Moneda_Documento": buscar_texto(root, [".//cbc:DocumentCurrencyCode"], nsmap)
        }

        # ----------- ITEMS -----------
        items = []
        for item in root.findall(".//cac:InvoiceLine", namespaces=nsmap):
            descripcion = buscar_texto(item, [
                ".//cbc:Description",
                ".//cac:Item//cbc:Description"
            ], nsmap)
            id_item = buscar_texto(item, [".//cbc:ID"], nsmap)
            cantidad = buscar_texto(item, [".//cbc:InvoicedQuantity"], nsmap)
            monto1 = buscar_texto(item, [".//cbc:LineExtensionAmount"], nsmap)
            monto2 = buscar_texto(item, [".//cac:Price//cbc:PriceAmount"], nsmap)
            monto_base = buscar_texto(item, [".//cac:Price//cbc:BaseQuantity"], nsmap)

            try:
                cuenta = obtener_cuenta_contable(
                    {"Descripcion_Item": descripcion},
                    factura["Nit_Vendedor"],
                    reglas_nit,
                    reglas_puc
                )
            except Exception:
                cuenta = "No encontrada"

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
