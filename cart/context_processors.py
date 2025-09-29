
from .models import Cart

def cart_context(request):
    """
    Add cart information to all templates
    """
    cart_items_count = 0
    cart_total = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items_count = cart.get_total_items()
            cart_total = cart.get_total_price()
        except Cart.DoesNotExist:
            pass
    else:
        # For session-based carts
        cart_data = request.session.get('cart', {})
        cart_items_count = sum(item.get('quantity', 0) for item in cart_data.values())
        cart_total = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart_data.values())
    
    return {
        'cart_items_count': cart_items_count,
        'cart_total': cart_total,
    }

