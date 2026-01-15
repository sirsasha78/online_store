from django.urls import path

from apps.profiles.views import (
    ProfileView,
    ShippingAddressesView,
    ShippingAddressViewID,
    OrdersView,
    OrderItemsView,
)


urlpatterns = [
    path("", ProfileView.as_view(), name="profile"),
    path(
        "shipping_addresses/",
        ShippingAddressesView.as_view(),
        name="shipping_addresses",
    ),
    path(
        "shipping_addresses/detail/<str:id>/",
        ShippingAddressViewID.as_view(),
        name="shipping_addresses_detail",
    ),
    path("orders/", OrdersView.as_view(), name="orders"),
    path("orders/<str:tx_ref>/", OrderItemsView.as_view(), name="orders_items"),
]
