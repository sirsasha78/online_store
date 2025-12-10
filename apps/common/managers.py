from django.db import models
from django.utils import timezone


class GetOrNoneQuerySet(models.QuerySet):
    """Расширение стандартного QuerySet Django, добавляющее метод для безопасного получения объекта."""

    def get_or_none(self, **kwargs):
        """Возвращает объект, соответствующий заданным параметрам, или None, если объект не найден."""
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class GetOrNoneManager(models.Manager):
    """Менеджер модели, расширяющий стандартный функционал Django-моделей
    методом `get_or_none`, позволяющим получать объект из базы данных
    или возвращать None, если объект не найден."""

    def get_queryset(self) -> GetOrNoneQuerySet:
        """Возвращает кастомный QuerySet, поддерживающий метод `get_or_none`."""

        return GetOrNoneQuerySet(self.model)

    def get_or_none(self, **kwargs):
        """Получает объект по заданным параметрам или возвращает None, если объект не найден."""
        return self.get_queryset().get_or_none(**kwargs)


class IsDeletedQuerySet(GetOrNoneQuerySet):
    """Расширение QuerySet для поддержки мягкого удаления объектов.

    Данный класс добавляет возможность мягкого удаления объектов моделей
    путём установки флага `is_deleted` и отметки времени удаления в поле `deleted_at`.
    При необходимости поддерживается также жёсткое удаление через вызов родительского метода.
    """

    def delete(self, hard_delete=False):
        """Выполняет мягкое или жёсткое удаление объектов в QuerySet."""

        if hard_delete:
            super().delete()
        else:
            return self.update(is_deleted=True, deleted_at=timezone.now())


class IsDeletedManager(GetOrNoneManager):
    """Менеджер для работы с объектами, у которых есть флаг `is_deleted`.

    Этот менеджер фильтрует объекты по умолчанию, исключая те, у которых установлен флаг `is_deleted=True`.
    Предоставляет методы для доступа ко всем объектам (включая удалённые) и для выполнения жёсткого удаления.
    """

    def get_queryset(self) -> IsDeletedQuerySet:
        """Возвращает набор запросов, фильтрующий объекты, у которых `is_deleted=False`."""

        return IsDeletedQuerySet(self.model).filter(is_deleted=False)

    def unfiltered(self) -> IsDeletedQuerySet:
        """Возвращает набор запросов без фильтрации по флагу `is_deleted`."""

        return IsDeletedQuerySet(self.model)

    def hard_delete(self):
        """Выполняет полное (жёсткое) удаление всех объектов в наборе, включая логически удалённые."""

        return self.unfiltered().delete(hard_delete=True)
