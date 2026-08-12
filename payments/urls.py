from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('process/', views.process_payment, name='process'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('success/', views.payment_success, name='success'),
    path('failed/', views.payment_failed, name='failed'),
    path('create-order/<int:order_id>/', views.create_order, name='create_order'),
    path('create-order/<int:order_id>/', views.create_order, name='create_order'),
    path('verify/', views.payment_verify, name='payment_verify'),
]