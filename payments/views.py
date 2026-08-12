from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from orders.models import Order

# Create your views here.

@login_required
def create_payment_intent(request):
    return JsonResponse({"error": "Payment integration coming soon"})

@login_required
def process_payment(request):
    return HttpResponse("<h1>Process Payment</h1><p>Payment processing coming soon...</p>")

@csrf_exempt
def stripe_webhook(request):
    return HttpResponse("Webhook received")

def payment_success(request):
    return HttpResponse("<h1>Payment Successful!</h1><p>Thank you for your payment!</p>")

def payment_failed(request):
    return HttpResponse("<h1>Payment Failed</h1><p>There was an issue with your payment.</p>")

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required
def create_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Don't let someone re-pay for an already paid order
    if order.is_paid:
        return redirect('order_success')  # adjust to your actual URL name

    amount_in_paise = int(order.total_amount * 100)  # Razorpay uses paise

    razorpay_order = client.order.create({
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': '1'
    })

    order.razorpay_order_id = razorpay_order['id']
    order.save()

    context = {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'amount': amount_in_paise,
    }
    return render(request, 'payments/checkout.html', context)


@csrf_exempt
@login_required
def payment_verify(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'failed', 'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)

        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature'),
        }

        # Signature verification — critical, do not skip
        client.utility.verify_payment_signature(params_dict)

    except KeyError:
        return JsonResponse({'status': 'failed', 'error': 'Missing payment data'}, status=400)
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'status': 'failed', 'error': 'Signature verification failed'}, status=400)

    try:
        order = Order.objects.get(razorpay_order_id=params_dict['razorpay_order_id'])
    except Order.DoesNotExist:
        return JsonResponse({'status': 'failed', 'error': 'Order not found'}, status=404)

    # Idempotency check — avoid double-processing if called twice
    if order.is_paid:
        return JsonResponse({'status': 'success'})

    order.razorpay_payment_id = params_dict['razorpay_payment_id']
    order.razorpay_signature = params_dict['razorpay_signature']
    order.is_paid = True
    order.save()

    return JsonResponse({'status': 'success'})