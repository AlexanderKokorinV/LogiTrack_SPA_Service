import random

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models import ShipmentLog


class Command(BaseCommand):
    help = "Создание демонстрационных рейсов"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=120,
            help="Количество демонстрационных рейсов (по умолчанию: 120)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]

        if count <= 0:
            self.stdout.write(
                self.style.ERROR("Количество рейсов должно быть больше нуля.")
            )
            return

        if ShipmentLog.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "База данных уже содержит рейсы. "
                    "Генерация демонстрационных данных пропущена."
                )
            )
            return

        cities_from = [
            "Москва",
            "Санкт-Петербург",
            "Казань",
            "Владимир",
            "Нижний Новгород",
        ]

        cities_to = [
            "Новосибирск",
            "Самара",
            "Краснодар",
            "Ростов-на-Дону",
            "Уфа",
            "Челябинск",
        ]

        logs_to_create = []

        for _ in range(count):
            route_name = (
                f"{random.choice(cities_from)} — "
                f"{random.choice(cities_to)}"
            )

            quantity = random.randint(10, 150)
            distance = round(random.uniform(150.0, 3500.0), 1)

            logs_to_create.append(
                ShipmentLog(
                    name=route_name,
                    quantity=quantity,
                    distance=distance,
                )
            )

        ShipmentLog.objects.bulk_create(logs_to_create)

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно создано демонстрационных рейсов: {len(logs_to_create)}"
            )
        )