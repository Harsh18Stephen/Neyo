from django.contrib.auth.models import User
from django.db import models
from products.models import Product, ProductVariant

# Create your models here.

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.user.username if self.user else self.session_key}"
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())
    
    def clear(self):
        self.items.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cart', 'product', 'variant')
    
    def __str__(self):
        size_info = f" ({self.variant.size})" if self.variant else ""
        return f"{self.product.name}{size_info} x {self.quantity}"
    
    def get_price(self):
        """Get the price for this item (variant price if available)"""
        return self.variant.get_price() if self.variant else self.product.price
    
    def get_total_price(self):
        return self.get_price() * self.quantity
