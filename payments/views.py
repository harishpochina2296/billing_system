from django.db import transaction
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from invoices.models import Invoice

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):

    queryset = Payment.objects.select_related(
        "invoice",
    )

    serializer_class = PaymentSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        invoice = serializer.validated_data["invoice"]
        amount = serializer.validated_data["amount"]

        # -----------------------------------------
        # Invoice must be ISSUED
        # -----------------------------------------

        if invoice.status != Invoice.Status.ISSUED:
            return Response(
                {
                    "invoice":
                    "Payments can only be created for issued invoices."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------------
        # Payment amount must match invoice total
        # -----------------------------------------

        if amount != invoice.total_amount:
            return Response(
                {
                    "amount":
                    f"Payment amount must be exactly "
                    f"{invoice.total_amount}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------------
        # Prevent duplicate payment
        # -----------------------------------------

        existing_payment = Payment.objects.filter(
            invoice=invoice,
            status__in=[
                Payment.Status.PENDING,
                Payment.Status.SUCCESS,
            ],
        ).exists()

        if existing_payment:
            return Response(
                {
                    "invoice":
                    "A payment already exists for this invoice."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------------
        # Create payment
        # -----------------------------------------

        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=serializer.validated_data[
                "payment_method"
            ],
            transaction_id=serializer.validated_data.get(
                "transaction_id"
            ),
        )

        output_serializer = self.get_serializer(
            payment
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    # -----------------------------------------
    # PAYMENT FAIL
    # -----------------------------------------

    @action(
        detail=True,
        methods=["post"],
    )
    @transaction.atomic
    def fail(self, request, pk=None):

        payment = self.get_object()

        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "detail":
                    "Only pending payments can be marked as failed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice = payment.invoice

        if invoice.status != Invoice.Status.ISSUED:
            return Response(
                {
                    "detail":
                    "Payment can only fail for an issued invoice."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.status = Payment.Status.FAILED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        invoice.status = Invoice.Status.ISSUED

        invoice.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        serializer = self.get_serializer(
            payment
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
       
    # -----------------------------------------
    # PAYMENT SUCCESS
    # -----------------------------------------

    @action(
        detail=True,
        methods=["post"],
    )
    @transaction.atomic
    def succeed(self, request, pk=None):

        payment = self.get_object()

        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "detail":
                    "Only pending payments can be marked as successful."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice = payment.invoice

        if invoice.status != Invoice.Status.ISSUED:
            return Response(
                {
                    "detail":
                    "Payment can only succeed for an issued invoice."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.status = Payment.Status.SUCCESS
        payment.paid_at = timezone.now()

        payment.save(
            update_fields=[
                "status",
                "paid_at",
                "updated_at",
            ]
        )

        invoice.status = Invoice.Status.PAID

        invoice.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        serializer = self.get_serializer(
            payment
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )