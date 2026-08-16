from rest_framework import serializers

from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceItem

        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
            "tax_percentage",
            "total_price",
        ]

        read_only_fields = [
            "id",
            "unit_price",
            "tax_percentage",
            "total_price",
        ]


class InvoiceSerializer(serializers.ModelSerializer):

    items = InvoiceItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Invoice

        fields = [
            "id",
            "invoice_number",
            "customer",
            "created_by",
            "status",
            "subtotal",
            "tax_amount",
            "total_amount",
            "issue_date",
            "due_date",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "status",
            "subtotal",
            "tax_amount",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]