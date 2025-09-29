from django.contrib import admin
from .models import Payment

# Register your models here.

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'payment_method', 'status', 'amount', 'currency', 'created_at')
    list_filter = ('payment_method', 'status', 'currency', 'created_at')
    search_fields = ('order__order_number', 'user__username', 'stripe_payment_intent_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'user', 'payment_method', 'status')
        }),
        ('Amount', {
            'fields': ('amount', 'currency')
        }),
        ('Stripe Details', {
            'fields': ('stripe_payment_intent_id', 'stripe_payment_method_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
