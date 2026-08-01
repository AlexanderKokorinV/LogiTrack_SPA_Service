from django.db import models

# Create your models here.


class ShipmentLog(models.Model):
    """Модель таблицы грузоперевозок (рейсов)"""

    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    name = models.CharField(max_length=255, verbose_name="Название")
    quantity = models.IntegerField(verbose_name="Количество")
    distance = models.FloatField(verbose_name="Расстояние")

    class Meta:
        verbose_name = "Рейс"
        verbose_name_plural = "Рейсы"
        ordering = ["-date"]
