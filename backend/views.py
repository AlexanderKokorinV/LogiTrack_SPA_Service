import logging

from rest_framework import viewsets

from backend.models import ShipmentLog
from backend.pagination import ShipmentlogPagination
from backend.serializers import ShipmentLogSerializer


# Create your views here.

logger = logging.getLogger(__name__)

class ShipmentLogViewSet(viewsets.ModelViewSet):
    """Контроллер для страницы SPA-приложения"""
    queryset = ShipmentLog.objects.all()
    serializer_class = ShipmentLogSerializer
    pagination_class = ShipmentlogPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        # Считывание параметров фильтрации из URL-запроса
        column = self.request.query_params.get("column") # выбор колонки (название, количество, расстояние)
        condition = self.request.query_params.get("condition") # условие (равно, содержит, больше, меньше)
        value = self.request.query_params.get("value") # значение для фильтрации

        if column and condition and value:
            lookup = None
            if condition == "equals":
                lookup = f"{column}__iexact" if column == "name" else f"{column}"
            elif condition == "contains" and column == "name":
                lookup = "name__icontains"
            elif condition == "greater":
                lookup = f"{column}__gt"
            elif condition == "less":
                lookup = f"{column}__lt"

            if lookup:
                try:
                    queryset = queryset.filter(**{lookup: value})
                    logger.info(f"Применен фильтр: {lookup}={value}. Найдено записей: {queryset.count()}")
                except (TypeError, ValueError) as e:
                    logger.warning(
                        f"Ошибка валидации типа данных при фильтрации. "
                        f"Колонка: {column}, Условие: {condition}, Значение: {value}. Ошибка: {e}"
                    )
                    pass

        ordering = self.request.query_params.get("ordering")
        if ordering and "date" not in ordering:
            queryset = queryset.order_by(ordering)

        return queryset

