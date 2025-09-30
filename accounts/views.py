from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, Address

# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'core:home')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('core:home')

def google_login(request):
    messages.info(request, 'Google login will be implemented soon')
    return redirect('accounts:login')

def google_callback(request):
    return redirect('accounts:login')

@login_required
def profile(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's addresses
    shipping_addresses = Address.objects.filter(user=request.user, type='shipping')
    billing_addresses = Address.objects.filter(user=request.user, type='billing')
    
    # Get recent orders
    from orders.models import Order
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'shipping_addresses': shipping_addresses,
        'billing_addresses': billing_addresses,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user information
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update profile information
        profile.phone = request.POST.get('phone', '')
        profile.save()
        
        messages.success(request, 'Profile updated successfully')
        return redirect('accounts:profile')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def add_address(request):
    if request.method == 'POST':
        address_type = request.POST.get('type')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        company = request.POST.get('company', '')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2', '')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country', 'United States')
        is_default = request.POST.get('is_default') == 'on'
        
        # If setting as default, unset other defaults
        if is_default:
            Address.objects.filter(user=request.user, type=address_type, is_default=True).update(is_default=False)
        
        # Create address
        Address.objects.create(
            user=request.user,
            type=address_type,
            first_name=first_name,
            last_name=last_name,
            company=company,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default
        )
        
        messages.success(request, f'{address_type.title()} address added successfully')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/add_address.html')

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.first_name = request.POST.get('first_name')
        address.last_name = request.POST.get('last_name')
        address.company = request.POST.get('company', '')
        address.address_line_1 = request.POST.get('address_line_1')
        address.address_line_2 = request.POST.get('address_line_2', '')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.postal_code = request.POST.get('postal_code')
        address.country = request.POST.get('country', 'United States')
        
        is_default = request.POST.get('is_default') == 'on'
        if is_default and not address.is_default:
            # Unset other defaults
            Address.objects.filter(user=request.user, type=address.type, is_default=True).update(is_default=False)
        address.is_default = is_default
        
        address.save()
        
        messages.success(request, 'Address updated successfully')
        return redirect('accounts:profile')
    
    context = {
        'address': address,
    }
    
    return render(request, 'accounts/edit_address.html', context)

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully')
    return redirect('accounts:profile')