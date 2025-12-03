# trips/admin_urls.py
from django.urls import path
from . import views

app_name = 'trips_admin'

urlpatterns = [
    # ... (Các path cũ giữ nguyên) ...
    path('', views.TripAdminListView.as_view(), name='trip_list'),
    path('<int:pk>/force-cancel/', views.force_cancel_trip, name='force_cancel'),
    path('export/', views.export_trips_csv, name='trip_export'),
    path('<int:pk>/chat-log/', views.admin_peek_chat, name='trip_chat_log'),

    # === THÊM 3 DÒNG NÀY ĐỂ SỬA LỖI 404 ===
    path('<int:pk>/members-manage/', views.admin_trip_members_manage, name='trip_members_manage'),
    path('members/<int:member_id>/kick/', views.admin_kick_member, name='admin_kick_member'),
    path('members/<int:member_id>/restore/', views.admin_restore_member, name='admin_restore_member'),
    # --- THÊM 2 DÒNG NÀY ĐỂ ADMIN DÙNG CHUNG VIEW VỚI USER ---
    path('tao-moi/', views.create_trip_view, name='create_trip'),
    path('<int:pk>/<slug:slug>/chinh-sua/', views.TripUpdateView.as_view(), name='update_trip'),
    path('chon-cung-duong/', views.SelectTrekForTripView.as_view(), name='select_trek_for_trip'),
]