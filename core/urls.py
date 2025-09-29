# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Khi truy cập trang gốc, gọi hàm demo_view
    path('', views.demo_view, name='demo'),
]