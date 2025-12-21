import secrets

from apps.common.models import BaseModel


def generate_unique_code(model: BaseModel, field: str) -> str:
    """Генерирует уникальный 12-символьный код из букв латинского алфавита и цифр.
    Код состоит только из заглавных букв латинского алфавита (A-Z) и цифр (1-9).
    Проверяет, существует ли уже объект указанной модели с таким значением
    в заданном поле. Если объект найден, генерация повторяется рекурсивно
    до тех пор, пока не будет получен уникальный код."""

    allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    unique_code = "".join(secrets.choice(allowed_chars) for _ in range(12))
    similar_object_exists = model.objects.filter(**{field: unique_code}).exists()
    if not similar_object_exists:
        return unique_code
    return generate_unique_code(model, field)
