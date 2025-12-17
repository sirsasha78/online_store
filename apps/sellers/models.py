from django.db import models
from autoslug import AutoSlugField

from apps.accounts.models import User
from apps.common.models import BaseModel


class Seller(BaseModel):
    """Модель продавца на маркетплейсе.
    Описывает юридическое или физическое лицо, зарегистрированное как продавец.
    Связана с пользователем через отношение один к одному. Содержит реквизиты
    бизнеса, контактную информацию, банковские данные и статус модерации."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="seller",
        verbose_name="Пользователь",
    )
    business_name = models.CharField(max_length=255, verbose_name="Название компании")
    slug = AutoSlugField(
        populate_from="business_name", always_update=True, null=True, verbose_name="URL"
    )
    inn_identification_number = models.CharField(max_length=50, verbose_name="ИНН")
    website_url = models.URLField(null=True, verbose_name="Сайт")
    phone_number = models.CharField(max_length=20, verbose_name="Телефон")
    business_description = models.TextField(verbose_name="Описание бизнеса")
    business_address = models.CharField(max_length=255, verbose_name="Адрес бизнеса")
    city = models.CharField(max_length=100, verbose_name="Город")
    postal_code = models.CharField(max_length=20, verbose_name="Почтовый индекс")
    bank_name = models.CharField(max_length=255, verbose_name="Название банка")
    bank_bic_number = models.CharField(max_length=9)
    bank_account_number = models.CharField(
        max_length=50, verbose_name="Банковский счет"
    )
    bank_routing_number = models.CharField(max_length=50)
    is_approved = models.BooleanField(default=False, verbose_name="Проверен")

    def __str__(self) -> str:
        """Возвращает строковое представление объекта продавца."""

        return f"Продавец из {self.business_name}"
