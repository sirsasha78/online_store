from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.request import Request

from apps.sellers.models import Seller
from apps.sellers.serializers import SellerSerializer
from apps.shop.models import Category, Product
from apps.shop.serializers import (
    ProductSerializer,
    CreateProductSerializer,
    OrderSerializer,
    CheckItemOrderSerializer,
)
from apps.common.utils import set_dict_attr
from apps.profiles.models import Order, OrderItem
from apps.common.permissions import IsSeller
from apps.common.paginations import CustomPagination
from core import settings


tags = ["Sellers"]


class SellersView(APIView):
    """Представление для создания или обновления профиля продавца.
    Данный эндпоинт позволяет аутентифицированному пользователю создать
    или обновить свой профиль продавца. При успешном создании или обновлении
    поле `account_type` пользователя автоматически устанавливается в значение 'SELLER'.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SellerSerializer

    @extend_schema(
        summary="Создание и обновление профиля продавца",
        description="Эндопоинт позволяющий создавать или обновлять профиль продавца",
        tags=tags,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
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

    permission_classes = [IsSeller]
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    @extend_schema(
        summary="Возвращает список продуктов продавца",
        description="Возвращает все товары от продавца. Товары могут быть отфильтрованы по названию, размеру или цвету.",
        tags=tags,
        parameters=[
            OpenApiParameter(
                name="page_size",
                description=f"Количество элементов на странице, которое вы хотите отобразить. По умолчанию используется {settings.REST_FRAMEWORK["PAGE_SIZE"]}",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
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

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(products, request)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Создание товара",
        description="Этот эндопоинт позволяет продавцу создавать продукт.",
        tags=tags,
        request=CreateProductSerializer,
        responses=ProductSerializer,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
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

    permission_classes = [IsSeller]
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
    def put(self, request: Request, *args, **kwargs) -> Response:
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
    def delete(self, request: Request, *args, **kwargs) -> Response:
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


class SellerOrdersView(APIView):
    """Представление для получения списка заказов, связанных с товарами продавца.
    Предоставляет API-эндпоинт, который возвращает все заказы,
    содержащие товары, принадлежащие текущему продавцу. Доступ разрешён только
    авторизованным пользователям с профилем продавца. Результаты отсортированы
    по дате создания заказа в порядке убывания (сначала новые).
    Заказы включаются в выборку, если хотя бы один из товаров в заказе
    принадлежит продавцу. Используется `distinct()`, чтобы избежать дублирования
    заказов при наличии нескольких товаров от одного продавца в одном заказе."""

    permission_classes = [IsSeller]
    serializer_class = OrderSerializer
    pagination_class = CustomPagination

    @extend_schema(
        summary="Выбор заказов продавца",
        description="Возвращает все заказы для конкретного продавца.",
        operation_id="seller_orders_view",
        tags=tags,
        parameters=[
            OpenApiParameter(
                name="page_size",
                description=f"Количество элементов на странице, которое вы хотите отобразить. По умолчанию используется {settings.REST_FRAMEWORK["PAGE_SIZE"]}",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения списка заказов продавца."""

        seller = request.user.seller
        orders = (
            Order.objects.filter(orderitems__product__seller=seller)
            .distinct()
            .order_by("-created_at")
        )

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(orders, request)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class SellerOrderItemsView(APIView):
    """Представление для получения товаров заказа, принадлежащих конкретному продавцу.
    Данный эндпоинт позволяет продавцу получить список позиций из указанного заказа,
    в которых участвуют товары, принадлежащие его магазину. Доступ разрешён только
    авторизованным пользователям с профилем продавца. Если заказ не существует
    или продавец не имеет к нему отношения, возвращается ошибка 404."""

    permission_classes = [IsSeller]
    serializer_class = CheckItemOrderSerializer
    pagination_class = CustomPagination

    @extend_schema(
        summary="Товары продавца",
        description="Возвращает все заказанные товары конкретного продавца.",
        operation_id="seller_order_items_view",
        tags=tags,
        parameters=[
            OpenApiParameter(
                name="page_size",
                description=f"Количество элементов на странице, которое вы хотите отобразить. По умолчанию используется {settings.REST_FRAMEWORK["PAGE_SIZE"]}",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения элементов заказа, связанных с продавцом."""

        seller = request.user.seller
        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order:
            return Response({"message": "Заказа не существует!"}, status=404)
        order_items = OrderItem.objects.filter(order=order, product__seller=seller)

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(order_items, request)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
