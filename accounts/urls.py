# accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
<<<<<<< HEAD

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
=======
from .views import dang_ky_view, CustomLoginView
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43

app_name = 'accounts'

urlpatterns = [
<<<<<<< HEAD
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
=======
    path('dang-ky/', dang_ky_view, name='dang-ky'),
    path('dang-nhap/', CustomLoginView.as_view(), name='dang-nhap'),
    path('dang-xuat/', auth_views.LogoutView.as_view(next_page='/'), name='dang-xuat'),
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
]