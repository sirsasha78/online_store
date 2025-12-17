from django.db import models
from autoslug import AutoSlugField

from apps.common.models import BaseModel, IsDeletedModel
from apps.sellers.models import Seller


class Category(BaseModel):
    """Модель категории для классификации товаров на маркетплейсе."""

    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = AutoSlugField(
        populate_from="name", unique=True, always_update=True, verbose_name="URL"
    )
    image = models.ImageField(upload_to="category_images/", verbose_name="Фото")

    def __str__(self) -> str:
        """Возвращает строковое представление категории."""

        return self.name

    class Meta:
        """Мета-класс для настройки поведения модели."""

        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Product(IsDeletedModel):
    """Модель товара для платформы-маркетплейса.
    Описывает продукт, выставленный на продажу продавцом. Включает в себя
    основную информацию: название, описание, цены, количество на складе,
    изображения и связь с продавцом. Поддерживает мягкое удаление — товар
    можно скрыть без потери данных."""

    seller = models.ForeignKey(
        Seller,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
        verbose_name="Продавец",
    )
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = AutoSlugField(
        populate_from="name", unique=True, db_index=True, verbose_name="URL"
    )
    description = models.TextField(verbose_name="Описание")
    price_old = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, verbose_name="Старая цена"
    )
    price_current = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Текущая цена"
    )
    in_stock = models.IntegerField(default=5, verbose_name="Количество товара")
    image1 = models.ImageField(
        upload_to="product_images/", verbose_name="Первое изображение"
    )
    image2 = models.ImageField(
        upload_to="product_images/", blank=True, verbose_name="Второе изображение"
    )
    image3 = models.ImageField(
        upload_to="product_images/", blank=True, verbose_name="Третье изображение"
    )

    def __str__(self) -> str:
        """Возвращает строковое представление товара."""

        return self.name

    class Meta:
        """Мета-класс для настройки поведения модели."""

        verbose_name = "Товар"
        verbose_name_plural = "Товары"
