from django.urls import path

from apps.shop.views import (
    CategoriesView,
    ProductView,
    ProductsView,
    ProductsByCategoryView,
    ProductsBySellerView,
    CartView,
    CheckoutView,
)


urlpatterns = [
    path("categories/", CategoriesView.as_view(), name="categories"),
    path(
        "categories/<slug:slug>/",
        ProductsByCategoryView.as_view(),
        name="products_by_category",
    ),
    path(
        "sellers/<slug:slug>/",
        ProductsBySellerView.as_view(),
        name="products_by_seller",
    ),
    path("products/", ProductsView.as_view(), name="products_all"),
    path("products/<slug:slug>/", ProductView.as_view(), name="product_detail"),
    path("cart/", CartView.as_view(), name="cart"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
]
