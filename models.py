from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Factura(BaseModel):
    N_Documento: Optional[str] = None
    CUFE: Optional[str] = None
    Fecha_Documento: Optional[str] = None
    Nombre_Vendedor: Optional[str] = None
    Nit_Vendedor: Optional[str] = None
    Correo_Vendedor: Optional[str] = None
    Direccion_Vendedor: Optional[str] = None
    Codigo_Ciudad_Vendedor: Optional[str] = None
    Telefono_Vendedor: Optional[str] = None
    Contacto_Vendedor: Optional[str] = None
    Cantidad_Items: Optional[str] = None
    Monto_Total: Optional[str] = None
    Monto_Sin_Impuestos: Optional[str] = None
    Monto_Con_Impuestos: Optional[str] = None
    Monto_Pagar: Optional[str] = None
    Nombre_Comprador: Optional[str] = None
    Nit_Comprador: Optional[str] = None
    Moneda_Documento: Optional[str] = None

class Item(BaseModel):
    Id_Item: Optional[str] = None
    Cantidad_Item: Optional[str] = None
    Monto1_Item: Optional[str] = None
    Monto2_Item: Optional[str] = None
    MontoBase_Item: Optional[str] = None
    Descripcion_Item: Optional[str] = None
    cuentacontable: Optional[str] = None
    keycontable: Optional[str] = None

class DatosEntrada(BaseModel):
    factura: Factura
    items: List[Item]

    class Config:
        extra = "allow"  # 🔥 permite conservar cualquier campo adicional no definido
