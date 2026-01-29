from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.request import Request


from apps.shop.models import Category, Product, Review
from apps.shop.serializers import (
    CategorySerializer,
    ProductSerializer,
    OrderItemSerializer,
    ToggleCartItemSerializer,
    CheckoutSerializer,
    OrderSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)
from apps.sellers.models import Seller
from apps.profiles.models import OrderItem, ShippingAddress, Order
from apps.common.permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from apps.shop.filters import ProductFilter
from apps.shop.schema_examples import PRODUCT_PARAM_EXAMPLE
from apps.common.paginations import CustomPagination
from core import settings


tags = ["Shop"]


class CategoriesView(APIView):
    """Представление для управления категориями.
    Предоставляет эндпоинты для:
    - Получения списка всех категорий.
    - Создания новой категории."""

    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategorySerializer
    pagination_class = CustomPagination

    @extend_schema(
        summary="Выбор категорий",
        description="Этот эндопоинт возвращает все категории",
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
        """Обрабатывает GET-запрос для получения списка всех категорий."""

        categories = Category.objects.all()

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(categories, request)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Создание категории",
        description="Эндопоинт для создание категорий",
        tags=tags,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает POST-запрос для создания новой категории.
        Принимает данные от клиента, валидирует их через CategorySerializer.
        При успешной валидации создаёт новую категорию в базе данных."""

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_cat = Category.objects.create(**serializer.validated_data)
            serializer = self.serializer_class(new_cat)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class ProductsByCategoryView(APIView):
    """Представление для получения списка товаров по slug категории.
    Обрабатывает GET-запросы и возвращает все продукты,
    относящиеся к категории с указанным slug.
    В случае, если категория не найдена, возвращается ошибка 404."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    @extend_schema(
        operation_id="category_products",
        summary="Выбор товаров по категориям",
        description="Этот эндопоинт возвращает все продукты в определенной категории.",
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
        """Обрабатывает GET-запрос для получения товаров по категории."""

        category = Category.objects.get_or_none(slug=kwargs["slug"])
        if not category:
            return Response({"message": "Категория не существует!"}, status=404)

        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(category=category)

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(products, request)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProductsView(APIView):
    """Представление для отображения списка всех продуктов с возможностью фильтрации и пагинации.
    Данный эндпоинт предоставляет доступ к списку продуктов с поддержкой:
    - Фильтрации по различным параметрам (например, по цене),
    - Пагинации результатов,
    - Оптимизированных запросов к базе данных с использованием select_related.
    Доступ к этому представлению разрешён всем пользователям, включая неаутентифицированных.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    @extend_schema(
        operation_id="all_products",
        summary="Все товары",
        description="Этот эндопоинт возвращает все продукты.",
        tags=tags,
        parameters=PRODUCT_PARAM_EXAMPLE,
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает HTTP GET-запрос для получения списка продуктов с фильтрацией."""

        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).all()
        filterset = ProductFilter(request.query_params, queryset=products)
        if filterset.is_valid():
            queryset = filterset.qs
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = self.serializer_class(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response(filterset.errors, status=400)


class ProductsBySellerView(APIView):
    """Представление для получения списка товаров определённого продавца по его slug.
    Этот эндпоинт позволяет получить все товары, связанные с продавцом,
    идентифицируемым по уникальному слагу (slug). Возвращаемые данные включают
    информацию о товарах с предзагрузкой связанных объектов: категория, продавец,
    а также пользователь, связанный с продавцом."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    @extend_schema(
        summary="Товары продавца",
        description="Этот эндопоинт возвращает все товары у определенного продавца.",
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
        """Обрабатывает GET-запрос для получения всех товаров продавца."""

        seller = Seller.objects.get_or_none(slug=kwargs["slug"])
        if not seller:
            return Response({"message": "Продавца не существует!"}, status=404)

        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(seller=seller)

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(products, request)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProductView(APIView):
    """Представление для отображения информации о продукте.
    Предоставляет эндпоинт для получения детальных сведений о продукте
    по его уникальному идентификатору в виде slug.
    Доступен для всех пользователей (включая неаутентифицированных)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer

    def get_object(self, slug: str) -> Product | None:
        """Возвращает объект продукта по заданному slug."""

        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="product_detail",
        summary="Информация о товаре",
        description="Этот эндопоинт возвращает сведения о продукте с помощью slug.",
        tags=tags,
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения детальной информации о продукте."""

        product = self.get_object(kwargs["slug"])
        if not product:
            return Response({"message": "Продукта не существует!"}, status=404)

        serializer = self.serializer_class(product)
        return Response(serializer.data, status=200)


class CartView(APIView):
    """Представление для управления корзиной пользователя.
    Позволяет:
    - Получать список всех товаров, добавленных в корзину (не привязанных к заказу).
    - Добавлять, обновлять или удалять товары в корзине с помощью POST-запроса.
    Аутентифицированные пользователи работают с привязанной к ним корзиной.
    Товары в корзине определяются как объекты `OrderItem`, у которых поле `order` равно `None`.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderItemSerializer
    pagination_class = CustomPagination

    @extend_schema(
        summary="Вывод товаров из корзины",
        description="Возвращает все товары из корзины пользователя.",
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
        """Обрабатывает GET-запрос для получения всех товаров из корзины текущего пользователя.
        Выполняет выборку объектов `OrderItem`, связанных с текущим пользователем и не привязанных к заказу.
        Использует `select_related` для оптимизации запросов к связанным объектам: продукт, продавец, пользователь продавца.
        """

        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None).select_related(
            "product", "product__seller", "product__seller__user"
        )

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(orderitems, request)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Переместить товар в корзину",
        description="Позволяет пользователю или гостю добавлять/обновлять/удалять товар из корзины. Если количество равно 0, товар удаляется из корзины.",
        request=ToggleCartItemSerializer,
        tags=tags,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает POST-запрос для добавления, обновления или удаления товара в корзине.
        Принимает слаг продукта и количество. На основе этих данных:
        - Если товара ещё нет — создаётся новый `OrderItem`.
        - Если есть — обновляется количество.
        - Если количество равно 0 — товар удаляется из корзины."""

        user = request.user
        serializer = ToggleCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quantity = data["quantity"]

        product = Product.objects.select_related("seller", "seller__user").get_or_none(
            slug=data["slug"]
        )
        if not product:
            return Response({"message": "Продукта с таким слагом нет!"}, status=404)
        orderitem, created = OrderItem.objects.update_or_create(
            user=user, order=None, product=product, defaults={"quantity": quantity}
        )
        resp_message_substring = "Обновлен"
        status_code = 200

        if created:
            status_code = 201
            resp_message_substring = "Добавлен"
        if orderitem.quantity == 0:
            resp_message_substring = "Удален"
            orderitem.delete()
            data = None
        if resp_message_substring != "Удален":
            serializer = self.serializer_class(orderitem)
            data = serializer.data
        return Response(
            data={"message": f"Товар {resp_message_substring}", "товар": data},
            status=status_code,
        )


class CheckoutView(APIView):
    """Представление для оформления заказа из корзины пользователя.
    Позволяет аутентифицированному пользователю создать заказ на основе товаров,
    находящихся в его корзине (объекты `OrderItem` с `order=None`). При успешном
    оформлении заказа все элементы корзины связываются с новым заказом, а данные
    доставки копируются из выбранного адреса."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CheckoutSerializer

    @extend_schema(
        summary="Проверка",
        description="Позволяет пользователю создать заказ, с помощью которого затем можно произвести оплату.",
        request=CheckoutSerializer,
        tags=tags,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает POST-запрос для создания заказа из корзины пользователя."""

        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None)
        if not orderitems.exists():
            return Response({"message": "В корзине нет товаров"}, status=404)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_id = data.get("shipping_id")
        shipping = ShippingAddress.objects.get_or_none(id=shipping_id)
        if not shipping:
            return Response(
                {"message": "Нет адреса доставки с таким идентификатором"}, status=404
            )

        fields_to_update = (
            "full_name",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "zipcode",
        )
        data = {}
        for field in fields_to_update:
            value = getattr(shipping, field)
            data[field] = value

        order = Order.objects.create(user=user, **data)
        orderitems.update(order=order)
        serializer = OrderSerializer(order)
        return Response(
            data={
                "message": "Оформление заказа прошло успешно",
                "заказ": serializer.data,
            },
            status=201,
        )


class ProductReviewsView(APIView):
    """Представление для получения пагинированного списка отзывов на товар по его slug.
    Данный класс обрабатывает GET-запросы для отображения всех активных отзывов,
    связанных с определённым товаром. Поддерживает пагинацию результатов,
    что позволяет эффективно отображать большое количество отзывов без перегрузки сервера.
    Атрибуты:
        serializer_class (type): Класс сериализатора, используемый для преобразования
            объектов отзывов в JSON-формат.
        permission_classes (list): Список классов разрешений. Доступ к представлению
            разрешён всем пользователям, включая неаутентифицированных.
        pagination_class (type): Класс пагинации, используемый для разбиения списка
            отзывов на страницы. Позволяет клиенту управлять количеством элементов
            на странице через параметр `page_size`."""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination

    @extend_schema(
        summary="Получение отзывов",
        description="Этот эндопоинт возвращает все отзывы",
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
        """Обрабатывает GET-запрос для получения всех отзывов на товар.
        Получает товар по значению `slug` из URL-параметров. Если товар не найден,
        возвращает сообщение об ошибке. В противном случае возвращает список
        всех отзывов, связанных с этим товаром."""

        product = Product.objects.get_or_none(slug=kwargs["slug"])
        if not product:
            return Response({"message": "Товар не существует"}, status=404)

        reviews = Review.objects.filter(product=product, is_deleted=False)
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(reviews, request)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class ReviewCreateView(APIView):
    """Представление для создания нового отзыва на товар.
    Обрабатывает POST-запросы на создание отзыва с проверкой прав доступа
    и валидацией данных. Использует указанный сериализатор для преобразования
    входных данных и сохранения отзыва в базу данных. Поддерживает автоматическую
    документацию через drf-spectacular.
    Атрибуты:
        serializer_class (type): Класс сериализатора, используемый для валидации
                                 и десериализации входных данных при создании отзыва."""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Создание отзыва",
        description="Эндопоинт для создание отзывов",
        tags=tags,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает POST-запрос для создания нового отзыва на товар.
        Выполняет валидацию входных данных с помощью сериализатора.
        Если данные валидны, создаёт новый отзыв и возвращает его данные.
        В случае ошибки валидации возвращает детали ошибок."""

        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class ReviewDetailView(APIView):
    """Представление для детального взаимодействия с отзывом.
    Поддерживает операции получения, полного обновления и удаления отзыва.
    Доступ к изменению и удалению имеет только владелец отзыва или персонал (is_staff).
    При удалении используется мягкое удаление — запись помечается как удалённая,
    но остаётся в базе данных.
    Атрибуты:
        serializer_class (ReviewSerializer): Сериализатор для преобразования данных отзыва.
        permission_classes (list): Список классов разрешений. Доступ разрешён только владельцу
                                   или персоналу для операций записи."""

    serializer_class = ReviewUpdateSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_object(self, pk: str) -> Review | None:
        """Возвращает объект отзыва по его идентификатору.
        Метод использует `get_or_none` для безопасного получения объекта без выброса исключения.
        Если объект не найден, возвращается None."""

        review = Review.objects.get_or_none(id=pk, is_deleted=False)
        self.check_object_permissions(self.request, review)
        return review

    @extend_schema(
        summary="Получение отзыва",
        description="Возвращает данные одного отзыва.",
        tags=tags,
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения данных конкретного отзыва.
        Если отзыв с указанным ID не найден, возвращается ошибка 404.
        В случае успеха — данные отзыва сериализуются и возвращаются с кодом 200."""

        review = self.get_object(kwargs["pk"])
        if not review:
            return Response({"message": "Отзыв не найден"}, status=404)
        serializer = self.serializer_class(review)
        return Response(serializer.data, status=200)

    @extend_schema(
        summary="Изменение отзыва",
        description="Позволяет владельцу изменить текст или рейтинг отзыва.",
        tags=tags,
    )
    def put(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает PUT-запрос для полного обновления отзыва.
        Проверяет права доступа через `permission_classes`. Если данные валидны,
        отзыв обновляется. При отсутствии отзыва или невалидных данных возвращается
        соответствующий статус-код."""

        review = self.get_object(kwargs["pk"])
        if not review:
            return Response({"message": "Отзыв не найден"}, status=404)

        serializer = self.serializer_class(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @extend_schema(
        summary="Удаление отзыва",
        description="Помечает отзыв как удалённый (мягкое удаление).",
        tags=tags,
    )
    def delete(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает DELETE-запрос для удаления отзыва.
        Реализует мягкое удаление: объект не удаляется физически, а помечается
        как удалённый через метод `delete()` модели. После успешного удаления
        возвращается сообщение и статус 202."""

        review = self.get_object(kwargs["pk"])
        if not review:
            return Response({"message": "Отзыв не найден"}, status=404)

        review.delete()
        return Response({"message": "Отзыв успешно удален"}, status=204)
