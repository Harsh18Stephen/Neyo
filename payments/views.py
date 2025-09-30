from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
import razorpay
import json
import hmac
import hashlib
from .models import Payment
from orders.models import Order

# Create your views here.

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required
def process_payment(request, order_id):
    """Display payment page and create Razorpay order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order already has a successful payment
    if hasattr(order, 'payment') and order.payment.status == 'succeeded':
        messages.info(request, 'This order has already been paid')
        return redirect('orders:detail', order_id=order.id)
    
    # Create or get payment record
    payment, created = Payment.objects.get_or_create(
        order=order,
        user=request.user,
        defaults={
            'amount': order.total_amount,
            'currency': 'INR',
            'payment_method': 'razorpay',
            'status': 'pending'
        }
    )
    
    # Create Razorpay order if not already created
    if not payment.razorpay_order_id:
        try:
            # Amount should be in paise (multiply by 100)
            amount_in_paise = int(float(order.total_amount) * 100)
            
            razorpay_order = razorpay_client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': '1',  # Auto capture
                'notes': {
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                }
            })
            
            payment.razorpay_order_id = razorpay_order['id']
            payment.save()
            
        except Exception as e:
            messages.error(request, f'Error creating payment order: {str(e)}')
            return redirect('orders:checkout')
    
    context = {
        'order': order,
        'payment': payment,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': payment.razorpay_order_id,
        'amount': order.total_amount,
        'currency': 'INR',
        'user': request.user,
    }
    
    return render(request, 'payments/process_payment.html', context)


@login_required
@csrf_exempt
def verify_payment(request):
    """Verify Razorpay payment signature"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Get payment record
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id, user=request.user)
        
        # Verify signature
        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature == razorpay_signature:
            # Signature is valid - update payment
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.mark_as_succeeded()
            
            return JsonResponse({
                'success': True,
                'order_id': str(payment.order.id),
                'redirect_url': f'/orders/success/{payment.order.id}/'
            })
        else:
            # Signature verification failed
            payment.mark_as_failed('Signature verification failed')
            return JsonResponse({
                'success': False,
                'error': 'Payment verification failed'
            })
            
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Payment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhooks for payment events"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Verify webhook signature
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        
        # Get raw body
        webhook_body = request.body.decode('utf-8')
        
        # Verify signature
        expected_signature = hmac.new(
            webhook_secret.encode(),
            webhook_body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if webhook_signature != expected_signature:
            return HttpResponse('Invalid signature', status=400)
        
        # Parse webhook data
        data = json.loads(webhook_body)
        event = data.get('event')
        payload = data.get('payload', {}).get('payment', {}).get('entity', {})
        
        # Handle different events
        if event == 'payment.captured':
            # Payment was successfully captured
            order_id = payload.get('notes', {}).get('order_id')
            payment_id = payload.get('id')
            
            if order_id:
                try:
                    payment = Payment.objects.get(order__id=order_id)
                    payment.razorpay_payment_id = payment_id
                    payment.mark_as_succeeded()
                except Payment.DoesNotExist:
                    pass
        
        elif event == 'payment.failed':
            # Payment failed
            order_id = payload.get('notes', {}).get('order_id')
            error_description = payload.get('error_description', 'Payment failed')
            
            if order_id:
                try:
                    payment = Payment.objects.get(order__id=order_id)
                    payment.mark_as_failed(error_description)
                except Payment.DoesNotExist:
                    pass
        
        return HttpResponse('OK', status=200)
        
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=400)


def payment_success(request):
    """Payment success page"""
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            return render(request, 'payments/success.html', {'order': order})
        except Order.DoesNotExist:
            pass
    
    return render(request, 'payments/success.html')


def payment_failed(request):
    """Payment failed page"""
    order_id = request.GET.get('order_id')
    error = request.GET.get('error', 'Payment failed')
    
    context = {
        'error': error,
    }
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            context['order'] = order
        except Order.DoesNotExist:
            pass
    
    return render(request, 'payments/failed.html', context)


@login_required
def retry_payment(request, order_id):
    """Allow user to retry payment for failed orders"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order can be retried
    if order.payment_status not in ['pending', 'failed']:
        messages.error(request, 'This order cannot be retried')
        return redirect('orders:detail', order_id=order.id)
    
    # Reset payment if exists
    if hasattr(order, 'payment'):
        payment = order.payment
        payment.status = 'pending'
        payment.razorpay_order_id = None
        payment.razorpay_payment_id = None
        payment.razorpay_signature = None
        payment.save()
    
    return redirect('payments:process', order_id=order.id)