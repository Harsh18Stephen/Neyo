import razorpay
from django.conf import settings
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


client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Create your views here.


@login_required
def checkout(request):
    # Step 1 - Get cart
    try:
        cart = Cart.objects.get(user=request.user)
        if cart.get_total_items() == 0:
            messages.warning(request, 'Your cart is empty')
            return redirect('products:list')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty')
        return redirect('products:list')
    
    shipping_addresses = Address.objects.filter(user=request.user, type='shipping')
    billing_addresses = Address.objects.filter(user=request.user, type='billing')
    
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
    # Step 2 - Address selection
    if request.method == 'POST':
        shipping_address_id = request.POST.get('shipping_address')
        billing_address_id = request.POST.get('billing_address')
        use_same_address = request.POST.get('use_same_address')
        
        request.session['shipping_address_id'] = shipping_address_id
        if use_same_address:
            request.session['billing_address_id'] = shipping_address_id
        else:
            request.session['billing_address_id'] = billing_address_id
        
        return redirect('orders:checkout_payment')
    
    shipping_addresses = Address.objects.filter(user=request.user, type='shipping')
    billing_addresses = Address.objects.filter(user=request.user, type='billing')
    
    context = {
        'shipping_addresses': shipping_addresses,
        'billing_addresses': billing_addresses,
    }
    
    return render(request, 'orders/checkout_address.html', context)


@login_required
def checkout_payment(request):
    """Checkout step 3 - Payment information (creates Order + Razorpay order)"""
    if not request.session.get('shipping_address_id'):
        messages.warning(request, 'Please select shipping address')
        return redirect('orders:checkout_address')

    try:
        cart = Cart.objects.get(user=request.user)
        if cart.get_total_items() == 0:
            messages.error(request, 'Your cart is empty')
            return redirect('products:list')
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty')
        return redirect('products:list')

    subtotal = cart.get_total_price()
    tax = subtotal * Decimal('0.10')
    shipping_cost = Decimal('0') if subtotal > 50 else Decimal('5.99')
    total = subtotal + tax + shipping_cost

    # Reuse a pending order for this session if one already exists,
    # instead of creating duplicates on page refresh
    order_id = request.session.get('pending_order_id')
    order = Order.objects.filter(id=order_id, user=request.user, payment_status='pending').first() if order_id else None

    if not order:
        shipping_address_id = request.session.get('shipping_address_id')
        billing_address_id = request.session.get('billing_address_id')

        if not shipping_address_id or not billing_address_id:
            messages.error(request, 'Please complete address information')
            return redirect('orders:checkout_address')

        shipping_address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
        billing_address = get_object_or_404(Address, id=billing_address_id, user=request.user)

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

        request.session['pending_order_id'] = str(order.id)

    # Create (or reuse) the Razorpay order
    if not order.razorpay_order_id:
        amount_in_paise = int(order.total_amount * 100)
        razorpay_order = client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1'
        })
        order.razorpay_order_id = razorpay_order['id']
        order.save()

    context = {
        'order': order,
        'razorpay_order_id': order.razorpay_order_id,
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'amount': int(order.total_amount * 100),
        'subtotal': subtotal,
        'tax': tax,
        'shipping': shipping_cost,
        'total': total,
    }

    return render(request, 'orders/checkout_payment.html', context)


@login_required
def checkout_confirm(request):
    """
    Legacy step 4 view. Order creation now happens in checkout_payment,
    so this view is no longer part of the active flow. Left here in case
    anything still references it, but it should not be routed to normally.
    """
    if request.method != 'POST':
        return redirect('orders:checkout')

    messages.info(request, 'Please complete payment to confirm your order')
    return redirect('orders:checkout_payment')


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_success.html', context)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'orders/order_history.html', context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'orders/order_detail.html', context)


@login_required
def cancel_order(request, order_id):
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
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # For now, return simple HTML (we'll add PDF generation later)
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    
    return render(request, 'orders/invoice.html', context)