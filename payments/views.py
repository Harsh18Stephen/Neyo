from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

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