# Billing System

A Django-based billing system with web interface for creating invoices, calculating bills, and managing customer purchases.

## Features

- **Product Management**: CRUD operations for products with name, SKU, price, tax percentage, and stock quantity
- **Billing System**: 
  - Dynamic form to add multiple products to a bill
  - Automatic calculation of subtotal, tax, and total amount
  - Denomination-based balance calculation
  - Invoice generation with detailed breakdown
- **Customer Management**: Email-based customer tracking and purchase history
- **Async Email Sending**: Background email sending for invoices
- **Purchase History**: View past purchases by customer email
- **Admin Interface**: Django admin for managing all data

## Requirements

- Python 3.8+
- Django 4.2+
- Django REST Framework
- Django Filter
- Django REST Framework SimpleJWT

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd billing
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv billing_env
   # On Windows:
   billing_env\Scripts\activate
   # On Unix/MacOS:
   source billing_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Seed sample products** (optional)
   ```bash
   python manage.py seed_products
   ```

6. **Create superuser for admin access**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Billing System: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/
   - API: http://127.0.0.1:8000/api/

## Usage

### Creating a Bill

1. Navigate to the billing page at http://127.0.0.1:8000/
2. Enter customer email
3. Add products by entering Product ID and quantity
4. Click "Add New" to add more products
5. Enter available denominations in the shop
6. Enter cash paid by customer
7. Click "Generate Bill" to create the invoice

### Viewing Customer History

1. Click "View Customer History" from the billing page
2. Enter customer email
3. View all past purchases and click on any to see details

### Managing Products

1. Access admin panel at http://127.0.0.1:8000/admin/
2. Navigate to Products section
3. Add, edit, or delete products as needed

### API Endpoints

The system also provides REST API endpoints:

- `/api/products/` - Product CRUD operations
- `/api/invoices/` - Invoice management
- `/api/payments/` - Payment tracking
- `/api/token/` - JWT token authentication

## Project Structure

```
billing/
├── accounts/          # User authentication and roles
├── customers/         # Customer profiles
├── products/          # Product management
├── invoices/          # Invoice and invoice items
├── payments/          # Payment tracking
├── billing_frontend/  # Web interface for billing
│   ├── templates/     # HTML templates
│   ├── management/    # Management commands
│   └── views.py       # View logic
└── billing/           # Project settings
```

## Assumptions Made

1. **Product ID**: Used SKU field as Product ID for product identification
2. **Denominations**: Default denominations are 500, 50, 20, 10, 5, 2, 1
3. **Email Backend**: Console email backend for development (can be configured for production)
4. **User Creation**: If customer email doesn't exist in system, a new user is automatically created
5. **Rounding**: Net price is rounded down to nearest integer for balance calculation
6. **Tax Calculation**: Tax is calculated as percentage of purchase price
7. **Async Email**: Uses threading for background email sending

## Configuration

### Email Settings

For production, update email settings in `billing/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

### Database

Default uses SQLite. For production, update `DATABASES` in settings:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'billing_db',
        'USER': 'billing_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Testing

Run tests with:
```bash
python manage.py test
```

## Production Deployment

1. Set `DEBUG = False` in settings
2. Update `ALLOWED_HOSTS`
3. Configure production database
4. Set up proper email backend
5. Configure static files serving
6. Use a production WSGI server (Gunicorn, uWSGI)

## License

This project is created for assessment purposes.

## Support

For issues or questions, please contact the development team.