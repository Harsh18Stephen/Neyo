from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, ProductImage, ProductVariant

def product_list(request):
    """Product catalog with pagination"""
    # Get all active products
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'search_query': search_query,
        'total_products': products.count(),
    }
    
    return render(request, 'products/list.html', context)

def product_detail(request, slug):
    """Product detail page with images and variants"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get all images for this product
    images = product.images.all().order_by('order', 'id')
    
    # Get all variants (sizes) for this product
    variants = product.variants.all().order_by('size')
    
    # Get related products (same price range or featured)
    related_products = Product.objects.filter(
        is_active=True
    ).exclude(
        id=product.id
    ).filter(
        Q(price__gte=product.price - 10) & Q(price__lte=product.price + 10)
    )[:4]
    
    context = {
        'product': product,
        'images': images,
        'variants': variants,
        'related_products': related_products,
    }
    
    return render(request, 'products/detail.html', context)