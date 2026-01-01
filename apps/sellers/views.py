from django.http import HttpRequest
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sellers.models import Seller
from apps.sellers.serializers import SellerSerializer
from apps.shop.models import Category, Product
from apps.shop.serializers import ProductSerializer, CreateProductSerializer
from apps.common.utils import set_dict_attr


tags = ["Sellers"]


class SellersView(APIView):
    """Представление для создания или обновления профиля продавца.
    Данный эндпоинт позволяет аутентифицированному пользователю создать
    или обновить свой профиль продавца. При успешном создании или обновлении
    поле `account_type` пользователя автоматически устанавливается в значение 'SELLER'.
    """

    serializer_class = SellerSerializer

    @extend_schema(
        summary="Создание и обновление профиля продавца",
        description="Эндопоинт позволяющий создавать или обновлять профиль продавца",
        tags=tags,
    )
    def post(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает POST-запрос для создания или обновления профиля продавца."""

        user = request.user
        serializer = self.serializer_class(data=request.data, partial=False)
        if serializer.is_valid():
            data = serializer.validated_data
            seller, _ = Seller.objects.update_or_create(user=user, defaults=data)
            user.account_type = "SELLER"
            user.save()
            serializer = self.serializer_class(seller)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class SellerProductsView(APIView):
    """Представление для отображения и создания товаров продавца.
    Доступ к эндпоинтам разрешён только подтвержденным продавцам
    (пользователям с ролью продавца и статусом is_approved=True)."""

    serializer_class = ProductSerializer

    @extend_schema(
        summary="Возвращает список продуктов продавца",
        description="Возвращает все товары от продавца. Товары могут быть отфильтрованы по названию, размеру или цвету.",
        tags=tags,
    )
    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения списка товаров продавца.
        Проверяет, является ли текущий пользователь подтверждённым продавцом.
        Если нет — возвращает статус 403.
        Если да — возвращает все товары продавца с предзагрузкой связанных объектов
        (категория, продавец, пользователь) для оптимизации запросов."""

        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response({"message": "Доступ запрещен"}, status=403)

        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=200)

    @extend_schema(
        summary="Создание товара",
        description="Этот эндопоинт позволяет продавцу создавать продукт.",
        tags=tags,
        request=CreateProductSerializer,
        responses=ProductSerializer,
    )
    def post(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает POST-запрос для создания нового товара продавцом.
        Проверяет:
        - Является ли пользователь подтверждённым продавцом.
        - Валидны ли входные данные.
        - Существует ли указанная категория (по slug).
        При успешной проверке создаёт товар, связывая его с продавцом и категорией.
        Возвращает сериализованные данные созданного товара."""

        serializer = CreateProductSerializer(data=request.data)
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response({"message": "Доступ запрещен"}, status=403)

        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response({"message": "Категория не существует!"}, status=404)

            data["category"] = category
            data["seller"] = seller
            new_prod = Product.objects.create(**data)
            serializer = ProductSerializer(new_prod)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class SellerProductView(APIView):
    """Представление для обновления и удаления продукта продавцом.
    Доступ к эндпоинтам разрешён только проверенным продавцам
    (пользователям с подтверждённым статусом продавца).
    Операции выполняются по уникальному идентификатору продукта — slug."""

    serializer_class = CreateProductSerializer

    def get_object(self, slug: str):
        """Возвращает объект продукта по его slug или None, если продукт не найден."""

        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        summary="Обновление продукта продавца",
        description="Этот эндпоинт позволяет продавцу обновит свой продукт.",
        tags=tags,
    )
    def put(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает PUT-запрос для полного обновления продукта.
        При изменении цены, предыдущее значение сохраняется в `price_old`."""

        product = self.get_object(kwargs["slug"])
        if not product:
            return Response({"message": "Продукт не существует!"}, status=404)

        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response({"message": "Доступ запрещен"}, status=403)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response({"message": "Категория не существует!"}, status=404)

            data["category"] = category
            if data["price_current"] != product.price_current:
                data["price_old"] = product.price_current
            product = set_dict_attr(product, data)
            product.save()
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)

    @extend_schema(
        summary="Удаление продукта продавца",
        description="Этот эндпоинт позволяет продавцу удалить свой продукт.",
        tags=tags,
    )
    def delete(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает DELETE-запрос для удаления продукта.
        Проверяет:
        - Существование продукта по slug.
        - Является ли текущий пользователь проверенным продавцом.
        Продукт удаляется физически из базы данных."""

        product = self.get_object(kwargs["slug"])
        if not product:
            return Response({"message": "Продукт не существует!"}, status=404)

        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response({"message": "Доступ запрещен"})

        product.delete()
        return Response({"message": "Товар успешно удален"}, status=202)
