from django.http import HttpRequest
from rest_framework import permissions
from rest_framework.views import View

from typing import Any


class IsOwner(permissions.BasePermission):
    """Пользовательское разрешение, разрешающее доступ только владельцам объекта или персоналу.
    Проверяет:
    - Аутентификацию пользователя на уровне запроса (has_permission).
    - Принадлежность объекта пользователю или наличие прав персонала на уровне объекта (has_object_permission).
    Используется для ограничения доступа к объектам таким образом, чтобы:
    - Только аутентифицированные пользователи могли выполнять запросы.
    - Пользователь мог взаимодействовать только со своими объектами.
    - Администраторы (staff) имели полный доступ к любым объектам."""

    def has_permission(self, request: HttpRequest, view: View) -> bool:
        """Проверяет, имеет ли пользователь право на выполнение запроса."""

        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request: HttpRequest, view: View, obj: Any) -> bool:
        """Проверяет, имеет ли пользователь право на взаимодействие с конкретным объектом.
        Метод вызывается при попытке доступа к конкретному объекту (например, при редактировании или удалении).
        """
        return obj.user == request.user or request.user.is_staff


class IsSeller(permissions.BasePermission):
    """Пользовательское разрешение, разрешающее доступ только подтверждённым продавцам или персоналу.
    Проверяет права доступа на двух уровнях:
    - На уровне запроса (has_permission): пользователь должен быть аутентифицирован, иметь тип аккаунта "SELLER"
      и подтверждённый профиль продавца, либо быть сотрудником (staff).
    - На уровне объекта (has_object_permission): пользователь может взаимодействовать только с объектами,
      принадлежащими его профилю продавца, либо быть сотрудником (staff)."""

    def has_permission(self, request: HttpRequest, view: View) -> bool:
        """Проверяет, имеет ли пользователь право на выполнение запроса."""

        if (
            request.user.is_authenticated
            and request.user.account_type == "SELLER"
            and request.user.seller.is_approved
        ) or request.user.is_staff:
            return True
        return False

    def has_object_permission(self, request: HttpRequest, view: View, obj: Any) -> bool:
        """Проверяет, имеет ли пользователь право на взаимодействие с конкретным объектом."""

        return obj.seller == request.user.seller or request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """Пользовательское разрешение, позволяющее доступ на чтение всем,
    но на запись — только администраторам.
    Разрешает выполнение безопасных HTTP-методов (GET, HEAD, OPTIONS)
    любым пользователям (включая неаутентифицированных).
    Для небезопасных методов (POST, PUT, PATCH, DELETE) требует,
    чтобы пользователь был аутентифицирован и являлся администратором (staff).
    Применяется для представлений, где данные должны быть защищены
    от изменений, но доступны для просмотра всем."""

    def has_permission(self, request: HttpRequest, view: View) -> bool:
        """Проверяет, имеет ли пользователь право на выполнение запроса."""

        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
