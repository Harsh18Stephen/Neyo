from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Address

# Register your models here.

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, AddressInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'email_notifications', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('email_notifications', 'created_at')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'get_full_name', 'city', 'state', 'is_default')
    list_filter = ('type', 'is_default', 'state', 'country')
    search_fields = ('user__username', 'first_name', 'last_name', 'city')