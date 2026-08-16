from django.contrib import admin
from .models import CustomerEmail, Denomination, Purchase


@admin.register(CustomerEmail)
class CustomerEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']


@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    list_display = ['value', 'count', 'is_active']
    list_filter = ['is_active']
    ordering = ['-value']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['customer_email', 'invoice', 'cash_paid', 'balance_returned', 'created_at']
    list_filter = ['created_at']
    search_fields = ['customer_email__email']
    readonly_fields = ['created_at']