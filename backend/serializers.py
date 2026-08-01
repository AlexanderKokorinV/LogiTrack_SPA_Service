from rest_framework import serializers

from backend.models import ShipmentLog


class ShipmentLogSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рейсов"""

    date = serializers.DateTimeField(format="%d/%m/%Y %H:%M", read_only=True)

    class Meta:
        model = ShipmentLog
        fields = "__all__"
