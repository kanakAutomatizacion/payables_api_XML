import xml.etree.ElementTree as ET
import re
import json
import os

def extraer_factura_embebida(xml_path):
    print("🧾 Detectando tipo de XML...")

    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_str = f.read()

    if "<AttachedDocument" in xml_str:
        print("🧾 Detectado AttachedDocument — extrayendo factura embebida...")

        root = ET.fromstring(xml_str)
        namespaces = detectar_namespaces(xml_str)

        embedded = root.find(".//cac:Attachment/cac:ExternalReference/cbc:Description", namespaces)
        if embedded is not None and embedded.text:
            factura_embebida_str = embedded.text.strip()
            with open("factura_embebida.xml", "w", encoding="utf-8") as f2:
                f2.write(factura_embebida_str)
            print("✅ Factura embebida extraída correctamente → factura_embebida.xml")
            return "factura_embebida.xml"
        else:
            print("⚠️ No se encontró documento embebido en el AttachedDocument")
            return None
    else:
        print("📄 No es un AttachedDocument, usando el XML directamente.")
        return xml_path


def detectar_namespaces(xml_str):
    pattern = re.compile(r'xmlns:([a-zA-Z0-9]+)="([^"]+)"')
    nsmap = dict(pattern.findall(xml_str))
    nsmap.setdefault("cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
    nsmap.setdefault("cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    return nsmap


def buscar_texto(root, rutas, nsmap):
    for ruta in rutas:
        valor = root.findtext(ruta, namespaces=nsmap)
        if valor:
            return valor.strip()
    for ruta in rutas:
        valor = root.findtext(ruta.replace("cbc:", "").replace("cac:", ""))
        if valor:
            return valor.strip()
    return ""


def procesar_factura(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_str = f.read()

    nsmap = detectar_namespaces(xml_str)
    root = ET.fromstring(xml_str)

    # ===== Datos del Vendedor =====
    proveedor = root.find(".//cac:AccountingSupplierParty", nsmap)
    comprador = root.find(".//cac:AccountingCustomerParty", nsmap)

    factura = {
        "N_Documento": buscar_texto(root, [".//cbc:ID"], nsmap),
        "CUFE": buscar_texto(root, [".//cbc:UUID"], nsmap),
        "Fecha_Documento": buscar_texto(root, [".//cbc:IssueDate"], nsmap),
        "Nombre_Vendedor": buscar_texto(proveedor, [".//cbc:Name"], nsmap),
        "Nit_Vendedor": buscar_texto(proveedor, [".//cbc:CompanyID"], nsmap),
        "Correo_Vendedor": buscar_texto(proveedor, [".//cbc:ElectronicMail"], nsmap),
        "Direccion_Vendedor": buscar_texto(proveedor, [".//cac:Address/cbc:StreetName"], nsmap),
        "Codigo_Ciudad_Vendedor": buscar_texto(proveedor, [".//cac:Address/cbc:ID"], nsmap),
        "Telefono_Vendedor": buscar_texto(proveedor, [".//cbc:Telephone"], nsmap),
        "Contacto_Vendedor": buscar_texto(proveedor, [".//cac:Contact/cbc:Name"], nsmap),
        "Monto_Total": buscar_texto(root, [".//cac:LegalMonetaryTotal//cbc:LineExtensionAmount"], nsmap),
        "Monto_Sin_Impuestos": buscar_texto(root, [".//cac:LegalMonetaryTotal//cbc:TaxExclusiveAmount"], nsmap),
        "Monto_Con_Impuestos": buscar_texto(root, [".//cac:LegalMonetaryTotal//cbc:TaxInclusiveAmount"], nsmap),
        "Monto_Pagar": buscar_texto(root, [".//cac:LegalMonetaryTotal//cbc:PayableAmount"], nsmap),
        "Nombre_Comprador": buscar_texto(comprador, [".//cbc:Name"], nsmap),
        "Nit_Comprador": buscar_texto(comprador, [".//cbc:CompanyID"], nsmap),
        "Moneda_Documento": buscar_texto(root, [".//cbc:DocumentCurrencyCode"], nsmap),
    }

    items = []
    for item in root.findall(".//cac:InvoiceLine", nsmap) or root.findall(".//InvoiceLine"):
        id_item = buscar_texto(item, ["./cbc:ID"], nsmap)
        descripcion = buscar_texto(item, ["./cac:Item/cbc:Description"], nsmap)
        cantidad = buscar_texto(item, ["./cbc:InvoicedQuantity"], nsmap)
        monto1 = buscar_texto(item, ["./cac:Price/cbc:PriceAmount"], nsmap)
        monto2 = buscar_texto(item, ["./cbc:LineExtensionAmount"], nsmap)
        monto_base = buscar_texto(item, ["./cbc:BaseQuantity"], nsmap)

        cuenta_contable = asignar_cuenta_contable(descripcion)
        key = f"{factura['Nit_Comprador']}_{factura['Nit_Vendedor']}_{descripcion}"

        items.append({
            "Id_Item": id_item,
            "Cantidad_Item": cantidad or "1.00",
            "Monto1_Item": monto1 or "0.00",
            "Monto2_Item": monto2 or "0.00",
            "MontoBase_Item": monto_base or "1.00",
            "Descripcion_Item": descripcion,
            "cuentacontable": cuenta_contable,
            "keycontable": key
        })

    factura["Cantidad_Items"] = str(len(items))
    return {"factura": factura, "items": items}


def asignar_cuenta_contable(descripcion):
    descripcion = descripcion.lower()
    if "flete" in descripcion or "transporte" in descripcion:
        return "513550"
    elif "sanda" in descripcion or "zapato" in descripcion or "calzado" in descripcion:
        return "51959501"
    elif "temporal" in descripcion or "servicio" in descripcion:
        return "51351005"
    elif "mantenimiento" in descripcion:
        return "51451001"
    else:
        return "51999999"


def main():
    xml_path = "dos.xml"

    factura_embebida = extraer_factura_embebida(xml_path)
    if factura_embebida:
        resultado = procesar_factura(factura_embebida)
        print("\n🧮 Resultado final:")
        print(json.dumps(resultado, indent=4, ensure_ascii=False))

        # Guarda resultado.json automáticamente
        with open("resultado.json", "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=4, ensure_ascii=False)
        print("\n💾 Archivo guardado como resultado.json")
    else:
        print("⚠️ No se pudo extraer o procesar la factura embebida.")


if __name__ == "__main__":
    main()


