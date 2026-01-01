from django.http import HttpRequest
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shop.models import Category, Product
from apps.shop.serializers import CategorySerializer, ProductSerializer
from apps.sellers.models import Seller


tags = ["Shop"]


class CategoriesView(APIView):
    """Представление для управления категориями.
    Предоставляет эндпоинты для:
    - Получения списка всех категорий.
    - Создания новой категории."""

    serializer_class = CategorySerializer

    @extend_schema(
        summary="Выбор категорий",
        description="Этот эндопоинт возвращает все категории",
        tags=tags,
    )
    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения списка всех категорий."""

        categories = Category.objects.all()
        serializer = self.serializer_class(categories, many=True)
        return Response(serializer.data, status=200)

    @extend_schema(
        summary="Создание категории",
        description="Эндопоинт для создание категорий",
        tags=tags,
    )
    def post(self, request: HttpRequest, *args, **kwargs) -> Response:
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

    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="category_products",
        summary="Выбор товаров по категориям",
        description="Этот эндопоинт возвращает все продукты в определенной категории.",
        tags=tags,
    )
    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения товаров по категории."""

        category = Category.objects.get_or_none(slug=kwargs["slug"])
        if not category:
            return Response({"message": "Категория не существует!"}, status=404)

        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(category=category)
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=200)


class ProductsView(APIView):
    """Представление для отображения списка всех продуктов.
    Обрабатывает GET-запросы и возвращает список всех доступных товаров
    с информацией о категории, продавце и связанных данных.
    Использует оптимизированный запрос к базе данных с `select_related`
    для уменьшения количества запросов."""

    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="all_products",
        summary="Все товары",
        description="Этот эндопоинт возвращает все продукты.",
        tags=tags,
    )
    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения списка всех продуктов."""

        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).all()
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=200)


class ProductsBySellerView(APIView):
    """Представление для получения списка товаров определённого продавца по его slug.
    Этот эндпоинт позволяет получить все товары, связанные с продавцом,
    идентифицируемым по уникальному слагу (slug). Возвращаемые данные включают
    информацию о товарах с предзагрузкой связанных объектов: категория, продавец,
    а также пользователь, связанный с продавцом."""

    serializer_class = ProductSerializer

    @extend_schema(
        summary="Товары продавца",
        description="Этот эндопоинт возвращает все товары у определенного продавца.",
        tags=tags,
    )
    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения всех товаров продавца."""

        seller = Seller.objects.get_or_none(slug=kwargs["slug"])
        if not seller:
            return Response({"message": "Продавца не существует!"}, status=404)

        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=200)


class ProductView(APIView):
    """Представление для отображения информации о продукте.
    Предоставляет эндпоинт для получения детальных сведений о продукте
    по его уникальному идентификатору в виде slug.
    Доступен для всех пользователей (включая неаутентифицированных)."""

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
    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения детальной информации о продукте."""

        product = self.get_object(kwargs["slug"])
        if not product:
            return Response({"message": "Продукта не существует!"}, status=404)

        serializer = self.serializer_class(product)
        return Response(serializer.data, status=200)
