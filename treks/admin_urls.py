# treks/admin_urls.py (NỘI DUNG CHÍNH XÁC)

from django.urls import path
from . import views as admin_views
from . import views
# Khai báo app_name để Django có thể tìm thấy namespace cho 'treks_admin'
# Mặc dù namespace được định nghĩa trong include(), app_name vẫn cần thiết
app_name = 'treks_admin' 

urlpatterns = [
    # Danh sách (dashboard/cung-duong/)
    path('', admin_views.CungDuongListView.as_view(), name='cung_duong_list'),
    
    # Thêm mới (dashboard/cung-duong/them-moi/)
    path('them-moi/', admin_views.CungDuongCreateView.as_view(), name='cung_duong_create'),
    
    # Chi tiết admin (dashboard/cung-duong/1/)
    path('<int:pk>/', admin_views.CungDuongDetailView.as_view(), name='cung_duong_detail'),
    
    # Chỉnh sửa (dashboard/cung-duong/1/chinh-sua/)
    path('<int:pk>/chinh-sua/', admin_views.CungDuongUpdateView.as_view(), name='cung_duong_update'),
    
    # Xóa (dashboard/cung-duong/1/xoa/)
    path('<int:pk>/xoa/', admin_views.CungDuongDeleteView.as_view(), name='cung_duong_delete'),
    path(
        'media/<int:pk>/delete-now/', 
        views.delete_media_view, # Trỏ đến view function
        name='cung_duong_media_delete_now' # Tên phải khớp chính xác với template
    ),
]