from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.db.models import Avg

from apps.profiles.serializers import ShippingAddressSerializer
from apps.shop.models import Review, Product


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
    атрибуты товара: название, описание, цены, категорию, изображения и информацию
    о продавце. Также вычисляет средний рейтинг товара на основе активных отзывов.
    Используется для отображения детальной и краткой информации о товаре
    в API-эндпоинтах, таких как список товаров или страница отдельного товара.
    Методы:
        get_average_rating(obj): Вычисляет и возвращает средний рейтинг товара
            на основе активных (не удалённых) отзывов. Если отзывов нет, возвращает None.
    """

    seller = SellerShopSerializer()
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField()
    description = serializers.CharField()
    price_old = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = CategorySerializer()
    in_stock = serializers.IntegerField()
    average_rating = serializers.SerializerMethodField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)

    def get_average_rating(self, obj: Product) -> float | None:
        """Вычисляет средний рейтинг товара на основе активных отзывов.
        Метод фильтрует отзывы, связанные с переданным товаром, исключает
        удалённые отзывы и рассчитывает среднее значение по полю `rating`."""

        avg = Review.objects.filter(product=obj, is_deleted=False).aggregate(
            Avg("rating")
        )["rating__avg"]
        return round(avg, 1) if avg is not None else None


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
        max_digits=10, decimal_places=2, source="price_current"
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


class CheckoutSerializer(serializers.Serializer):
    """Сериализатор для обработки данных при оформлении заказа.
    Используется для валидации и десериализации данных, переданных при запросе
    на оформление заказа. Требует идентификатор способа доставки в виде UUID."""

    shipping_id = serializers.UUIDField()


class OrderSerializer(serializers.Serializer):
    """Сериализатор для представления данных заказа.
    Преобразует данные модели Order в формат JSON для вывода в API.
    Включает вложенные данные о пользователе, адресе доставки и суммах заказа.
    Используется для отображения информации о заказе, включая статусы доставки и оплаты,
    контактные данные пользователя и стоимость заказа."""

    tx_ref = serializers.CharField()
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    delivery_status = serializers.CharField()
    payment_status = serializers.CharField()
    date_delivered = serializers.DateTimeField()
    shipping_details = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(
        max_digits=100, decimal_places=2, source="get_cart_subtotal"
    )
    total = serializers.DecimalField(
        max_digits=100, decimal_places=2, source="get_cart_total"
    )

    @extend_schema_field(ShippingAddressSerializer)
    def get_shipping_details(self, obj):
        """Возвращает сериализованные данные адреса доставки.
        Метод использует ShippingAddressSerializer для преобразования объекта заказа
        в словарь с деталями адреса доставки."""

        return ShippingAddressSerializer(obj).data


class CheckItemOrderSerializer(serializers.Serializer):
    """Сериализатор для представления элемента заказа в детализированной информации о заказе.
    Используется для сериализации данных о товаре, входящем в состав заказа, включая
    информацию о продукте, количество единиц и общую стоимость позиции."""

    product = ProductSerializer()
    quantity = serializers.IntegerField()
    total = serializers.FloatField(source="get_total")


class ReviewSerializer(serializers.Serializer):
    """Сериализатор для создания и валидации отзыва пользователя на товар.
    Поля:
        id (UUIDField): Уникальный идентификатор отзыва. Предоставляется только для чтения.
        product (SlugRelatedField): Ссылка на товар, используя поле `slug` в качестве идентификатора.
            Принимает значение `slug` товара и проверяет его существование в базе данных.
        rating (IntegerField): Рейтинг, выставленный пользователем. Должен быть в диапазоне от 1 до 5.
        text (CharField): Текст отзыва. Может быть пустым.
    Методы:
        create(validated_data): Создаёт новый отзыв после проверки уникальности.
        update(instance, validated_data): Обновляет существующий отзыв с учётом переданных данных.
            Сохраняет изменения в базе данных и возвращает обновлённый объект.
        validate_rating(value): Проверяет, что рейтинг находится в допустимом диапазоне.
    Особенности:
        - Проверяет, что пользователь не оставил активный (не удалённый) отзыв на указанный товар.
        - Поддерживает логическое удаление: позволяет оставить новый отзыв, если предыдущий помечен как удалённый.
    """

    id = serializers.UUIDField(read_only=True)
    product = serializers.SlugRelatedField(
        slug_field="slug", queryset=Product.objects.all()
    )
    rating = serializers.IntegerField()
    text = serializers.CharField(allow_blank=True, required=False)

    def create(self, validated_data: dict) -> Review:
        """Создаёт новый отзыв после проверки уникальности для данного пользователя и товара.
        Проверяет, существует ли уже неудалённый отзыв от текущего пользователя
        на указанный товар. Если такой отзыв найден — выбрасывается ошибка валидации."""

        user = self.context["request"].user
        product = validated_data["product"]

        review = Review.objects.filter(
            user=user, product=product, is_deleted=False
        ).exists()
        if review:
            raise serializers.ValidationError(
                {"non_field_errors": "Вы уже оставили отзыв на этот товар."}
            )
        return Review.objects.create(user=user, **validated_data)

    def update(self, instance: Review, validated_data: dict) -> Review:
        """Обновляет существующий отзыв новыми значениями полей.
        Обновляет поля отзыва (товар, рейтинг, текст), если они переданы в данных.
        Сохраняет изменения в базе данных и возвращает обновлённый объект."""

        instance.product = validated_data.get("product", instance.product)
        instance.rating = validated_data.get("rating", instance.rating)
        instance.text = validated_data.get("text", instance.text)
        instance.save()
        return instance

    def validate_rating(self, value: int) -> int:
        """Валидирует значение рейтинга.
        Проверяет, что переданное значение рейтинга находится в диапазоне от 1 до 5 включительно.
        Если значение вне диапазона — выбрасывается ошибка валидации."""

        if not 1 <= value <= 5:
            raise serializers.ValidationError("Рейтинг должен быть от 1 до 5.")
        return value
