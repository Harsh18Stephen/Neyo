from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from decimal import Decimal
import time

from .models import Order, OrderItem
from cart.models import Cart
from accounts.models import Address
from products.models import Product

# Create your views here.


@login_required
def checkout(request):
    """Checkout landing - show cart summary and start checkout"""
    # Get user's cart
    try:
        cart = Cart.objects.get(user=request.user)
        if cart.get_total_items() == 0:
            messages.warning(request, 'Your cart is empty')
            return redirect('products:list')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty')
        return redirect('products:list')
    
    # Get user's saved addresses
    shipping_addresses = Address.objects.filter(user=request.user, type='shipping')
    billing_addresses = Address.objects.filter(user=request.user, type='billing')
    
    # Calculate totals
    subtotal = cart.get_total_price()
    tax = subtotal * Decimal('0.10')
    shipping = Decimal('0') if subtotal > 50 else Decimal('5.99')
    total = subtotal + tax + shipping
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
        'shipping_addresses': shipping_addresses,
        'billing_addresses': billing_addresses,
        'subtotal': subtotal,
        'tax': tax,
        'shipping': shipping,
        'total': total,
    }
    
    return render(request, 'orders/checkout.html', context)

@login_required
def checkout_address(request):
    """Checkout step 2 - Address information"""
    if request.method == 'POST':
        # Save shipping address
        shipping_address_id = request.POST.get('shipping_address')
        billing_address_id = request.POST.get('billing_address')
        use_same_address = request.POST.get('use_same_address')
        
        # Store in session for next step
        request.session['shipping_address_id'] = shipping_address_id
        if use_same_address:
            request.session['billing_address_id'] = shipping_address_id
        else:
            request.session['billing_address_id'] = billing_address_id
        
        return redirect('orders:checkout_payment')
    
    # Get user's addresses
    shipping_addresses = Address.objects.filter(user=request.user, type='shipping')
    billing_addresses = Address.objects.filter(user=request.user, type='billing')
    
    context = {
        'shipping_addresses': shipping_addresses,
        'billing_addresses': billing_addresses,
    }
    
    return render(request, 'orders/checkout_address.html', context)

@login_required
def checkout_payment(request):
    """Checkout step 3 - Payment information"""
    # Verify addresses are selected
    if not request.session.get('shipping_address_id'):
        messages.warning(request, 'Please select shipping address')
        return redirect('orders:checkout_address')
    
    # Get cart
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty')
        return redirect('products:list')
    
    # Calculate totals
    subtotal = cart.get_total_price()
    tax = subtotal * Decimal('0.10')
    shipping = Decimal('0') if subtotal > 50 else Decimal('5.99')
    total = subtotal + tax + shipping
    
    context = {
        'subtotal': subtotal,
        'tax': tax,
        'shipping': shipping,
        'total': total,
    }
    
    return render(request, 'orders/checkout_payment.html', context)

@login_required
def checkout_confirm(request):
    """Checkout step 4 - Order confirmation and processing"""
    if request.method != 'POST':
        return redirect('orders:checkout')
    
    try:
        # Get cart
        cart = Cart.objects.get(user=request.user)
        if cart.get_total_items() == 0:
            messages.error(request, 'Your cart is empty')
            return redirect('products:list')
        
        # Get addresses
        shipping_address_id = request.session.get('shipping_address_id')
        billing_address_id = request.session.get('billing_address_id')
        
        if not shipping_address_id or not billing_address_id:
            messages.error(request, 'Please complete address information')
            return redirect('orders:checkout_address')
        
        shipping_address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
        billing_address = get_object_or_404(Address, id=billing_address_id, user=request.user)
        
        # Calculate totals
        subtotal = cart.get_total_price()
        tax = subtotal * Decimal('0.10')
        shipping_cost = Decimal('0') if subtotal > 50 else Decimal('5.99')
        total = subtotal + tax + shipping_cost
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            tax_amount=tax,
            shipping_amount=shipping_cost,
            total_amount=total,
            shipping_address=shipping_address.get_full_address(),
            billing_address=billing_address.get_full_address(),
            payment_status='pending',
            status='pending'
        )
        
        # Create order items from cart
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=cart_item.get_price(),
                product_name=cart_item.product.name,
                product_size=cart_item.variant.size if cart_item.variant else ''
            )
        
        # Clear cart
        cart.clear()
        
        # Clear session data
        request.session.pop('shipping_address_id', None)
        request.session.pop('billing_address_id', None)
        
        # Redirect to payment processing
        return redirect('payments:process', order_id=order.id)
        
    except Exception as e:
        messages.error(request, f'Error processing order: {str(e)}')
        return redirect('orders:checkout')

def order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_success.html', context)

@login_required
def order_history(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'orders/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """Order detail view"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'orders/order_detail.html', context)

@login_required
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.can_cancel():
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order {order.order_number} has been cancelled')
    else:
        messages.error(request, 'This order cannot be cancelled')
    
    return redirect('orders:detail', order_id=order_id)

@login_required
def generate_invoice(request, order_id):
    """Generate PDF invoice for order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # For now, return simple HTML (we'll add PDF generation later)
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    
    return render(request, 'orders/invoice.html', context)