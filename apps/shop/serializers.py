from rest_framework import serializers


class CategorySerializer(serializers.Serializer):
    """Сериализатор для представления данных категории товара.
    Преобразует данные категории в формат JSON и обратно.
    Используется для отображения и создания категорий в API."""

    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(read_only=True)
    image = serializers.ImageField()


class SellerShopSerializer(serializers.Serializer):
    """Сериализатор для представления данных магазина продавца.
    Преобразует данные модели продавца (Seller) в JSON-формат,
    включая название магазина, уникальный идентификатор (slug) и аватар.
    Используется для отображения основной информации о магазине
    в списке объявлений, карточке товара или на странице продавца."""

    name = serializers.CharField(source="business_name")
    slug = serializers.SlugField()
    avatar = serializers.CharField(source="user.avatar")


class ProductSerializer(serializers.Serializer):
    """Сериализатор для представления данных продукта.
    Преобразует объекты товаров в JSON-формат и обратно. Включает основные
    атрибуты товара, такие как название, описание, цена, категория, изображения
    и информация о продавце. Используется для отображения детальной и
    краткой информации о товаре в API."""

    seller = SellerShopSerializer()
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField()
    description = serializers.CharField()
    price_old = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = CategorySerializer()
    in_stock = serializers.IntegerField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)


class CreateProductSerializer(serializers.Serializer):
    """Сериализатор для создания нового продукта.
    Преобразует входные данные при создании продукта из формата JSON в
    валидированные Python-объекты. Проводит валидацию полей, необходимых
    для добавления товара в систему."""

    name = serializers.CharField(max_length=100)
    description = serializers.CharField()
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_slug = serializers.SlugField()
    in_stock = serializers.IntegerField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)


class OrderItemProductSerializer(serializers.Serializer):
    """Сериализатор для представления данных продукта в составе заказа.
    Преобразует данные продукта, входящего в заказ, в формат, пригодный для вывода.
    Включает информацию о продавце, названии, уникальном идентификаторе (slug)
    и итоговой стоимости продукта с учётом количества.
    Используется для вложенного отображения товаров в деталях заказа."""

    seller = SellerShopSerializer()
    name = serializers.CharField()
    slug = serializers.SlugField()
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="get_total"
    )


class OrderItemSerializer(serializers.Serializer):
    """Сериализатор для представления элемента заказа.
    Преобразует данные об отдельном товаре в заказе в формат, пригодный для вывода.
    Включает информацию о продукте, количество единиц и итоговую стоимость позиции."""

    product = OrderItemProductSerializer()
    quantity = serializers.IntegerField()
    total = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="get_total"
    )


class ToggleCartItemSerializer(serializers.Serializer):
    """Сериализатор для управления элементом корзины.
    Предназначен для валидации данных при добавлении, изменении или удалении
    товара в корзине пользователя."""

    slug = serializers.SlugField()
    quantity = serializers.IntegerField(min_value=0)
