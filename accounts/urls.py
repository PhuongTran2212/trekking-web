# accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    dang_ky_view, 
    CustomLoginView, 
    profile_view, 
    profile_update_view,
    delete_equipment_view
)

app_name = 'accounts'

urlpatterns = [
    # URLs xác thực
    path('dang-ky/', dang_ky_view, name='dang-ky'),
    path('dang-nhap/', CustomLoginView.as_view(), name='dang-nhap'),
    path('dang-xuat/', auth_views.LogoutView.as_view(next_page='/'), name='dang-xuat'),

    # URLs cho Profile
    path('ho-so/<str:username>/', profile_view, name='profile-detail'),
    path('cai-dat/', profile_update_view, name='profile-update'),
    path('cai-dat/xoa-thiet-bi/<int:pk>/', delete_equipment_view, name='equipment-delete'),
]