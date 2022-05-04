from django.urls import path
from orders.views import OrderView, CartView

urlpatterns = [
    path('', OrderView.as_view()),
    path('/carts', CartView.as_view()),
]
