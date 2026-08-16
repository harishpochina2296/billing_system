from django.db import models
from decimal import Decimal


class CustomerEmail(models.Model):
    """Simple customer model for email-based purchases"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.email


class Denomination(models.Model):
    """Available denominations in the shop"""
    value = models.PositiveIntegerField()
    count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-value']
    
    def __str__(self):
        return f"{self.value}: {self.count}"


class Purchase(models.Model):
    """Customer purchase record"""
    customer_email = models.ForeignKey(CustomerEmail, on_delete=models.PROTECT, related_name='purchases')
    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.PROTECT, related_name='email_purchases', null=True, blank=True)
    cash_paid = models.DecimalField(max_digits=12, decimal_places=2)
    balance_returned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Purchase by {self.customer_email.email} at {self.created_at}"