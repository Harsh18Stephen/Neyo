from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment processing
    path('process/<uuid:order_id>/', views.process_payment, name='process'),
    path('verify/', views.verify_payment, name='verify'),
    path('retry/<uuid:order_id>/', views.retry_payment, name='retry'),
    
    # Webhooks
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
    
    # Success/Failed pages
    path('success/', views.payment_success, name='success'),
    path('failed/', views.payment_failed, name='failed'),
]