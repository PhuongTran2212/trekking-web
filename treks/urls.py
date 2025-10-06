# treks/urls.py

from django.urls import path
from . import views

# Đặt một tên riêng cho các URL này để tránh trùng lặp
app_name = 'treks_admin' 

urlpatterns = [
    # 1. Trang danh sách: /dashboard/cung-duong/
    path('', views.CungDuongListView.as_view(), name='cung_duong_list'),
    
    # 2. Trang thêm mới: /dashboard/cung-duong/them/
    path('them/', views.CungDuongCreateView.as_view(), name='cung_duong_create'),
    
    # 3. Trang cập nhật: /dashboard/cung-duong/1/sua/
    path('<int:pk>/sua/', views.CungDuongUpdateView.as_view(), name='cung_duong_update'),
    
    # 4. Trang xóa: /dashboard/cung-duong/1/xoa/
    path('<int:pk>/xoa/', views.CungDuongDeleteView.as_view(), name='cung_duong_delete'),
]