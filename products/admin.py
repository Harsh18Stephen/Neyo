from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductImage, ProductVariant

# Register your models here.

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_main', 'order')

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'stock', 'price_adjustment')

@admin.register(Product)  # Fixed: Complete decorator
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_active', 'is_featured')
    
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_thumbnail', 'alt_text', 'is_main', 'order')  # Better name
    list_filter = ('is_main', 'product')
    search_fields = ('product__name', 'alt_text')
    
    def image_thumbnail(self, obj):  # Better method name
        """Display thumbnail of product image in admin list"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">', 
                obj.image.url
            )
        return "No Image"
    image_thumbnail.short_description = "Thumbnail"  # Better description

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'stock', 'variant_price', 'is_in_stock')  # Better name
    list_filter = ('size', 'product')
    search_fields = ('product__name',)
    list_editable = ('stock',)
    
    def variant_price(self, obj):  # Better method name
        """Display the final price for this variant"""
        return f"${obj.get_price():.2f}"
    variant_price.short_description = "Final Price"