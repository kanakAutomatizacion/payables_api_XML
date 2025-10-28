import requests

# 🔹 URL de tu API local o desplegada
url = "http://127.0.0.1:8000/cuenta_contable_xml/"  # cambia el puerto si usas Render u otro

# 🔹 Cargar el XML de prueba
xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<factura>
    <Nit_Vendedor>830055643</Nit_Vendedor>
    <items>
        <item>
            <Descripcion_Item>Pago de honorarios revisoría fiscal</Descripcion_Item>
        </item>
        <item>
            <Descripcion_Item>Pago de vacaciones</Descripcion_Item>
        </item>
        <item>
            <Descripcion_Item>Compra de insumos varios</Descripcion_Item>
        </item>
    </items>
</factura>
"""

# 🔹 Encabezados
headers = {
    "Content-Type": "application/xml"
}

# 🔹 Enviar solicitud POST
response = requests.post(url, headers=headers, data=xml_data.encode("utf-8"))

# 🔹 Mostrar resultado
print("Código de estado:", response.status_code)
try:
    print("Respuesta JSON:")
    print(response.json())
except Exception as e:
    print("Error al decodificar JSON:", e)
    print("Texto de respuesta:", response.text)

