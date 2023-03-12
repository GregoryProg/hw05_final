from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    now_year = timezone.now().year
    return {
        'year': now_year,
    }
