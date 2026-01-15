from decimal import Decimal
from django.db import models

from apps.accounts.models import User
from apps.common.models import BaseModel
from apps.shop.models import Product
from apps.common.utils import generate_unique_code


DELIVERY_STATUS_CHOICES = (
    ("PENDING", "Рассматриваемый"),
    ("PACKING", "Упаковка"),
    ("SHIPPING", "Доставка"),
    ("ARRIVING", "Прибывающий"),
    ("SUCCESS", "Успешно"),
)

PAYMENT_STATUS_CHOICES = (
    ("PENDING", "Рассматриваемый"),
    ("PROCESSING", "Обработка"),
    ("SUCCESSFUL", "Успешно"),
    ("CANCELLED", "Отмененный"),
    ("FAILED", "Провал"),
)


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


class Order(BaseModel):
    """Модель заказа для обработки покупок на платформе.
    Хранит информацию о заказе, включая данные пользователя, статусы доставки и оплаты,
    контактные данные для доставки, а также уникальный идентификатор транзакции.
    Используется в сценариях, где требуется формализованная обработка заказа с оплатой
    и доставкой через платформу."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь",
    )
    tx_ref = models.CharField(
        max_length=100, blank=True, unique=True, verbose_name="Идентификатор транзакции"
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default="PENDING",
        verbose_name="Статус доставки",
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="PENDING",
        verbose_name="Статус платежа",
    )
    date_delivered = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата доставки"
    )
    full_name = models.CharField(max_length=1000, null=True, verbose_name="Полное имя")
    email = models.EmailField(null=True, verbose_name="Электронная почта")
    phone = models.CharField(max_length=20, null=True, verbose_name="Телефон")
    address = models.CharField(max_length=1000, null=True, verbose_name="Адрес")
    city = models.CharField(max_length=200, null=True, verbose_name="Город")
    country = models.CharField(max_length=100, null=True, verbose_name="Страна")
    zipcode = models.CharField(max_length=6, null=True, verbose_name="Почтовый индекс")

    def __str__(self) -> str:
        """Возвращает строковое представление объекта заказа."""

        return self.user.full_name

    def save(self, *args, **kwargs):
        """Переопределённый метод сохранения объекта заказа.
        Перед сохранением проверяет, является ли объект новым (по отсутствию `created_at`).
        Если да — генерирует уникальный идентификатор транзакции `tx_ref` с помощью
        функции `generate_unique_code`."""

        if not self.created_at:
            self.tx_ref = generate_unique_code(Order, "tx_ref")
        super().save(*args, **kwargs)

    @property
    def get_cart_subtotal(self) -> Decimal:
        """Вычисляет общую стоимость всех позиций в заказе.
        Суммирует итоговые стоимости всех объектов OrderItem, связанных с этим заказом
        через обратную связь 'orderitems'."""

        orderitems = self.orderitems.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_total(self) -> Decimal:
        """Возвращает итоговую стоимость заказа.
        На текущий момент совпадает с подытогом (get_cart_subtotal), но метод
        может быть расширен в будущем для включения стоимости доставки, налогов
        или скидок."""

        total = self.get_cart_subtotal
        return total


class OrderItem(BaseModel):
    """Модель позиции в заказе.
    Хранит информацию о товаре, количестве и связанном заказе.
    Используется для формирования состава заказа и расчёта итоговых сумм.
    Поддерживает связь с пользователем (для корзины до оформления заказа)
    и с конкретным заказом (после оформления)."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="orderitems",
        verbose_name="Заказ",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    @property
    def get_total(self) -> Decimal:
        """Возвращает общую стоимость позиции в заказе."""

        return self.product.price_current * self.quantity

    def __str__(self) -> str:
        """Возвращает строковое представление объекта."""

        return self.product.name

    class Meta:
        """Метакласс для настройки модели OrderItem."""

        ordering = ["-created_at"]
