from services.reglas_service import buscar_por_nit, buscar_por_palabras

CUENTA_POR_DEFECTO = "51959501"

def obtener_cuenta_contable(item, nit, reglas_nit, reglas_puc):
    # 1. Buscar por NIT
    cuenta = buscar_por_nit(nit, reglas_nit)
    if cuenta:
        return cuenta

    # 2. Buscar por palabras clave
    cuenta = buscar_por_palabras(item["Descripcion_Item"], reglas_puc)
    if cuenta:
        return cuenta

    # 3. Cuenta por defecto
    return CUENTA_POR_DEFECTO
