from products.models import Cart
from wallet.models import Wallet


def user_context(request):
    """Add user-related context data"""
    context = {}
    
    if request.user.is_authenticated:
        # Get or create cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=request.user)
        
        # Get or create wallet
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=request.user)
        
        context.update({
            'user_cart': cart,
            'user_wallet': wallet,
        })
    
    return context
