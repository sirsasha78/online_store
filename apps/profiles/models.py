from django.db import models

from apps.accounts.models import User
from apps.common.models import BaseModel


class ShippingAddress(BaseModel):
    """Модель адреса доставки для пользователя.
    Представляет собой адрес, связанный с пользователем, который используется
    для доставки заказов. Содержит контактную и географическую информацию."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shipping_addresses"
    )
    full_name = models.CharField(max_length=255, verbose_name="Полное имя")
    email = models.EmailField(verbose_name="Электронная почта")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.CharField(max_length=1000, verbose_name="Адрес")
    city = models.CharField(max_length=100, verbose_name="Город")
    country = models.CharField(max_length=200, verbose_name="Страна")
    zipcode = models.CharField(max_length=6, verbose_name="Почтовый индекс")

    def __str__(self) -> str:
        """Возвращает строковое представление объекта."""

        return f"Детали доставки для {self.full_name}"
