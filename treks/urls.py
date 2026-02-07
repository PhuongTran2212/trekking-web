# treks/urls.py

from django.urls import path
from . import user_views

# app_name là bắt buộc để Django nhận diện được namespace
app_name = 'treks'

urlpatterns = [
    path('', user_views.CungDuongListView.as_view(), name='cung_duong_list'),
    path('<slug:slug>/', user_views.CungDuongDetailView.as_view(), name='cung_duong_detail'),
        # URL để xử lý việc xóa một đánh giá
    # Ví dụ: /treks/review/123/delete/
    path('review/<int:pk>/delete/', user_views.delete_review, name='delete_review'),

    # URL để hiển thị form và xử lý việc cập nhật một đánh giá
    # Ví dụ: /treks/review/123/update/
    path('api/review/<int:pk>/', user_views.get_review_data, name='get_review_data'),
    path('api/review-image/<int:pk>/delete/', user_views.delete_review_image, name='delete_review_image'),
]