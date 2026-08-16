from rest_framework import viewsets

from .models import Product
from .permissions import (
    IsAdmin,
    IsAdminOrStaff,
    IsAuthenticatedUser,
)
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.all()

    serializer_class = ProductSerializer

    def get_permissions(self):

        if self.action in ["list", "retrieve"]:
            permission_classes = [
                IsAuthenticatedUser
            ]

        elif self.action in [
            "create",
            "update",
            "partial_update",
        ]:
            permission_classes = [
                IsAdminOrStaff
            ]

        elif self.action == "destroy":
            permission_classes = [
                IsAdmin
            ]

        else:
            permission_classes = [
                IsAuthenticatedUser
            ]

        return [
            permission()
            for permission in permission_classes
        ]