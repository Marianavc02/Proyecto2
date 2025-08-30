# productos/context_processors.py
def cart(request):
    """
    Expone cart_count en todas las plantillas.
    Cuenta productos distintos (no cantidades).
    """
    carrito = request.session.get('carrito', {})
    return {'cart_count': len(carrito)}
