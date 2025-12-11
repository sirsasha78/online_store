from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.common.models import IsDeletedModel
from apps.accounts.managers import CustomUserManager


ACCOUNT_TYPE_CHOICES = (
    ("SELLER", "SELLER"),
    ("BUYER", "BUYER"),
)


class User(IsDeletedModel, AbstractUser):
    """Кастомная модель пользователя, расширяющая встроенную модель AbstractUser.
    Представляет пользователя системы с дополнительными полями, такими как имя,
    фамилия, электронная почта, аватар и тип аккаунта. Использует электронную
    почту в качестве уникального идентификатора для входа."""

    first_name = models.CharField(max_length=25, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=25, null=True, verbose_name="Фамилия")
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        default="avatars/default.jpg",
        verbose_name="Аватар",
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    account_type = models.CharField(
        max_length=6, choices=ACCOUNT_TYPE_CHOICES, default="BUYER"
    )

    USERNAME_FIELD = "email"
    """Поле, используемое для входа в систему — электронная почта."""

    REQUIRED_FIELDS = ["first_name", "last_name"]
    """Список полей, обязательных при создании пользователя через команду createsuperuser."""

    objects = CustomUserManager()

    @property
    def full_name(self) -> str:
        """Возвращает полное имя пользователя в формате "Имя Фамилия"."""

        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        """Возвращает строковое представление пользователя."""

        return self.full_name

    def has_perm(self, perm, obj=None) -> bool:
        """Проверяет, имеет ли пользователь указанное разрешение."""

        return True

    def has_module_perms(self, app_label) -> bool:
        """Проверяет, имеет ли пользователь права на доступ к приложению.
        Используется в админке Django для определения доступа к модулям."""

        return True

    @property
    def is_superuser(self) -> bool:
        """Определяет, является ли пользователь суперпользователем.
        В данной реализации суперпользователь — это тот, у кого is_staff = True."""

        return self.is_staff
