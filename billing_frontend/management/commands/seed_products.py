from django.core.management.base import BaseCommand
from products.models import Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed the database with sample products'

    def handle(self, *args, **options):
        products_data = [
            {
                'name': 'Laptop',
                'sku': 'LAP001',
                'description': 'High-performance laptop',
                'price': Decimal('899.99'),
                'tax_percentage': Decimal('10.00'),
                'stock_quantity': 50,
                'is_active': True,
            },
            {
                'name': 'Wireless Mouse',
                'sku': 'MOU001',
                'description': 'Ergonomic wireless mouse',
                'price': Decimal('29.99'),
                'tax_percentage': Decimal('5.00'),
                'stock_quantity': 200,
                'is_active': True,
            },
            {
                'name': 'USB Keyboard',
                'sku': 'KEY001',
                'description': 'Mechanical keyboard',
                'price': Decimal('79.99'),
                'tax_percentage': Decimal('8.00'),
                'stock_quantity': 150,
                'is_active': True,
            },
            {
                'name': 'Monitor 24"',
                'sku': 'MON001',
                'description': '24-inch LED monitor',
                'price': Decimal('199.99'),
                'tax_percentage': Decimal('12.00'),
                'stock_quantity': 80,
                'is_active': True,
            },
            {
                'name': 'Webcam HD',
                'sku': 'CAM001',
                'description': 'HD webcam with microphone',
                'price': Decimal('49.99'),
                'tax_percentage': Decimal('5.00'),
                'stock_quantity': 120,
                'is_active': True,
            },
            {
                'name': 'Headphones',
                'sku': 'HEA001',
                'description': 'Noise-cancelling headphones',
                'price': Decimal('149.99'),
                'tax_percentage': Decimal('10.00'),
                'stock_quantity': 60,
                'is_active': True,
            },
            {
                'name': 'USB Hub',
                'sku': 'HUB001',
                'description': '7-port USB hub',
                'price': Decimal('19.99'),
                'tax_percentage': Decimal('5.00'),
                'stock_quantity': 300,
                'is_active': True,
            },
            {
                'name': 'External HDD 1TB',
                'sku': 'HDD001',
                'description': '1TB external hard drive',
                'price': Decimal('59.99'),
                'tax_percentage': Decimal('8.00'),
                'stock_quantity': 100,
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for product_data in products_data:
            sku = product_data['sku']
            product, created = Product.objects.update_or_create(
                sku=sku,
                defaults=product_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created product: {product.name} ({sku})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated product: {product.name} ({sku})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} new products, '
                f'updated {updated_count} existing products.'
            )
        )