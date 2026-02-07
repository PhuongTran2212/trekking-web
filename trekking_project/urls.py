from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from accounts.views import home_view

urlpatterns = [
    # --- PHẦN CHUNG (SYSTEM) ---
    path('admin/', admin.site.urls),
    path('tai-khoan/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('tinymce/', include('tinymce.urls')),

    # --- TRANG CHỦ & CORE ---
    path('', home_view, name='home'),
    path('', include('core.urls')), # Của bạn: Thêm các url core khác nếu có

    # --- PUBLIC URLs (Dành cho người dùng xem) ---
    # Treks (Cung đường) - Public
    path('cung-duong/', include('treks.urls', namespace='treks')),
    # Trips (Chuyến đi) - Public
    path('chuyen-di/', include('trips.urls', namespace='trips')),
    # Gamification (Thành tựu)
    path('thanh-tuu/', include(('gamification.urls', 'gamification'), namespace='gamification')),
    # Community (Cộng đồng) - Của bạn bạn
    path("community/", include(("community.urls", "community"), namespace="community")),
    # Knowledge (Kiến thức) - Của bạn bạn
    path('knowledge/', include('knowledge.urls', namespace='knowledge')),


    # --- DASHBOARD URLs (Dành cho quản trị viên) ---
    path('dashboard/', core_views.admin_dashboard_view, name='admin_dashboard'),
    
    # 1. Treks Admin: Tôi ưu tiên dùng 'treks.admin_urls' của bạn để tách biệt logic quản lý
    path('dashboard/cung-duong/', include('treks.admin_urls', namespace='treks_admin')),
    
    # 2. Trips Admin: Của bạn
    path('dashboard/trips/', include('trips.admin_urls', namespace='trips_admin')),

    # 3. Posts Admin: Của bạn bạn
    path('dashboard/posts/', include('post.urls', namespace='post_admin')),

    # 4. Reports Admin: Của bạn bạn
    path('dashboard/reports/', include('report_admin.urls', namespace='report_admin')),

    # 5. Articles Admin: Của bạn bạn
    path('dashboard/articles/', include('articles.urls', namespace='articles')),

    # 6. User Admin: Của bạn (Mới)
    path('dashboard/users/', include('user_admin.urls', namespace='user_admin')),
]

# Chỉ dùng khi DEBUG=True để phục vụ media trong dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)