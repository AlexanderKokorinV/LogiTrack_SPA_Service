import io
import os
import sys
from unittest.mock import patch

import openpyxl
from django.apps import apps
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from backend.models import ShipmentLog


class ShipmentLogAPITests(APITestCase):
    """
    Комплексный набор тестов API путевых листов LogiTrack.

    Проверяются:
    - наличие тестовых данных;
    - серверная пагинация;
    - изменение размера страницы;
    - фильтрация по текстовым и числовым полям;
    - промежуточные состояния фильтрации SPA;
    - валидация параметров фильтрации;
    - сортировка;
    - ограничения CRUD API;
    - экспорт данных в Excel;
    - фильтрация при экспорте;
    - структура Excel-файла.
    """

    def setUp(self):
        """
        Создаёт контролируемый набор данных перед каждым тестом.
        """
        self.logs = []

        for i in range(1, 26):
            self.logs.append(
                ShipmentLog.objects.create(
                    name=(f"Маршрут {i}" if i <= 15 else f"Город {i} — Доставка"),
                    quantity=10 * i,
                    distance=100.5 * i,
                )
            )

        self.url = reverse("shipment-list")

    def test_auto_population_exists(self):
        """
        1. Проверяет наличие записей в тестовой базе данных.
        """
        self.assertGreaterEqual(
            ShipmentLog.objects.count(),
            25,
        )

    def test_pagination_server_side(self):
        """
        2. Проверяет серверную пагинацию.
        """
        response = self.client.get(
            self.url,
            {"page": 1},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(
            response.data["count"],
            25,
        )
        self.assertEqual(
            len(response.data["results"]),
            10,
        )

    def test_second_page_returns_expected_page_size(self):
        """
        3. Проверяет получение второй страницы.
        """
        response = self.client.get(
            self.url,
            {"page": 2},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(response.data["results"]),
            10,
        )

    def test_page_size_query_param_is_supported(self):
        """
        4. Проверяет изменение размера страницы через page_size.
        """
        response = self.client.get(
            self.url,
            {"page_size": 5},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(response.data["results"]),
            5,
        )

    def test_page_size_cannot_exceed_maximum(self):
        """
        5. Проверяет максимальный размер страницы.
        """
        ShipmentLog.objects.bulk_create(
            [
                ShipmentLog(
                    name=f"Дополнительный маршрут {i}",
                    quantity=100,
                    distance=100.0,
                )
                for i in range(100)
            ]
        )

        response = self.client.get(
            self.url,
            {"page_size": 1000},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(response.data["results"]),
            100,
        )

    def test_filter_equals_number(self):
        """
        6. Проверяет фильтрацию числового поля по условию equals.
        """
        response = self.client.get(
            self.url,
            {
                "column": "quantity",
                "condition": "equals",
                "value": "50",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["name"],
            "Маршрут 5",
        )

    def test_filter_equals_text(self):
        """
        7. Проверяет точное сравнение текстового поля.
        """
        response = self.client.get(
            self.url,
            {
                "column": "name",
                "condition": "equals",
                "value": "Маршрут 5",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["name"],
            "Маршрут 5",
        )

    def test_filter_contains_text(self):
        """
        8. Проверяет фильтрацию текстового поля по условию contains.
        """
        response = self.client.get(
            self.url,
            {
                "column": "name",
                "condition": "contains",
                "value": "Маршрут",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            15,
        )
        self.assertEqual(
            len(response.data["results"]),
            10,
        )

    def test_filter_greater_than(self):
        """
        9. Проверяет фильтрацию по условию greater.
        """
        response = self.client.get(
            self.url,
            {
                "column": "distance",
                "condition": "greater",
                "value": "2000",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            6,
        )

    def test_filter_less_than(self):
        """
        10. Проверяет фильтрацию по условию less.
        """
        response = self.client.get(
            self.url,
            {
                "column": "quantity",
                "condition": "less",
                "value": "40",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            3,
        )

    def test_filter_invalid_quantity_returns_400(self):
        """
        11. Некорректное значение quantity возвращает 400.
        """
        response = self.client.get(
            self.url,
            {
                "column": "quantity",
                "condition": "greater",
                "value": "слово_вместо_числа",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "value",
            response.data,
        )

    def test_filter_invalid_distance_returns_400(self):
        """
        12. Некорректное значение distance возвращает 400.
        """
        response = self.client.get(
            self.url,
            {
                "column": "distance",
                "condition": "less",
                "value": "не число",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "value",
            response.data,
        )

    def test_filter_unknown_column_returns_400(self):
        """
        13. Неизвестное поле фильтрации возвращает 400.
        """
        response = self.client.get(
            self.url,
            {
                "column": "password",
                "condition": "equals",
                "value": "123",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "column",
            response.data,
        )

    def test_filter_unsupported_condition_returns_400(self):
        """
        14. Недоступное для выбранного поля условие возвращает 400.
        """
        response = self.client.get(
            self.url,
            {
                "column": "quantity",
                "condition": "contains",
                "value": "10",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "condition",
            response.data,
        )

    def test_partial_filter_is_allowed(self):
        """
        15. Проверяет промежуточное состояние фильтра SPA.

        Пока SPA не передал все параметры фильтра, запрос не считается
        ошибочным и возвращает исходный список.
        """
        response = self.client.get(
            self.url,
            {"column": "quantity"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            25,
        )

    def test_sorting_by_quantity(self):
        """
        16. Проверяет сортировку по разрешённому полю quantity.
        """
        response = self.client.get(
            self.url,
            {"ordering": "quantity"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        results = response.data["results"]

        self.assertLess(
            results[0]["quantity"],
            results[1]["quantity"],
        )

    def test_sorting_by_distance_descending(self):
        """
        17. Проверяет сортировку distance по убыванию.
        """
        response = self.client.get(
            self.url,
            {"ordering": "-distance"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        results = response.data["results"]

        self.assertGreater(
            results[0]["distance"],
            results[1]["distance"],
        )

    def test_sorting_by_date_is_ignored(self):
        """
        18. Проверяет, что пользовательская сортировка по date
        не применяется.

        date используется только для сортировки по умолчанию.
        """
        response_default = self.client.get(
            self.url,
        )

        response_date = self.client.get(
            self.url,
            {"ordering": "date"},
        )

        self.assertEqual(
            response_default.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response_date.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response_default.data["results"][0]["id"],
            response_date.data["results"][0]["id"],
        )

    def test_crud_methods_are_not_available(self):
        """
        19. Проверяет, что создание и удаление записей через API
        списка недоступны.
        """
        post_response = self.client.post(
            self.url,
            {
                "name": "Новый рейс",
                "quantity": 10,
                "distance": 100.0,
            },
            format="json",
        )

        delete_response = self.client.delete(
            f"{self.url}{self.logs[0].id}/",
        )

        self.assertEqual(
            post_response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_export_excel_endpoint_all_data(self):
        """
        20. Проверяет экспорт всех записей без фильтрации.
        """
        export_url = reverse("shipment-export-excel")

        response = self.client.get(export_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response["Content-Type"],
            ("application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"),
        )
        self.assertIn(
            "Content-Disposition",
            response,
        )
        self.assertTrue(response["Content-Disposition"].startswith("attachment; filename="))

    def test_export_excel_with_active_filters(self):
        """
        21. Проверяет экспорт всех записей, соответствующих фильтру.

        Пагинация при экспорте не применяется.
        """
        export_url = reverse("shipment-export-excel")

        response = self.client.get(
            export_url,
            {
                "column": "quantity",
                "condition": "greater",
                "value": "200",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        excel_file = io.BytesIO(
            response.content,
        )

        wb = openpyxl.load_workbook(
            excel_file,
            read_only=True,
        )
        ws = wb.active

        # 1 строка заголовка + 5 отфильтрованных записей.
        self.assertEqual(
            ws.max_row,
            6,
        )

        wb.close()

    def test_export_excel_structure(self):
        """
        22. Проверяет структуру сформированного Excel-файла.
        """
        export_url = reverse("shipment-export-excel")

        response = self.client.get(export_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        excel_file = io.BytesIO(
            response.content,
        )

        wb = openpyxl.load_workbook(
            excel_file,
            read_only=False,
        )
        ws = wb.active

        expected_headers = [
            "Дата рейса",
            "Маршрут",
            "Количество груза (ед.)",
            "Расстояние (км)",
        ]

        actual_headers = [ws.cell(row=1, column=i).value for i in range(1, 5)]

        self.assertEqual(
            actual_headers,
            expected_headers,
        )
        self.assertEqual(
            ws.title,
            "Рейсы LogiTrack",
        )

        wb.close()

    def test_export_excel_invalid_filter_returns_400(self):
        """
        23. Некорректное числовое значение фильтра
        при экспорте возвращает 400.
        """
        export_url = reverse("shipment-export-excel")

        response = self.client.get(
            export_url,
            {
                "column": "quantity",
                "condition": "less",
                "value": "ошибка_синтаксиса",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "value",
            response.data,
        )


class BackendConfigTests(TestCase):
    """Тесты логики автоматического заполнения базы данных"""

    def setUp(self):
        """
        24. Используется зарегистрированный Django AppConfig
        """
        self.config = apps.get_app_config("backend")

    def test_ready_skips_during_test(self):
        """Проверяет, что автозаполнение отключено при запуске тестов"""

        with patch.object(sys, "argv", ["manage.py", "test"]):
            self.config.ready()

        self.assertEqual(ShipmentLog.objects.count(), 0)

    def test_ready_does_not_populate_existing_database(self):
        """
        25. Проверяет, что заполненная БД не заполняется повторно
        """

        ShipmentLog.objects.create(
            name="Москва — Казань",
            quantity=42,
            distance=820.5,
        )

        with patch.object(sys, "argv", ["manage.py", "runserver"]):
            with patch.dict(os.environ, {"RUN_MAIN": "false"}):
                self.config.ready()

        self.assertEqual(ShipmentLog.objects.count(), 1)

    def test_ready_populates_empty_database(self):
        """
        26. Проверяет автоматическое создание 120 рейсов в пустой БД
        """

        with patch.object(sys, "argv", ["manage.py", "runserver"]):
            with patch.dict(os.environ, {"RUN_MAIN": "false"}):
                self.config.ready()

        self.assertEqual(ShipmentLog.objects.count(), 120)

    def test_ready_handles_population_error(self):
        """
        27. Проверяет обработку ошибки автозаполнения
        """

        with patch.object(
            ShipmentLog.objects,
            "exists",
            side_effect=Exception("DB error"),
        ):
            with patch("backend.apps.logger.error") as mock_logger:
                with patch.object(
                    sys,
                    "argv",
                    ["manage.py", "runserver"],
                ):
                    with patch.dict(
                        os.environ,
                        {"RUN_MAIN": "false"},
                    ):
                        self.config.ready()

        mock_logger.assert_called_once()
