from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пользовательская пагинация для управления постраничным выводом данных.
    Этот класс наследуется от PageNumberPagination и переопределяет параметры пагинации
    для использования кастомного параметра размера страницы в URL-запросе."""

    page_size_query_param = "page_size"
    max_page_size = 100
