# ================================
# core/admin.py
# Site-wide Django admin customization for NEYO
# ================================

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect

# ================================
# CUSTOM ADMIN SITE CONFIGURATION
# ================================

class NeyoAdminSite(AdminSite):
    """
    Custom admin site for NEYO e-commerce platform
    """
    site_header = "NEYO Administration"
    site_title = "NEYO Admin Portal"
    index_title = "Welcome to NEYO Administration Dashboard"
    
    def index(self, request, extra_context=None):
        """
        Custom admin dashboard with quick stats
        """
        extra_context = extra_context or {}
        
        # Add custom dashboard data
        try:
            from products.models import Product
            from orders.models import Order
            from django.contrib.auth.models import User
            
            extra_context.update({
                'total_products': Product.objects.filter(is_active=True).count(),
                'total_orders': Order.objects.count(),
                'total_users': User.objects.count(),
                'pending_orders': Order.objects.filter(status='pending').count(),
            })
        except ImportError:
            # In case models aren't created yet
            pass
            
        return super().index(request, extra_context)

# Create custom admin instance (optional - you can use default too)
neyo_admin_site = NeyoAdminSite(name='neyo_admin')

# ================================
# ADMIN SITE CUSTOMIZATION
# ================================

# Customize default Django admin
admin.site.site_header = "NEYO Administration"
admin.site.site_title = "NEYO Admin Portal"
admin.site.index_title = "Welcome to NEYO Administration Dashboard"

# Custom CSS for admin interface
admin.site.enable_nav_sidebar = True  # Enable sidebar navigation

# ================================
# ADMIN DASHBOARD ENHANCEMENTS
# ================================

def neyo_admin_view(request):
    """
    Custom admin dashboard view with business metrics
    """
    from django.shortcuts import render
    
    context = {
        'title': 'NEYO Dashboard',
        'site_header': admin.site.site_header,
    }
    
    # Add business metrics if models exist
    try:
        from products.models import Product
        from orders.models import Order
        from cart.models import Cart
        from django.contrib.auth.models import User
        from django.db.models import Sum, Count
        from datetime import datetime, timedelta
        
        # Product metrics
        context.update({
            'total_products': Product.objects.filter(is_active=True).count(),
            'featured_products': Product.objects.filter(is_featured=True, is_active=True).count(),
            'out_of_stock': Product.objects.filter(stock=0).count(),
            'low_stock': Product.objects.filter(stock__lte=10, stock__gt=0).count(),
        })
        
        # Order metrics
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        context.update({
            'total_orders': Order.objects.count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
            'completed_orders': Order.objects.filter(status='delivered').count(),
            'orders_this_week': Order.objects.filter(created_at__date__gte=week_ago).count(),
            'total_revenue': Order.objects.filter(
                payment_status='paid'
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        })
        
        # User metrics
        context.update({
            'total_users': User.objects.count(),
            'active_carts': Cart.objects.exclude(items=None).count(),
            'new_users_this_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
        })
        
        # Recent orders (last 5)
        context['recent_orders'] = Order.objects.select_related('user').order_by('-created_at')[:5]
        
        # Low stock products
        context['low_stock_products'] = Product.objects.filter(
            stock__lte=10, is_active=True
        ).order_by('stock')[:5]
        
    except (ImportError, Exception):
        # Fallback if models don't exist yet
        context.update({
            'setup_mode': True,
            'message': 'Complete the setup by running migrations and creating your first products.'
        })
    
    return render(request, 'admin/neyo_dashboard.html', context)

# ================================
# ADMIN ACTIONS & UTILITIES
# ================================

def make_featured(modeladmin, request, queryset):
    """
    Bulk action to mark products as featured
    """
    updated = queryset.update(is_featured=True)
    modeladmin.message_user(
        request, 
        f'{updated} product(s) marked as featured.'
    )
make_featured.short_description = "Mark selected products as featured"

def make_unfeatured(modeladmin, request, queryset):
    """
    Bulk action to unmark products as featured
    """
    updated = queryset.update(is_featured=False)
    modeladmin.message_user(
        request, 
        f'{updated} product(s) unmarked as featured.'
    )
make_unfeatured.short_description = "Unmark selected products as featured"

def make_active(modeladmin, request, queryset):
    """
    Bulk action to activate products
    """
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request, 
        f'{updated} product(s) activated.'
    )
make_active.short_description = "Activate selected products"

def make_inactive(modeladmin, request, queryset):
    """
    Bulk action to deactivate products
    """
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request, 
        f'{updated} product(s) deactivated.'
    )
make_inactive.short_description = "Deactivate selected products"

# ================================
# ADMIN MIXINS FOR REUSABILITY
# ================================

class TimestampAdminMixin:
    """
    Mixin to add created_at/updated_at to readonly fields
    """
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if hasattr(self.model, 'created_at'):
            if 'created_at' not in fields:
                fields.append('created_at')
        if hasattr(self.model, 'updated_at'):
            if 'updated_at' not in fields:
                fields.append('updated_at')
        return fields

class UserTrackingAdminMixin:
    """
    Mixin to automatically set user fields
    """
    def save_model(self, request, obj, form, change):
        if hasattr(obj, 'created_by') and not change:
            obj.created_by = request.user
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

class BulkActionAdminMixin:
    """
    Mixin to add common bulk actions
    """
    actions = [make_active, make_inactive]

# ================================
# HELPER FUNCTIONS
# ================================

def admin_thumbnail(image_field, width=50, height=50):
    """
    Generate HTML for admin thumbnails
    """
    def thumbnail(obj):
        if hasattr(obj, image_field) and getattr(obj, image_field):
            image = getattr(obj, image_field)
            return format_html(
                '<img src="{}" style="width: {}px; height: {}px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;">',
                image.url, width, height
            )
        return format_html('<span style="color: #999;">No image</span>')
    
    thumbnail.short_description = 'Thumbnail'
    return thumbnail

def admin_link_to_object(field_name, link_text=None):
    """
    Generate admin link to related object
    """
    def link(obj):
        related_obj = getattr(obj, field_name)
        if related_obj:
            url = reverse(
                f'admin:{related_obj._meta.app_label}_{related_obj._meta.model_name}_change',
                args=[related_obj.pk]
            )
            text = link_text or str(related_obj)
            return format_html('<a href="{}">{}</a>', url, text)
        return '-'
    
    link.short_description = field_name.replace('_', ' ').title()
    return link

# ================================
# ADMIN SITE ENHANCEMENTS
# ================================

# Add custom CSS/JS to admin
class Media:
    css = {
        'all': ('admin/css/neyo-admin.css',)
    }
    js = ('admin/js/neyo-admin.js',)

# Apply custom media to admin site
admin.site.Media = Media

# ================================
# LOGGING FOR ADMIN ACTIONS
# ================================

import logging
logger = logging.getLogger('neyo.admin')

def log_admin_action(user, action, object_name):
    """
    Log admin actions for audit trail
    """
    logger.info(f"Admin Action: {user.username} {action} {object_name}")

# You can extend this to add more comprehensive admin customizations
# such as custom filters, dashboard widgets, etc.