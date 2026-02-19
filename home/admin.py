from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Payment, SuccessfulPayment

# Unregister the default User admin
admin.site.unregister(User)

# Register User with custom admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-id']
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'transaction_id', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'transaction_id', 'esewa_ref_id']
    readonly_fields = ['created_at']
    ordering = ['-id']

@admin.register(SuccessfulPayment)
class SuccessfulPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'transaction_id', 'payment_date', 'subscription_end']
    list_filter = ['payment_date']
    search_fields = ['user__username', 'transaction_id', 'esewa_ref_id']
    readonly_fields = ['payment_date', 'subscription_start']
    ordering = ['-id']
