from services.reglas_service import buscar_por_nit, buscar_por_palabras

def obtener_cuenta_contable(item, nit, reglas_nit, reglas_puc):
    """Decide la cuenta contable usando NIT o descripción."""
    cuenta = buscar_por_nit(nit, reglas_nit)
    if cuenta:
        return cuenta
    return buscar_por_palabras(item["Descripcion_Item"], reglas_puc)
