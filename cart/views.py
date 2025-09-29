from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import Product, ProductVariant
from .models import Cart, CartItem


# Create your views here.

def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def cart_view(request):
    """Display shopping cart"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product', 'variant')
    
    # Calculate totals (using Decimal to avoid type errors)
    from decimal import Decimal
    
    subtotal = cart.get_total_price()
    tax = subtotal * Decimal('0.10')  # 10% tax as Decimal
    shipping = Decimal('0') if subtotal > 50 else Decimal('5.99')  # Free shipping over $50
    total = subtotal + tax + shipping
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'shipping': shipping,
        'total': total,
    }
    
    return render(request, 'cart/cart.html', context)

@require_POST
def add_to_cart(request):
    """Add product to cart"""
    try:
        product_id = request.POST.get('product_id')
        size = request.POST.get('size', '')
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate inputs
        if not product_id:
            messages.error(request, 'Product not specified')
            return redirect('products:list')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Check if product requires size
        variant = None
        if size:
            try:
                variant = ProductVariant.objects.get(product=product, size=size)
                if not variant.is_in_stock():
                    messages.error(request, f'Size {size} is out of stock')
                    return redirect('products:detail', slug=product.slug)
            except ProductVariant.DoesNotExist:
                messages.error(request, 'Invalid size selected')
                return redirect('products:detail', slug=product.slug)
        
        # Get or create cart
        cart = get_or_create_cart(request)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()
            messages.success(request, f'Updated {product.name} quantity in cart')
        else:
            messages.success(request, f'Added {product.name} to cart')
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Added to cart',
                'cart_count': cart.get_total_items()
            })
        
        return redirect('cart:view')
        
    except Exception as e:
        messages.error(request, 'Error adding item to cart')
        return redirect('products:list')

@require_POST
def update_cart(request, item_id):
    """Update cart item quantity"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if quantity < 1:
            cart_item.delete()
            messages.success(request, 'Item removed from cart')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated')
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': cart.get_total_items(),
                'subtotal': float(cart.get_total_price())
            })
        
        return redirect('cart:view')
        
    except Exception as e:
        messages.error(request, 'Error updating cart')
        return redirect('cart:view')

def remove_from_cart(request, item_id):
    """Remove item from cart"""
    try:
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        product_name = cart_item.product.name
        cart_item.delete()
        
        messages.success(request, f'Removed {product_name} from cart')
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': cart.get_total_items(),
                'subtotal': float(cart.get_total_price())
            })
        
        return redirect('cart:view')
        
    except Exception as e:
        messages.error(request, 'Error removing item')
        return redirect('cart:view')

def clear_cart(request):
    """Clear entire cart"""
    cart = get_or_create_cart(request)
    cart.clear()
    messages.success(request, 'Cart cleared')
    return redirect('cart:view')

def cart_count(request):
    """AJAX endpoint to get cart count"""
    cart = get_or_create_cart(request)
    return JsonResponse({
        'count': cart.get_total_items()
    })