from django.urls import path

from backend.views import ShipmentLogExportExcelView, ShipmentLogListView

urlpatterns = [
    path(
        "shipments/",
        ShipmentLogListView.as_view(),
        name="shipment-list",
    ),
    path(
        "shipments/export_excel/",
        ShipmentLogExportExcelView.as_view(),
        name="shipment-export-excel",
    ),
]
