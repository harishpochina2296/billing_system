from django.urls import path
from . import views

urlpatterns = [
    path('', views.billing_page, name='billing_page'),
    path('history/', views.customer_history, name='customer_history'),
]