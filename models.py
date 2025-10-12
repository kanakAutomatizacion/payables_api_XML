from pydantic import BaseModel
from typing import List, Optional

class Factura(BaseModel):
    Nit_Vendedor: str

class Item(BaseModel):
    Descripcion_Item: str
    cuentacontable: Optional[str] = None

class DatosEntrada(BaseModel):
    factura: Factura
    items: List[Item]
