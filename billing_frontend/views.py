from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import asyncio
from threading import Thread

from products.models import Product
from invoices.models import Invoice, InvoiceItem
from customers.models import Customer
from accounts.models import User
from .models import CustomerEmail, Denomination, Purchase


def calculate_denominations(balance, available_denominations):
    """Calculate optimal denomination breakdown for balance"""
    result = {}
    remaining = int(balance)
    
    for denom in available_denominations:
        if remaining <= 0:
            break
        if denom.value <= remaining and denom.count > 0:
            count = min(remaining // denom.value, denom.count)
            if count > 0:
                result[denom.value] = count
                remaining -= denom.value * count
    
    return result, remaining == 0


def send_invoice_email_async(invoice, customer_email):
    """Send invoice email asynchronously"""
    try:
        subject = f'Invoice {invoice.invoice_number}'
        
        # Calculate bill details
        items_data = []
        for item in invoice.items.all():
            items_data.append({
                'product_id': item.product.sku,
                'name': item.product.name,
                'unit_price': float(item.unit_price),
                'quantity': item.quantity,
                'purchase_price': float(item.unit_price * item.quantity),
                'tax_percentage': float(item.tax_percentage),
                'tax_payable': float(item.unit_price * item.quantity * item.tax_percentage / 100),
                'total_price': float(item.total_price),
            })
        
        context = {
            'invoice': invoice,
            'items': items_data,
            'customer_email': customer_email,
        }
        
        message = render_to_string('billing_frontend/email_template.txt', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [customer_email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email: {e}")


def billing_page(request):
    """Page 1: Billing calculation page"""
    if request.method == 'POST':
        return generate_bill(request)
    
    # Get default denominations
    default_denominations = [500, 50, 20, 10, 5, 2, 1]
    
    context = {
        'denominations': default_denominations,
        'products': Product.objects.filter(is_active=True),
    }
    return render(request, 'billing_frontend/billing_page.html', context)


@transaction.atomic
def generate_bill(request):
    """Generate bill from form data"""
    customer_email = request.POST.get('customer_email')
    cash_paid = Decimal(request.POST.get('cash_paid', '0'))
    
    # Get product entries
    product_entries = []
    i = 0
    while f'product_id_{i}' in request.POST:
        product_id = request.POST.get(f'product_id_{i}')
        quantity = request.POST.get(f'quantity_{i}')
        
        if product_id and quantity:
            try:
                product = Product.objects.get(sku=product_id, is_active=True)
                quantity = int(quantity)
                if quantity > 0:
                    product_entries.append({
                        'product': product,
                        'quantity': quantity
                    })
            except Product.DoesNotExist:
                messages.error(request, f'Product with ID {product_id} not found')
                return redirect('billing_page')
        i += 1
    
    if not product_entries:
        messages.error(request, 'Please add at least one product')
        return redirect('billing_page')
    
    # Get denominations
    denominations_input = {}
    for denom_value in [500, 50, 20, 10, 5, 2, 1]:
        count = request.POST.get(f'denom_{denom_value}', 0)
        if count:
            denominations_input[denom_value] = int(count)
    
    # Calculate bill
    items_data = []
    subtotal = Decimal('0')
    total_tax = Decimal('0')
    
    for entry in product_entries:
        product = entry['product']
        quantity = entry['quantity']
        
        unit_price = product.price
        tax_percentage = product.tax_percentage
        purchase_price = unit_price * quantity
        tax_payable = purchase_price * tax_percentage / Decimal('100')
        total_price = purchase_price + tax_payable
        
        items_data.append({
            'product': product,
            'product_id': product.sku,
            'unit_price': unit_price,
            'quantity': quantity,
            'purchase_price': purchase_price,
            'tax_percentage': tax_percentage,
            'tax_payable': tax_payable,
            'total_price': total_price,
        })
        
        subtotal += purchase_price
        total_tax += tax_payable
    
    net_price = subtotal + total_tax
    rounded_net_price = net_price.quantize(Decimal('1'))
    balance = cash_paid - rounded_net_price
    
    # Calculate balance denominations
    available_denominations = []
    for value, count in denominations_input.items():
        denom = Denomination(value=value, count=count)
        available_denominations.append(denom)
    
    balance_denominations, exact_change = calculate_denominations(balance, available_denominations)
    
    if not exact_change:
        messages.warning(request, 'Cannot provide exact change with available denominations')
    
    # Create or get customer email
    customer_email_obj, created = CustomerEmail.objects.get_or_create(
        email=customer_email
    )
    
    # Create invoice
    invoice_number = f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create or get customer
    try:
        user = User.objects.get(email=customer_email)
        customer = Customer.objects.get(user=user)
    except (User.DoesNotExist, Customer.DoesNotExist):
        # Create user and customer
        username = customer_email.split('@')[0]
        user = User.objects.create_user(
            username=username,
            email=customer_email,
            role=User.Role.CUSTOMER
        )
        customer = Customer.objects.create(user=user)
    
    invoice = Invoice.objects.create(
        invoice_number=invoice_number,
        customer=customer,
        created_by=request.user if request.user.is_authenticated else User.objects.first(),
        status=Invoice.Status.ISSUED,
        subtotal=subtotal,
        tax_amount=total_tax,
        total_amount=net_price,
        issue_date=timezone.now().date(),
    )
    
    # Create invoice items
    for item_data in items_data:
        InvoiceItem.objects.create(
            invoice=invoice,
            product=item_data['product'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            tax_percentage=item_data['tax_percentage'],
            total_price=item_data['total_price'],
        )
    
    # Create purchase record
    purchase = Purchase.objects.create(
        customer_email=customer_email_obj,
        invoice=invoice,
        cash_paid=cash_paid,
        balance_returned=balance if balance > 0 else Decimal('0'),
    )
    
    # Send invoice email asynchronously
    email_thread = Thread(target=send_invoice_email_async, args=(invoice, customer_email))
    email_thread.start()
    
    context = {
        'customer_email': customer_email,
        'items': items_data,
        'subtotal': subtotal,
        'total_tax': total_tax,
        'net_price': net_price,
        'rounded_net_price': rounded_net_price,
        'cash_paid': cash_paid,
        'balance': balance if balance > 0 else Decimal('0'),
        'balance_denominations': balance_denominations,
        'invoice_number': invoice_number,
    }
    
    return render(request, 'billing_frontend/bill_result.html', context)


def customer_history(request):
    """View customer purchase history"""
    email = request.GET.get('email')
    purchases = []
    selected_purchase = None
    
    if email:
        try:
            customer_email = CustomerEmail.objects.get(email=email)
            purchases = Purchase.objects.filter(customer_email=customer_email).order_by('-created_at')
            
            purchase_id = request.GET.get('purchase_id')
            if purchase_id:
                selected_purchase = get_object_or_404(Purchase, id=purchase_id, customer_email=customer_email)
        except CustomerEmail.DoesNotExist:
            messages.error(request, 'Customer not found')
    
    context = {
        'email': email,
        'purchases': purchases,
        'selected_purchase': selected_purchase,
    }
    return render(request, 'billing_frontend/customer_history.html', context)