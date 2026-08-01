from django.urls import path, include
from rest_framework.routers import DefaultRouter
from backend.views import ShipmentLogViewSet

router = DefaultRouter()
router.register(r"shipments", ShipmentLogViewSet, basename="shipment")

urlpatterns = [
    path("", include(router.urls)),
]