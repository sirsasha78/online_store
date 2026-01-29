from uuid import UUID
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema

from apps.common.utils import set_dict_attr
from apps.profiles.serializers import ProfileSerializer, ShippingAddressSerializer
from apps.profiles.models import ShippingAddress, Order, OrderItem
from apps.shop.serializers import OrderSerializer, CheckItemOrderSerializer
from apps.common.permissions import IsOwner


tags = ["Profiles"]


class ProfileView(APIView):
    """Представление для управления профилем пользователя.
    Позволяет просматривать, редактировать и деактивировать профиль
    аутентифицированного пользователя. Доступ к эндпоинтам разрешён
    только авторизованным пользователям (проверка осуществляется
    на уровне permission_classes, подразумевается её наличие)."""

    permission_classes = [IsOwner]
    serializer_class = ProfileSerializer

    @extend_schema(
        summary="Получить профиль",
        description="""Эта конечная точка позволяет пользователю получить доступ к своему профилю.""",
        tags=tags,
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Возвращает данные профиля текущего пользователя."""

        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=200)

    @extend_schema(
        summary="Обновить профиль",
        description="""Эта конечная точка позволяет пользователю обновить свой профиль.""",
        tags=tags,
        request={"multipart/form-data": serializer_class},
    )
    def put(self, request: Request, *args, **kwargs) -> Response:
        """Полностью обновляет данные профиля пользователя.
        Принимает данные из тела запроса, валидирует их с помощью
        ProfileSerializer, и при успешной валидации обновляет
        соответствующие поля пользователя. Использует вспомогательную
        функцию set_dict_attr для безопасного копирования значений."""

        user = request.user
        serilizer = self.serializer_class(data=request.data)
        serilizer.is_valid(raise_exception=True)
        user = set_dict_attr(user, serilizer.validated_data)
        user.save()
        serilizer = self.serializer_class(user)
        return Response(serilizer.data)

    @extend_schema(
        summary="Деактивировать учетную запись",
        description="""Эта конечная точка позволяет пользователю деактивировать свою учетную запись.""",
        tags=tags,
    )
    def delete(self, request: Request, *args, **kwargs) -> Response:
        """Деактивирует учётную запись текущего пользователя."""

        user = request.user
        user.is_active = False
        user.save()
        return Response({"message": "User Account Deactivated"})


class ShippingAddressesView(APIView):
    """Представление для управления адресами доставки пользователя.
    Предоставляет два основных действия:
    - Получение списка всех адресов доставки текущего пользователя.
    - Создание нового адреса доставки."""

    permission_classes = [IsOwner]
    serializer_class = ShippingAddressSerializer

    @extend_schema(
        summary="Выборка адресов доставки",
        description="""Эта конечная точка возвращает все адреса доставки, связанные с пользователем.""",
        tags=tags,
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Возвращает список всех адресов доставки, привязанных к текущему пользователю."""

        user = request.user
        shipping_addresses = ShippingAddress.objects.filter(user=user)
        serializer = self.serializer_class(shipping_addresses, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Создайте адрес доставки",
        description="""Эта конечная точка позволяет пользователю создать адрес доставки.""",
        tags=tags,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """Создаёт новый адрес доставки для текущего пользователя."""

        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address, _ = ShippingAddress.objects.get_or_create(user=user, **data)
        serializer = self.serializer_class(shipping_address)
        return Response(serializer.data, status=201)


class ShippingAddressViewID(APIView):
    """Представление для управления конкретным адресом доставки пользователя по его UUID.
    Предоставляет операции чтения, обновления и удаления (GET, PUT, DELETE)
    для адреса доставки, связанного с аутентифицированным пользователем.
    Доступ к адресу возможен только по его уникальному идентификатору (UUID)."""

    permission_classes = [IsOwner]
    serializer_class = ShippingAddressSerializer

    def get_object(self, user, shipping_id):
        """Получает объект адреса доставки по UUID и пользователю.
        Проверяет, что переданный идентификатор имеет корректный формат UUID.
        Затем ищет адрес доставки, связанный с указанным пользователем и идентификатором.
        Если адрес не найден или идентификатор неверен, вызывает соответствующее исключение.
        """

        try:
            shipping_uuid = UUID(shipping_id)
        except ValueError as e:
            raise ValidationError(
                {"message": "Неверный формат идентификатора доставки UUID"}
            ) from e
        shipping_address = ShippingAddress.objects.get_or_none(
            user=user, id=shipping_uuid
        )
        if shipping_address is None:
            raise NotFound({"message": "Адреса доставки не существует!"}, code=404)
        self.check_object_permissions(self.request, shipping_address)

        return shipping_address

    @extend_schema(
        summary="Идентификатор адреса доставки",
        description="""Эта конечная точка возвращает один адрес доставки, связанный с пользователем.""",
        tags=tags,
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения данных одного адреса доставки."""

        user = request.user
        shipping_address = self.get_object(user, kwargs["id"])
        serializer = self.serializer_class(shipping_address)
        return Response(serializer.data)

    @extend_schema(
        summary="Обновить адрес доставки",
        description="""Эта конечная точка позволяет пользователю обновить свой адрес доставки.""",
        tags=tags,
    )
    def put(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает PUT-запрос для полного обновления адреса доставки."""

        user = request.user
        shipping_address = self.get_object(user, kwargs["id"])
        serializer = self.serializer_class(request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address = set_dict_attr(shipping_address, data)
        shipping_address.save()
        serialiser = self.serializer_class(shipping_address)
        return Response(serialiser.data, status=200)

    @extend_schema(
        summary="Удалить адрес доставки",
        description="""Эта конечная точка позволяет пользователю удалить свой адрес доставки.""",
        tags=tags,
    )
    def delete(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает DELETE-запрос для удаления адреса доставки."""

        user = request.user
        shipping_address = self.get_object(user, kwargs["id"])
        shipping_address.delete()
        return Response({"message": "Адрес доставки успешно удален"}, status=200)


class OrdersView(APIView):
    """Представление для получения списка заказов пользователя.
    Предоставляет API-эндпоинт, который возвращает все заказы,
    оформленные текущим аутентифицированным пользователем.
    Результат отсортирован по дате создания в порядке убывания
    (сначала самые новые заказы).
    Поддерживает оптимизированный запрос к базе данных:
    - Подгружает связанный объект пользователя (select_related).
    - Предварительно загружает позиции заказов и связанные с ними товары (prefetch_related).
    """

    permission_classes = [IsOwner]
    serializer_class = OrderSerializer

    @extend_schema(
        summary="Получение заказов",
        description="Возвращает все заказы для конкретного пользователя.",
        operation_id="orders_view",
        tags=tags,
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает HTTP GET-запрос для получения списка всех заказов пользователя."""

        user = request.user
        orders = (
            Order.objects.filter(user=user)
            .select_related("user")
            .prefetch_related("orderitems", "orderitems__product")
            .order_by("-created_at")
        )
        serializer = self.serializer_class(orders, many=True)
        return Response(serializer.data, status=200)


class OrderItemsView(APIView):
    """Представление для получения списка товаров, входящих в состав конкретного заказа.
    Обрабатывает GET-запрос и возвращает все элементы заказа (товары с количеством),
    связанные с указанным заказом. Доступ разрешён только авторизованному пользователю,
    которому принадлежит заказ. Используется для отображения содержимого заказа
    после его оформления или при отслеживании статуса."""

    permission_classes = [IsOwner]
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        summary="Товары внутри заказа",
        description="Возвращает список элементов конкретного заказа",
        operation_id="order_items_view",
        tags=tags,
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает GET-запрос для получения всех товаров, входящих в заказ."""

        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order or order.user != request.user:
            return Response({"message": "Заказа не существует!"}, status=404)
        order_items = OrderItem.objects.filter(order=order).select_related(
            "product", "product__seller", "product__seller__user"
        )
        serializer = self.serializer_class(order_items, many=True)
        return Response(serializer.data, status=200)
