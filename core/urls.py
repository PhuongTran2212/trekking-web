# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ... các url khác ...
    path('system-configuration/', views.system_config_view, name='system_config'),
    
    # URL Xóa (Dùng pk)
    path('system-configuration/delete/<str:model_type>/<int:pk>/', views.delete_master_data, name='delete_master_data'),
    
    # URL Thêm mới (Không có pk)
    path('system-configuration/save/<str:model_type>/', views.save_master_data, name='add_master_data'),
    
    # URL Cập nhật (Dùng pk - CHÚ Ý DÒNG NÀY)
    path('system-configuration/save/<str:model_type>/<int:pk>/', views.save_master_data, name='edit_master_data'),
]