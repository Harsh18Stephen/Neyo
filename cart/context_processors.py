
from .models import Cart

def cart_context(request):
    """
    Add cart information to all templates
    """
    cart_items_count = 0
    cart_total = 0
    
    try:
        from .models import Cart
        
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=request.user)
                cart_items_count = cart.get_total_items()
                cart_total = cart.get_total_price()
            except Cart.DoesNotExist:
                pass
        else:
            # For session-based carts
            session_key = request.session.session_key
            if session_key:
                try:
                    cart = Cart.objects.get(session_key=session_key)
                    cart_items_count = cart.get_total_items()
                    cart_total = cart.get_total_price()
                except Cart.DoesNotExist:
                    pass
    except Exception:
        # If there's any error, just return defaults
        pass
    
    return {
        'cart_items_count': cart_items_count,
        'cart_total': cart_total,
    }
