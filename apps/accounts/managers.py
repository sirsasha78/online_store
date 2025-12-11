from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер пользователей для модели пользователя с email в качестве уникального идентификатора.
    Этот менеджер переопределяет стандартные методы создания обычных пользователей
    и суперпользователей, обеспечивая валидацию электронной почты, имени и фамилии."""

    def email_validator(self, email: str):
        """Проверяет корректность электронной почты."""

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(
                "Вы должны указать действительный адрес электронной почты"
            )

    def validate_user(self, first_name: str, last_name: str, email: str, password: str):
        """Валидирует обязательные поля при создании пользователя.
        Проверяет наличие имени, фамилии, email и пароля. Нормализует email."""

        if not first_name:
            raise ValueError("Пользователи должны указать свое имя")

        if not last_name:
            raise ValueError("Пользователи должны указать свою фамилию")

        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError(
                "Базовая учетная запись пользователя: Требуется адрес электронной почты"
            )

        if not password:
            raise ValueError("У пользователя должен быть пароль")

    def create_user(self, first_name, last_name, email, password, **extra_fields):
        """Создает и сохраняет обычного пользователя с указанными данными."""

        self.validate_user(first_name, last_name, email, password)
        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def validate_superuser(self, **extra_fields):
        """Валидирует поля суперпользователя, устанавливая is_staff в True."""

        extra_fields.setdefault("is_staff", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("У суперпользователей должно быть значение is_staff=True")
        return extra_fields

    def create_superuser(self, first_name, last_name, email, password, **extra_fields):
        """Создает и сохраняет суперпользователя с указанными данными."""

        extra_fields = self.validate_superuser(**extra_fields)
        user = self.create_user(first_name, last_name, email, password, **extra_fields)
        return user
