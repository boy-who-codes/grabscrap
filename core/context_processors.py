from orders.models import Cart

def cart_items_count(request):
    """Context processor to provide cart items count to all templates"""
    if request.user.is_authenticated:
        try:
            active_cart = Cart.objects.filter(user=request.user, is_active=True).first()
            if active_cart:
                return {'user_cart_items': active_cart.total_items}
            else:
                return {'user_cart_items': 0}
        except Exception:
            return {'user_cart_items': 0}
    return {'user_cart_items': 0} 