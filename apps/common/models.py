import uuid
from django.db import models
from django.utils import timezone

from apps.common.managers import GetOrNoneManager, IsDeletedManager


class BaseModel(models.Model):
    """Абстрактная модель, предоставляющая базовые поля и функциональность для других моделей."""

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GetOrNoneManager()

    class Meta:
        """Метакласс, указывающий, что данная модель является абстрактной."""

        abstract = True


class IsDeletedModel(BaseModel):
    """Абстрактная модель, добавляющая функциональность мягкого удаления объектов.

    Вместо фактического удаления записи из базы данных помечает её как удалённую
    с помощью флага `is_deleted` и сохраняет время удаления в поле `deleted_at`.
    Это позволяет сохранять данные и при необходимости восстанавливать их."""

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = IsDeletedManager()

    class Meta:
        """Метакласс, указывающий, что данная модель является абстрактной."""

        ordering = ["id"]
        abstract = True

    def delete(self, *args, **kwargs):
        """Помечает объект как удалённый, устанавливая флаг `is_deleted` в True
        и сохраняя текущее время в поле `deleted_at`."""

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, *args, **kwargs):
        """Полностью удаляет объект из базы данных, обходя механизм мягкого удаления."""

        super().delete(*args, **kwargs)
