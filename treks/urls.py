# treks/urls.py

from django.urls import path
from . import user_views

# app_name là bắt buộc để Django nhận diện được namespace
app_name = 'treks'

urlpatterns = [
    path('', user_views.CungDuongListView.as_view(), name='cung_duong_list'),
    path('<slug:slug>/', user_views.CungDuongDetailView.as_view(), name='cung_duong_detail'),
]