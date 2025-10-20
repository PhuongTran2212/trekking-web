# post/urls.py

from django.urls import path
from . import views

app_name = 'post_admin'

urlpatterns = [
    # URL cho trang danh sách chính
    # VD: /dashboard/posts/manage/
    path('manage/', views.post_list_view, name='post_list'),
    
    # URL để cập nhật trạng thái (Duyệt/Từ chối)
    # VD: /dashboard/posts/manage/123/status/da_duyet/
    path('manage/<int:post_id>/status/<str:status>/', views.post_update_status_view, name='post_update_status'),

    # URL để xóa bài viết
    # VD: /dashboard/posts/manage/123/delete/
    path('manage/<int:post_id>/delete/', views.post_delete_view, name='post_delete'),
    path('manage/<int:post_id>/detail/', views.post_detail_view, name='post_detail'),
]