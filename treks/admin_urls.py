# treks/admin_urls.py

from django.urls import path
from . import views

app_name = 'treks_admin' 

urlpatterns = [
    path('', views.CungDuongListView.as_view(), name='cung_duong_list'),
    path('them-moi/', views.CungDuongCreateView.as_view(), name='cung_duong_create'),
    path('<int:pk>/', views.CungDuongDetailView.as_view(), name='cung_duong_detail'),
    path('<int:pk>/chinh-sua/', views.CungDuongUpdateView.as_view(), name='cung_duong_update'),
    path('<int:pk>/xoa/', views.CungDuongDeleteView.as_view(), name='cung_duong_delete'),
    path('media/<int:pk>/delete-now/', views.delete_media_view, name='cung_duong_media_delete_now'),
    path('api/search-location/', views.NominatimProxyView.as_view(), name='nominatim_proxy'),
    
    # URL MỚI CHO TRANG BẢN ĐỒ RIÊNG
    path('<int:pk>/chinh-sua-ban-do/', views.CungDuongMapUpdateView.as_view(), name='cung_duong_edit_map'),
]