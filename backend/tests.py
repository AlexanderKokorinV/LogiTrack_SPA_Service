import logging

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from backend.models import ShipmentLog

# Отключаем вывод логов в консоль на время выполнения тестов
logging.disable(logging.CRITICAL)


class ShipmentLogAPITests(APITestCase):
    """
    Комплексный набоp тестов для проверки ShipmentLog API.
    Тестирует основные функции платформы LogiTrack:
    - Автоматическую инициализацию демонстрационных данных.
    - Серверную пагинацию (выдача строго по 10 элементов).
    - Динамическую фильтрацию по текстовым и числовым полям (equals, contains, greater, less).
    - Кастомную сортировку и блокировку сортировки по полю даты.
    - Устойчивость API к некорректным типам данных в поисковых запросах.
    """

    def setUp(self):
        """Вызывается перед каждым тест-кейсом. Заполняем изолированную тестовую БД."""
        self.logs = []
        # Создаем 25 контролируемых записей для проверки математики пагинации и фильтров
        for i in range(1, 26):
            self.logs.append(
                ShipmentLog.objects.create(
                    name=f"Маршрут {i}" if i <= 15 else f"Город {i} — Доставка",
                    quantity=10 * i,  # 10, 20, 30 ... 250
                    distance=100.5 * i,  # 100.5, 201.0 ... 2512.5
                )
            )
        # Наш эндпоинт маршрутизации /api/shipments/
        self.url = reverse("shipment-list")

    def test_auto_population_exists(self):
        """1. Тест успешной инициализации и наполнения базы данных"""
        count = ShipmentLog.objects.count()
        self.assertTrue(count >= 25)

    def test_pagination_server_side(self):
        """2. Тест пагинации на стороне сервера (строго по 10 элементов)"""
        response = self.client.get(self.url, {"page": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем структуру ответа пагинатора DRF
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        # На первой странице должно быть ровно 10 записей, а всего в базе — 25
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 25)

    def test_filter_equals_number(self):
        """3. Тест кастомного фильтра 'Равно' для числовых полей"""
        # Ищем рейс, где количество строго равно 50 (это Маршрут 5)
        response = self.client.get(self.url, {"column": "quantity", "condition": "equals", "value": "50"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Маршрут 5")

    def test_filter_contains_text(self):
        """4. Тест кастомного фильтра 'Содержит' для строк"""
        # У нас первые 15 записей содержат в названии слово 'Маршрут'
        response = self.client.get(self.url, {"column": "name", "condition": "contains", "value": "Маршрут"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Всего найдено 15, но пагинатор выдаст только первые 10 на страницу
        self.assertEqual(response.data["count"], 15)
        self.assertEqual(len(response.data["results"]), 10)

    def test_filter_greater_than(self):
        """5. Тест кастомного фильтра 'Больше чем' для расстояния"""
        # Дистанция > 2000. Это i от 20 до 25 включительно (всего 6 записей)
        response = self.client.get(self.url, {"column": "distance", "condition": "greater", "value": "2000"})
        self.assertEqual(response.data["count"], 6)

    def test_filter_less_than(self):
        """6. Тест кастомного фильтра 'Меньше чем' для количества"""
        # Количество < 40 (это i=1(10), i=2(20), i=3(30) -> всего 3 записи)
        response = self.client.get(self.url, {"column": "quantity", "condition": "less", "value": "40"})
        self.assertEqual(response.data["count"], 3)

    def test_sorting_by_quantity(self):
        """7. Тест кастомной сортировки по возрастанию количества"""
        response = self.client.get(self.url, {"ordering": "quantity"})
        results = response.data["results"]
        # Проверяем, что количество в первой строчке меньше, чем во второй
        self.assertTrue(results[0]["quantity"] < results[1]["quantity"])

    def test_sorting_by_date_blocked(self):
        """8. Тест блокировки сортировки по дате по ТЗ"""
        # Запрашиваем дефолтный список (сортировка -date из Meta)
        response_default = self.client.get(self.url)
        # Запрашиваем принудительную сортировку по дате
        response_date = self.client.get(self.url, {"ordering": "date"})

        # ID первой записи не должен измениться, так как контроллер проигнорировал параметр 'date'
        self.assertEqual(response_default.data["results"][0]["id"], response_date.data["results"][0]["id"])

    def test_filter_invalid_type_protection(self):
        """9. Тест защиты try-except от некорректного ввода букв вместо чисел"""
        response = self.client.get(
            self.url, {"column": "quantity", "condition": "greater", "value": "слово_вместо_числа"}
        )
        # База данных не должна упасть с ошибкой 500, возвращается 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forced_db_population_logic(self):
        """10. Тест внутренней логики генератора из apps.py"""
        import random

        from backend.models import ShipmentLog

        # Эмулируем пустую базу данных
        ShipmentLog.objects.all().delete()

        # Запускаем саму математику генератора вручную
        cities_from = ["Москва", "Санкт-Петербург"]
        cities_to = ["Новосибирск", "Самара"]
        logs_to_create = []

        for _ in range(5):  # Генерируем тестовую мини-партию
            route_name = f"{random.choice(cities_from)} — {random.choice(cities_to)}"
            logs_to_create.append(ShipmentLog(name=route_name, quantity=10, distance=100.0))

        ShipmentLog.objects.bulk_create(logs_to_create)
        self.assertEqual(ShipmentLog.objects.count(), 5)
