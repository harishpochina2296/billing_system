from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from customers.models import Customer
from invoices.models import Invoice
from payments.models import Payment


class PaymentTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        # -----------------------------------------
        # Create test user
        # -----------------------------------------

        self.user = User.objects.create_user(
            username="payment_test_user",
            password="TestPass123!",
            role="CUSTOMER",
        )

        # -----------------------------------------
        # Create customer profile
        # -----------------------------------------

        self.customer = Customer.objects.create(
            user=self.user,
            phone="9876543210",
            address="Test Address",
            company_name="Test Company",
        )

        self.client.force_authenticate(
            user=self.user
        )

        # -----------------------------------------
        # Create issued invoice
        # -----------------------------------------

        self.invoice = Invoice.objects.create(
            invoice_number="TEST-INV-001",
            customer=self.customer,
            created_by=self.user,
            status=Invoice.Status.ISSUED,
            subtotal=Decimal("1000.00"),
            tax_amount=Decimal("180.00"),
            total_amount=Decimal("1180.00"),
        )

        # -----------------------------------------
        # Create pending payment
        # -----------------------------------------

        self.payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal("1180.00"),
            payment_method="UPI",
            transaction_id="TEST-TXN-001",
        )

    # -----------------------------------------
    # PENDING → FAILED
    # -----------------------------------------

    def test_pending_payment_can_be_failed(self):

        response = self.client.post(
            f"/api/payments/{self.payment.id}/fail/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.payment.refresh_from_db()
        self.invoice.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.FAILED,
        )

        self.assertEqual(
            self.invoice.status,
            Invoice.Status.ISSUED,
        )

    # -----------------------------------------
    # FAILED → FAILED should fail
    # -----------------------------------------

    def test_failed_payment_cannot_be_failed_again(self):

        self.payment.status = Payment.Status.FAILED

        self.payment.save(
            update_fields=["status"]
        )

        response = self.client.post(
            f"/api/payments/{self.payment.id}/fail/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["detail"],
            "Only pending payments can be marked as failed.",
        )

    # -----------------------------------------
    # PAID invoice cannot have failed payment
    # -----------------------------------------

    def test_payment_cannot_fail_for_paid_invoice(self):

        self.invoice.status = Invoice.Status.PAID

        self.invoice.save(
            update_fields=["status"]
        )

        response = self.client.post(
            f"/api/payments/{self.payment.id}/fail/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["detail"],
            "Payment can only fail for an issued invoice.",
        )