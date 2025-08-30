# productos/utils.py
def clasificar_empresa(sku: str) -> str:
    if not sku:
        return "Otros"

    sku = sku.upper().strip()

    if sku.startswith("S"):
        return "Stanley"
    elif sku.startswith("D"):
        return "DeWalt"
    elif sku.startswith("IW"):
        return "Irwin"
    elif sku.startswith("B") or "B3" in sku:
        return "Black&Decker"
    else:
        return "Otros"
