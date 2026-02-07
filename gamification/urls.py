from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # --- PHẦN NGƯỜI DÙNG & XEM DANH SÁCH ---
    # Sửa 'list/' thành 'danh-sach/' để khớp với link bạn đang truy cập
    path('danh-sach/', views.BadgeListView.as_view(), name='badge_list'),
    
    # Danh sách huy hiệu của user
    path('cua-toi/', views.MyBadgeListView.as_view(), name='my_badges'),
    
    # --- PHẦN QUẢN LÝ (CRUD CHO STAFF/ADMIN) ---
    path('tao-moi/', views.BadgeCreateView.as_view(), name='badge_create'),
    path('cap-nhat/<int:pk>/', views.BadgeUpdateView.as_view(), name='badge_update'),
    path('xoa/<int:pk>/', views.BadgeDeleteView.as_view(), name='badge_delete'),
]