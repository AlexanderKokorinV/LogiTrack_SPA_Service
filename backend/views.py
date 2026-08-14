import logging

import openpyxl
from django.db.models import QuerySet
from django.http import HttpResponse
from openpyxl.styles import Alignment, Font, PatternFill
from rest_framework import filters, generics
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from backend.models import ShipmentLog
from backend.pagination import ShipmentlogPagination
from backend.serializers import ShipmentLogSerializer

# Create your views here.

logger = logging.getLogger(__name__)


class ShipmentLogQueryMixin:
    """Общая логика фильтрации путевых листов"""

    FILTERS = {
        "name": {
            "equals": "name__iexact",
            "contains": "name__icontains",
        },
        "quantity": {
            "equals": "quantity",
            "greater": "quantity__gt",
            "less": "quantity__lt",
        },
        "distance": {
            "equals": "distance",
            "greater": "distance__gt",
            "less": "distance__lt",
        },
    }

    # Валидация - разрешена сортировка только по полям, предусмотренным ТЗ
    ordering_fields = [
        "name",
        "quantity",
        "distance",
    ]

    def get_filtered_queryset(self, queryset: QuerySet[ShipmentLog]) -> QuerySet[ShipmentLog]:
        """
        Применяет фильтрацию к переданному QuerySet.
        Фильтр применяется только после получения всех необходимых
        параметров от SPA.
        """

        # Считывание параметров фильтрации из URL-запроса
        column = self.request.query_params.get("column")  # выбор колонки (название, количество, расстояние)
        condition = self.request.query_params.get("condition")  # условие (равно, содержит, больше, меньше)
        value = self.request.query_params.get("value")  # значение для фильтрации

        # Фильтр применяется только после того,
        # как SPA передал все необходимые параметры
        if not all((column, condition, value)):
            return queryset

        if column not in self.FILTERS:
            logger.warning(
                "Недопустимое поле фильтрации: column=%s",
                column,
            )

            raise ValidationError({"column": f"Недопустимое поле фильтрации: {column}."})

        if condition not in self.FILTERS[column]:
            logger.warning(
                "Недопустимое условие фильтрации: " "column=%s, condition=%s",
                column,
                condition,
            )

            raise ValidationError({"condition": (f"Условие '{condition}' недоступно " f"для поля '{column}'.")})

        lookup = self.FILTERS[column][condition]

        # Числовые значения преобразуются явно,
        # чтобы некорректный ввод не передавался непосредственно в ORM.
        if column == "quantity":
            try:
                value = int(value)
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "Некорректное значение фильтра: " "column=%s, condition=%s, value=%s",
                    column,
                    condition,
                    value,
                )

                raise ValidationError(
                    {"value": (f"Некорректное значение '{value}' " f"для поля '{column}'.")}
                ) from exc

        elif column == "distance":
            try:
                value = float(value)
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "Некорректное значение фильтра: " "column=%s, condition=%s, value=%s",
                    column,
                    condition,
                    value,
                )

                raise ValidationError(
                    {"value": (f"Некорректное значение '{value}' " f"для поля '{column}'.")}
                ) from exc

        return queryset.filter(**{lookup: value})


class ShipmentLogListView(ShipmentLogQueryMixin, generics.ListAPIView):
    """
    Контроллер для управления списком путевых листов с фильтрацией, сортировкой
    и серверной пагинацией.
    """

    queryset = ShipmentLog.objects.all()
    serializer_class = ShipmentLogSerializer
    pagination_class = ShipmentlogPagination

    # Стандартный DRF OrderingFilter отвечает за обработку параметра ordering
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ShipmentLogQueryMixin.ordering_fields

    # Новые рейсы отображаются первыми
    ordering = ["-date"]

    def get_queryset(self) -> QuerySet[ShipmentLog]:
        """
        Возвращает отфильтрованный QuerySet путевых листов.
        Сортировка применяется стандартным OrderingFilter.
        """
        queryset = super().get_queryset()

        return self.get_filtered_queryset(queryset)


class ShipmentLogExportExcelView(ShipmentLogQueryMixin, generics.GenericAPIView):
    """
    Экспортирует отфильтрованные и отсортированные путевые листы
    в формате Excel.
    """

    queryset = ShipmentLog.objects.all()

    def get_queryset(self) -> QuerySet[ShipmentLog]:
        """Возвращает QuerySet путевых листов с применёнными
        фильтрацией и сортировкой без серверной пагинации.
        """
        queryset = super().get_queryset()

        # Используется общая логика фильтрации,
        # чтобы экспорт полностью соответствовал результату списка
        queryset = self.get_filtered_queryset(queryset)

        ordering = self.request.query_params.get("ordering")

        if not ordering:
            return queryset.order_by("-date")

        allowed_ordering = set(self.ordering_fields)

        if ordering.lstrip("-") not in allowed_ordering:
            logger.warning(
                "Недопустимое поле сортировки при экспорте: ordering=%s",
                ordering,
            )
            raise ValidationError({"ordering": (f"Недопустимое поле сортировки: {ordering}.")})

        return queryset.order_by(ordering)

    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """
        Экспортирует все записи, соответствующие текущим
        фильтрам и сортировке, в файл Excel.
        """

        # 1. Получаем отфильтрованный QuerySet
        queryset = self.get_queryset()

        logger.info(
            "Начат экспорт путевых листов в Excel: " "filters=%s, ordering=%s",
            {
                "column": request.query_params.get("column"),
                "condition": request.query_params.get("condition"),
            },
            request.query_params.get("ordering", "-date"),
        )

        try:
            # 2. Создаем книгу Excel в памяти
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Рейсы LogiTrack"

            # Стили оформления
            header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="1E4ED8", end_color="1E4ED8", fill_type="solid")  # Синяя заливка
            data_font = Font(name="Segoe UI", size=10)
            center_align = Alignment(horizontal="center", vertical="center")

            # 3. Записываем заголовки
            headers = [
                "Дата рейса",
                "Маршрут",
                "Количество груза (ед.)",
                "Расстояние (км)",
            ]

            ws.append(headers)

            for col_num, header in enumerate(headers, start=1):
                cell = ws.cell(
                    row=1,
                    column=col_num,
                )
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align

            # 4. Записываем данные из БД
            for shipment in queryset:

                # Форматируем дату
                date_str = shipment.date.strftime("%d.%m.%Y %H:%M") if shipment.date else ""

                row_data = [
                    date_str,
                    shipment.name,
                    shipment.quantity,
                    shipment.distance,
                ]

                # Записываем строку в таблицу Excel
                ws.append(row_data)

                current_row = ws.max_row

                # Применяем созданный data_font к каждой ячейке новой строки
                for col_num in range(1, 5):
                    ws.cell(
                        row=current_row,
                        column=col_num,
                    ).font = data_font

            # Выравниваем ширину колонок под текст автоматически
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(
                    max_len + 3,
                    12,
                )

            # 5. Формируем HTTP-ответ с файлом
            response = HttpResponse(
                content_type=("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet")
            )
            response["Content-Disposition"] = "attachment; " "filename='LogiTrack_Full_Report.xlsx'"

            # Записываем книгу в тело ответа
            wb.save(response)

            logger.info("Экспорт путевых листов в Excel успешно завершён.")

            return response

        except Exception:
            logger.exception("Ошибка при формировании Excel-отчёта.")
            raise
