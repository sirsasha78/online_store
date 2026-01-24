from drf_spectacular.utils import OpenApiParameter, OpenApiTypes

from core import settings


PRODUCT_PARAM_EXAMPLE = [
    OpenApiParameter(
        name="max_price",
        description="Фильтровать товары по максимальной текущей цене",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="min_price",
        description="Фильтровать товары по минимальной текущей цене",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="in_stock",
        description="Фильтровать товары по ассортименту",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="created_at",
        description="Фильтровать товары по дате создания",
        required=False,
        type=OpenApiTypes.DATE,
    ),
    OpenApiParameter(
        name="page_size",
        description=f"Количество элементов на странице, которое вы хотите отобразить. По умолчанию используется {settings.REST_FRAMEWORK["PAGE_SIZE"]}",
        required=False,
        type=OpenApiTypes.INT,
    ),
]
