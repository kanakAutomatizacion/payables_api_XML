import requests

# 🔹 URL de tu API
url = "http://127.0.0.1:8000/cuenta_contable/"  # cámbiala si estás en Render

# 🔹 Datos de prueba
data = {
    "factura": {
        "Nit_Vendedor": "830055643"
    },
    "items": [
        {"Descripcion_Item": "Pago de honorarios revisoría fiscal"},
        {"Descripcion_Item": "Pago de vacaciones"},
        {"Descripcion_Item": "Compra de insumos varios"}
    ]
}

# 🔹 Enviar solicitud POST
response = requests.post(url, json=data)

# 🔹 Ver resultado
print("Código de estado:", response.status_code)
print("Respuesta JSON:")
print(response.json())
