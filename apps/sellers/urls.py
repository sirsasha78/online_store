from django.urls import path

from apps.sellers.views import (
    SellersView,
    SellerProductsView,
    SellerProductView,
    SellerOrdersView,
    SellerOrderItemsView,
)


urlpatterns = [
    path("", SellersView.as_view(), name="seller_profile"),
    path("products/", SellerProductsView.as_view(), name="seller_products"),
    path("products/<slug:slug>/", SellerProductView.as_view(), name="seller_product"),
    path("orders/", SellerOrdersView.as_view(), name="seller_orders"),
    path(
        "orders/<str:tx_ref>/",
        SellerOrderItemsView.as_view(),
        name="seller_order_items",
    ),
]
