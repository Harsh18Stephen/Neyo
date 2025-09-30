from django.contrib.auth.models import User
from django.db import models
from orders.models import Order

# Create your models here.

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('cod', 'Cash on Delivery'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.OneToOneField(Order, related_name='payment', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='payments', on_delete=models.CASCADE)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='razorpay')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    # Razorpay specific fields
    razorpay_order_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    
    # Stripe specific fields (keeping for future)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=200, blank=True, null=True)
    
    # Additional info
    payment_details = models.JSONField(blank=True, null=True)  # Store additional payment info
    failure_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment for {self.order.order_number} - {self.status}"
    
    def mark_as_succeeded(self):
        """Mark payment as successful"""
        from django.utils import timezone
        self.status = 'succeeded'
        self.completed_at = timezone.now()
        self.save()
        
        # Update order payment status
        self.order.payment_status = 'paid'
        self.order.status = 'processing'
        self.order.save()
    
    def mark_as_failed(self, reason=''):
        """Mark payment as failed"""
        self.status = 'failed'
        self.failure_reason = reason
        self.save()
        
        # Update order payment status
        self.order.payment_status = 'failed'
        self.order.save()
