from django.db import models
from autoslug import AutoSlugField

from apps.common.models import BaseModel, IsDeletedModel
from apps.sellers.models import Seller
from apps.accounts.models import User


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
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Категория",
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


class Review(IsDeletedModel):
    """Модель отзыва пользователя на товар.
    Хранит информацию о рейтинге и текстовом отзыве, оставленном пользователем
    на конкретный товар. Поддерживает логическое удаление — при удалении запись
    помечается как удалённая (is_deleted=True), но не удаляется физически из базы данных.
    Каждый пользователь может оставить только один отзыв на один товар.
    Отзыв привязан к конкретному товару и автору (пользователю).
    Атрибуты:
        RATING_CHOICES (tuple): Кортеж допустимых значений рейтинга — от 1 до 5."""

    RATING_CHOICES = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5))

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Пользователь",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews", verbose_name="Товар"
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES, default=1, verbose_name="Рэйтинг"
    )
    text = models.TextField(blank=True, null=True, verbose_name="Текст отзыва")

    def __str__(self) -> str:
        """Возвращает строковое представление объекта отзыва."""

        return f"Отзыв от {self.user} на {self.product}"

    class Meta:
        """Метакласс модели Review."""

        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
