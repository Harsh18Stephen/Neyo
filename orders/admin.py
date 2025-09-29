from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem

# Register your models here.

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_total_price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email')
    readonly_fields = ('id', 'order_number', 'created_at', 'updated_at')
    list_editable = ('status',)
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'order_number', 'user', 'created_at', 'updated_at')
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_amount', 'total_amount')
        }),
        ('Addresses', {
            'fields': ('shipping_address', 'billing_address')
        }),
        ('Payment', {
            'fields': ('stripe_payment_intent',)
        }),
    )
    
    inlines = [OrderItemInline]
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing order
            return self.readonly_fields + ('user', 'subtotal', 'tax_amount', 'shipping_amount', 'total_amount')
        return self.readonly_fields

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'product_size', 'quantity', 'price', 'get_total_price')
    list_filter = ('order__created_at', 'product')
    search_fields = ('order__order_number', 'product_name')
    readonly_fields = ('get_total_price',)