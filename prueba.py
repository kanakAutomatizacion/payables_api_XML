import xml.etree.ElementTree as ET
import json

def procesar_xml(xml_path):
    try:
        # Cargar el XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Namespace (algunos XML tienen esto)
        ns = {'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
              'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'}

        factura = {
            "N_Documento": root.findtext(".//cbc:ID", default="", namespaces=ns),
            "CUFE": root.findtext(".//cbc:UUID", default="", namespaces=ns),
            "Fecha_Documento": root.findtext(".//cbc:IssueDate", default="", namespaces=ns),
            "Nombre_Vendedor": root.findtext(".//cac:AccountingSupplierParty//cbc:RegistrationName", default="", namespaces=ns),
            "Nit_Vendedor": root.findtext(".//cac:AccountingSupplierParty//cbc:CompanyID", default="", namespaces=ns),
            "Correo_Vendedor": root.findtext(".//cac:AccountingSupplierParty//cbc:ElectronicMail", default="", namespaces=ns),
            "Direccion_Vendedor": root.findtext(".//cac:AccountingSupplierParty//cac:PostalAddress//cbc:StreetName", default="", namespaces=ns),
            "Codigo_Ciudad_Vendedor": root.findtext(".//cac:AccountingSupplierParty//cac:PostalAddress//cbc:CitySubdivisionName", default="", namespaces=ns),
            "Telefono_Vendedor": root.findtext(".//cac:AccountingSupplierParty//cbc:Telephone", default="", namespaces=ns),
            "Contacto_Vendedor": root.findtext(".//cac:AccountingSupplierParty//cac:Contact//cbc:Name", default="", namespaces=ns),
            "Cantidad_Items": str(len(root.findall(".//cac:InvoiceLine", namespaces=ns))),
            "Monto_Total": root.findtext(".//cbc:PayableAmount", default="", namespaces=ns),
            "Monto_Sin_Impuestos": root.findtext(".//cbc:LineExtensionAmount", default="", namespaces=ns),
            "Monto_Con_Impuestos": root.findtext(".//cbc:TaxInclusiveAmount", default="", namespaces=ns),
            "Monto_Pagar": root.findtext(".//cbc:PayableAmount", default="", namespaces=ns),
            "Nombre_Comprador": root.findtext(".//cac:AccountingCustomerParty//cbc:RegistrationName", default="", namespaces=ns),
            "Nit_Comprador": root.findtext(".//cac:AccountingCustomerParty//cbc:CompanyID", default="", namespaces=ns),
            "Moneda_Documento": root.findtext(".//cbc:DocumentCurrencyCode", default="", namespaces=ns)
        }

        items = []
        for item in root.findall(".//cac:InvoiceLine", namespaces=ns):
            descripcion = item.findtext(".//cbc:Description", default="", namespaces=ns)
            monto = item.findtext(".//cbc:LineExtensionAmount", default="", namespaces=ns)
            cantidad = item.findtext(".//cbc:InvoicedQuantity", default="", namespaces=ns)
            id_item = item.findtext(".//cbc:ID", default="", namespaces=ns)
            keycontable = f"{factura['Nit_Comprador']}_{factura['Nit_Vendedor']}_{descripcion}"

            items.append({
                "Id_Item": id_item,
                "Cantidad_Item": cantidad,
                "Monto1_Item": monto,
                "Monto2_Item": monto,
                "MontoBase_Item": cantidad,
                "Descripcion_Item": descripcion,
                "cuentacontable": "51959501",  # Valor temporal
                "keycontable": keycontable
            })

        return {"factura": factura, "items": items}

    except Exception as e:
        return {"error": str(e)}

# --- Prueba local ---
if __name__ == "__main__":
    resultado = procesar_xml("tu_archivo.xml")  # reemplaza con el nombre del XML
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
