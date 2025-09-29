from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse

def cart_view(request):
    """Shopping cart view"""
    return HttpResponse("<h1>Shopping Cart</h1><p>Cart functionality coming soon...</p>")

def add_to_cart(request):
    """Add item to cart"""
    return JsonResponse({"success": False, "message": "Coming soon"})

def update_cart(request, item_id):
    """Update cart item"""
    return JsonResponse({"success": False, "message": "Coming soon"})

def remove_from_cart(request, item_id):
    """Remove item from cart"""
    return JsonResponse({"success": False, "message": "Coming soon"})

def clear_cart(request):
    """Clear entire cart"""
    return redirect("cart:view")

def cart_count(request):
    """Get cart count (AJAX)"""
    return JsonResponse({"count": 0})