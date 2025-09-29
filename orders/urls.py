from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/address/', views.checkout_address, name='checkout_address'),
    path('checkout/payment/', views.checkout_payment, name='checkout_payment'),
    path('checkout/confirm/', views.checkout_confirm, name='checkout_confirm'),
    path('success/<uuid:order_id>/', views.order_success, name='success'),
    path('history/', views.order_history, name='history'),
    path('detail/<uuid:order_id>/', views.order_detail, name='detail'),
    path('cancel/<uuid:order_id>/', views.cancel_order, name='cancel'),
    path('invoice/<uuid:order_id>/', views.generate_invoice, name='invoice'),
]
