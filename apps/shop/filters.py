import django_filters

from apps.shop.models import Product


class ProductFilter(django_filters.FilterSet):
    """Фильтр для модели Product, позволяющий фильтровать товары по различным критериям.
    Данный фильтр используется в представлениях на основе Django REST Framework
    для реализации гибкой фильтрации списка товаров. Поддерживает фильтрацию по:
      - диапазону текущей цены (min_price, max_price),
      - наличию на складе (in_stock),
      - дате создания (created_at)."""

    max_price = django_filters.NumberFilter(
        field_name="price_current",
        lookup_expr="lte",
        label="Максимальная цена",
        help_text="Максимальная цена",
    )
    min_price = django_filters.NumberFilter(
        field_name="price_current",
        lookup_expr="gte",
        label="Минимальная цена",
        help_text="Минимальная цена",
    )
    in_stock = django_filters.NumberFilter(
        lookup_expr="gte",
        label="В наличии",
        help_text="Товары с количеством на складе больше или равным указанному.",
    )
    created_at = django_filters.DateTimeFilter(
        lookup_expr="gte",
        label="Дата создания",
        help_text="Товары, созданные с указанной даты и времени.",
    )

    class Meta:
        """Метакласс, определяющий настройки фильтра."""

        model = Product
        fields = ["max_price", "min_price", "in_stock", "created_at"]
