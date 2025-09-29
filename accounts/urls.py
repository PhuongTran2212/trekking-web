# accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from .views import dang_ky_view, CustomLoginView

app_name = 'accounts'

urlpatterns = [
    path('dang-ky/', dang_ky_view, name='dang-ky'),
    path('dang-nhap/', CustomLoginView.as_view(), name='dang-nhap'),
    path('dang-xuat/', auth_views.LogoutView.as_view(next_page='/'), name='dang-xuat'),
]