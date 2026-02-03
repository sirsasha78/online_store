from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.serializers import CreateUserSerializer, MyTokenObtainPairSerializer


class RegisterAPIView(APIView):
    """API-представление для регистрации нового пользователя.
    Обрабатывает POST-запросы с данными пользователя, валидирует их
    с помощью сериализатора и создаёт нового пользователя в системе
    при успешной валидации."""

    serializer_class = CreateUserSerializer
    throttle_scope = "register"

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Обрабатывает POST-запрос для регистрации нового пользователя."""

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "success"}, status=201)
        return Response(serializer.errors, status=400)


class MyTokenObtainPairView(TokenObtainPairView):
    """Представление для получения пары JWT-токенов (access и refresh).
    Это кастомное представление наследуется от `TokenObtainPairView` из библиотеки `rest_framework_simplejwt`.
    Оно использует собственный сериализатор `MyTokenObtainPairSerializer` для включения дополнительных данных
    пользователя в ответ (например, имя, роль, идентификатор), что позволяет избежать дополнительных запросов к API
    после аутентификации."""

    serializer_class = MyTokenObtainPairSerializer
