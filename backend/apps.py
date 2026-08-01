import logging
import os
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class BackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend"

    def ready(self):
        """Переопределение метода для автозаполнения БД случайными значениями"""
        # Предотвращение запуска скрипта при миграциях и сборке статики (ложное срабатывание)
        if "manage.py" in sys.argv and any(x in sys.argv for x in ["makemigrations", "migrate", "collectstatic"]):
            return

        # Проверка, что это основной рабочий процесс, а не автоперезапуск Django (защита от двойного запуска)
        if os.environ.get("RUN_MAIN") != "true":
            try:
                import random

                from .models import ShipmentLog

                # Проверка, является ли БД пустой
                if not ShipmentLog.objects.exists():
                    logger.info("Инициализация базы данных: старт генерации рейсов.")

                    cities_from = ["Москва", "Санкт-Петербург", "Казань", "Владимир", "Нижний Новгород"]
                    cities_to = ["Новосибирск", "Самара", "Краснодар", "Ростов-на-Дону", "Уфа", "Челябинск"]

                    logs_to_create = []
                    for _ in range(120):  # Генерирация 120 рейсов (или 12 страниц пагинации)
                        route_name = f"{random.choice(cities_from)} — {random.choice(cities_to)}"
                        quantity = random.randint(10, 150)  # Объем груза (количество или вес)
                        distance = round(random.uniform(150.0, 3500.0), 1)  # Расстояние в км

                        logs_to_create.append(ShipmentLog(name=route_name, quantity=quantity, distance=distance))

                    # Быстрая массовая вставка с помощью bulk_create
                    ShipmentLog.objects.bulk_create(logs_to_create)
                    logger.info(f"База данных успешно заполнена. Создано {len(logs_to_create)} рейсов.")

            except Exception as e:
                logger.error(f"Критическая ошибка автозаполнения БД: {e}", exc_info=True)
