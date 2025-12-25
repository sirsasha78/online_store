from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User


class CreateUserSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя.
    Предоставляет функционал для валидации и создания нового пользователя
    на основе предоставленных данных (email и пароль). Пароль устанавливается
    с использованием хеширования через метод `set_password`, обеспечивая
    безопасное хранение. Поле пароля помечено как write-only, чтобы оно не
    возвращалось в ответах API."""

    class Meta:
        """Метаданные сериализатора."""

        model = User
        fields = ("email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value: str) -> str:
        """Валидирует пароль с использованием встроенных валидаторов Django."""

        validate_password(value)
        return value

    def create(self, validated_data: dict) -> User:
        """Создаёт и сохраняет нового пользователя в базе данных.
        Использует предоставленные валидные данные для создания экземпляра
        пользователя. Пароль устанавливается с помощью метода set_password,
        который автоматически хеширует пароль перед сохранением."""

        user = User(email=validated_data["email"])
        user.set_password(validated_data["password"])
        user.save()
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для получения JWT-токена с дополнительными данными пользователя.
    Расширяет стандартный `TokenObtainPairSerializer` из `djangorestframework-simplejwt`,
    добавляя в токен информацию о группе и роли пользователя для использования на фронтенде
    и в бизнес-логике."""

    @classmethod
    def get_token(cls, user: User):
        """Создаёт и возвращает JWT-токен с дополнительными пользовательскими данными."""

        token = super().get_token(user)

        if user.is_staff:
            token["group"] = "admin"
        else:
            token["group"] = "user"
            token["role"] = user.account_type

        return token
