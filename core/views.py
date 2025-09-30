from django.shortcuts import render

# Create your views here.

def homepage(request):
    context = {}
    
    try:
        from products.models import Product
        featured_products = Product.objects.filter(
            is_featured=True, 
            is_active=True
        )[:4]  
        context['featured_products'] = featured_products
    except ImportError:
        context['featured_products'] = None
    
    return render(request, 'core/home.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # TODO: Process contact form (send email, save to database, etc.)
        # For now, just show success message
        from django.contrib import messages
        messages.success(request, 'Thank you for your message! We\'ll get back to you soon.')
        
    return render(request, 'core/contact.html')

def error_404(request, exception):
    return render(request, 'core/404.html', status=404)

def error_500(request):
    return render(request, 'core/500.html', status=500)
