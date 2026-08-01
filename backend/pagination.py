from rest_framework import pagination


class ShipmentlogPagination(pagination.PageNumberPagination):
    """Пагинация для страницы SPA-приложения"""
    page_size = 10 # 10 строк на страницу
    page_size_query_param = "page_size"