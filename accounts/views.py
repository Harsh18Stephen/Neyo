from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def login_view(request):
    """User login view"""
    return HttpResponse("<h1>Login</h1><p>Login form coming soon...</p>")

def logout_view(request):
    """User logout view"""
    logout(request)
    return redirect("core:home")

def google_login(request):
    """Google OAuth login"""
    return HttpResponse("<h1>Google Login</h1><p>Google OAuth coming soon...</p>")

def google_callback(request):
    """Google OAuth callback"""
    return HttpResponse("<h1>Google Callback</h1><p>OAuth callback coming soon...</p>")

@login_required
def profile(request):
    """User profile view"""
    return HttpResponse(f"<h1>Profile</h1><p>Welcome {request.user.username}!</p>")

@login_required
def edit_profile(request):
    """Edit user profile"""
    return HttpResponse("<h1>Edit Profile</h1><p>Profile editing coming soon...</p>")