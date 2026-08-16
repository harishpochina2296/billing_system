from decimal import Decimal

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from products.models import Product

from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):

    queryset = Invoice.objects.prefetch_related(
        "items__product"
    ).select_related(
        "customer",
        "created_by",
    )

    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        customer_id = request.data.get("customer")
        items_data = request.data.get("items", [])

        if not customer_id:
            return Response(
                {"customer": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not items_data:
            return Response(
                {
                    "items":
                    "At least one invoice item is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        invoice = Invoice.objects.create(
            invoice_number=serializer.validated_data[
                "invoice_number"
            ],
            customer=serializer.validated_data[
                "customer"
            ],
            created_by=request.user,
            issue_date=serializer.validated_data.get(
                "issue_date"
            ),
            due_date=serializer.validated_data.get(
                "due_date"
            ),
            notes=serializer.validated_data.get(
                "notes",
                "",
            ),
        )

        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")

        for item_data in items_data:

            product_id = item_data.get("product")
            quantity = item_data.get("quantity")

            if not product_id:
                return Response(
                    {"product": "Product is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not quantity or quantity <= 0:
                return Response(
                    {
                        "quantity":
                        "Quantity must be greater than zero."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                product = Product.objects.get(
                    id=product_id,
                    is_active=True,
                )
            except Product.DoesNotExist:
                return Response(
                    {
                        "product":
                        f"Product {product_id} does not exist or is inactive."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            unit_price = product.price
            tax_percentage = product.tax_percentage

            item_subtotal = (
                unit_price * quantity
            )

            item_tax = (
                item_subtotal
                * tax_percentage
                / Decimal("100")
            )

            item_total = (
                item_subtotal + item_tax
            )

            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                tax_percentage=tax_percentage,
                total_price=item_total,
            )

            subtotal += item_subtotal
            tax_amount += item_tax

        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = (
            subtotal + tax_amount
        )

        invoice.save(
            update_fields=[
                "subtotal",
                "tax_amount",
                "total_amount",
                "updated_at",
            ]
        )

        output_serializer = self.get_serializer(
            invoice
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def issue(self, request, pk=None):

        invoice = self.get_object()

        if invoice.status != Invoice.Status.DRAFT:
            return Response(
                {
                    "detail":
                    "Only draft invoices can be issued."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.status = Invoice.Status.ISSUED

        invoice.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        serializer = self.get_serializer(
            invoice
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def cancel(self, request, pk=None):

        invoice = self.get_object()

        if invoice.status == Invoice.Status.PAID:
            return Response(
                {
                    "detail":
                    "Paid invoices cannot be cancelled."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invoice.status == Invoice.Status.CANCELLED:
            return Response(
                {
                    "detail":
                    "Invoice is already cancelled."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.status = Invoice.Status.CANCELLED

        invoice.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        serializer = self.get_serializer(
            invoice
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )