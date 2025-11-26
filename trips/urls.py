# trips/urls.py
from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    # Trang chính - Khám phá Chuyến đi
    path('', views.TripHubView.as_view(), name='trip_hub'), 
    path('api/events/', views.trip_events_api, name='trip_events_api'),

    # Luồng tạo & sửa
    path('tao-moi/', views.create_trip_view, name='create_trip'),
    path('<int:pk>/<slug:slug>/chinh-sua/', views.TripUpdateView.as_view(), name='update_trip'),

    # Trang chi tiết
    path('<int:pk>/<slug:slug>/', views.TripDetailView.as_view(), name='trip_detail'),
    
    # API endpoints cho các hành động của người dùng
    path('<int:pk>/join/', views.join_trip_request, name='join_trip'),
    path('<int:pk>/leave/', views.leave_trip, name='leave_trip'),
    path('<int:pk>/cancel-request/', views.cancel_join_request, name='cancel_join_request'),

    # API endpoints cho Trưởng đoàn
    path('<int:pk>/members/<int:member_id>/approve/', views.approve_member, name='approve_member'),
    path('<int:pk>/members/<int:member_id>/reject/', views.reject_member, name='reject_member'),
    path('<int:pk>/media/upload/', views.upload_trip_media, name='upload_trip_media'),
    path('<int:pk>/media/<int:media_id>/set-cover/', views.set_trip_cover, name='set_trip_cover'),
    path('media/<int:media_id>/delete/', views.delete_trip_media, name='delete_trip_media'),
    path('chon-cung-duong/', views.SelectTrekForTripView.as_view(), name='select_trek_for_trip'),
    path('chuyen-di/<int:pk>/<slug:slug>/', views.TripDetailView.as_view(), name='chuyen_di_detail'),
]