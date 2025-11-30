# trips/urls.py
from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    # =============================================
    # 1. CÁC TRANG TĨNH & KHỞI TẠO (Ưu tiên cao nhất)
    # =============================================
    path('', views.TripHubView.as_view(), name='trip_hub'), 
    path('api/events/', views.trip_events_api, name='trip_events_api'),
    path('chon-cung-duong/', views.SelectTrekForTripView.as_view(), name='select_trek_for_trip'),
    
    # Luồng tạo mới
    path('tao-moi/', views.create_trip_view, name='create_trip'),
    path('tao-moi/thanh-cong/<int:pk>/', views.TripCreateSuccessView.as_view(), name='trip_create_success'),

    # =============================================
    # 2. CÁC API XỬ LÝ MEDIA & THÀNH VIÊN (QUAN TRỌNG)
    # Phải đặt TRƯỚC các path có <slug:slug> để tránh lỗi 404
    # =============================================
    
    # --- Media (Ảnh/Video) ---
    path('<int:pk>/media/<int:media_id>/set-cover/', views.set_trip_cover, name='set_trip_cover'),
    path('<int:pk>/media/upload/', views.upload_trip_media, name='upload_trip_media'),
    path('media/<int:media_id>/delete/', views.delete_trip_media, name='delete_trip_media'),

    # --- Quản lý thành viên (Trưởng đoàn) ---
    path('<int:pk>/members/<int:member_id>/approve/', views.approve_member, name='approve_member'),
    path('<int:pk>/members/<int:member_id>/reject/', views.reject_member, name='reject_member'),

    # --- Tương tác cá nhân (Tham gia/Rời) ---
    path('<int:pk>/join/', views.join_trip_request, name='join_trip'),
    path('<int:pk>/leave/', views.leave_trip, name='leave_trip'),
    path('<int:pk>/cancel-request/', views.cancel_join_request, name='cancel_join_request'),

    # =============================================
    # 3. CÁC TRANG CHI TIẾT & CHỈNH SỬA (DYNAMIC SLUG)
    # Đặt ở cuối cùng vì nó bắt mọi từ khóa dạng chuỗi
    # =============================================
    path('<int:pk>/<slug:slug>/chinh-sua/', views.TripUpdateView.as_view(), name='update_trip'),
    
    # Trang chi tiết (Có 2 dạng URL để support cũ/mới)
    path('<int:pk>/<slug:slug>/', views.TripDetailView.as_view(), name='trip_detail'),
    path('chuyen-di/<int:pk>/<slug:slug>/', views.TripDetailView.as_view(), name='chuyen_di_detail'),
        # === CHAT ROOM URLS ===
    path('chat/<int:trip_id>/', views.TripChatRoomView.as_view(), name='chat_room'),
    path('chat/<int:trip_id>/send/', views.send_chat_message, name='chat_send'),
    path('chat/<int:trip_id>/get-messages/', views.get_chat_messages, name='chat_get_messages'),
    path('chat/delete/<int:msg_id>/', views.delete_chat_message, name='chat_delete'),
    path('chat/react/<int:msg_id>/', views.react_chat_message, name='chat_react'),
    
]