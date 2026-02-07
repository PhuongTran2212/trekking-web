# accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views

# Import các view với tên cũ
from .views import (
    dang_ky_view, 
    CustomLoginView, 
    profile_view, 
    profile_update_view,
    delete_equipment_view,
    edit_equipment_view,
    get_equipment_by_category  # Import view mới
)

app_name = 'accounts'

urlpatterns = [
    # URLs xác thực
    path('dang-ky/', dang_ky_view, name='dang-ky'),
    path('dang-nhap/', CustomLoginView.as_view(), name='dang-nhap'),
    path('dang-xuat/', auth_views.LogoutView.as_view(next_page='home'), name='dang-xuat'),

    # URLs cho Profile
    path('ho-so/<str:username>/', profile_view, name='profile-detail'),
    path('cai-dat/', profile_update_view, name='profile-update'),
    
    # URLs cho quản lý thiết bị
    path('cai-dat/xoa-thiet-bi/<int:pk>/', delete_equipment_view, name='equipment-delete'),
    path('cai-dat/sua-thiet-bi/<int:pk>/', edit_equipment_view, name='equipment-edit'),
    
    # === THÊM MỚI: URL cho API để lấy danh sách thiết bị ===
    path('api/get-equipment-by-category/', get_equipment_by_category, name='api_get_equipment_by_category'),
]