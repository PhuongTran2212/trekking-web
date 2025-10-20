# cSpell:disable

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from accounts.views import home_view
# --- THÊM CÁC DÒNG NÀY ---
from django.conf import settings
from django.conf.urls.static import static
# -------------------------

urlpatterns = [
    path('admin/', admin.site.urls),

    # URL cho app accounts
    path('tai-khoan/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Trang chủ
    path('', home_view, name='home'),
     # URL cho trang dashboard của admin
    path('dashboard/', core_views.admin_dashboard_view, name='admin_dashboard'),
        # --- DÒNG MỚI ---
    # Bất kỳ URL nào bắt đầu bằng 'cung-duong/' sẽ được chuyển đến file treks/urls.py
    path('dashboard/cung-duong/', include('treks.urls', namespace='treks_admin')),
    path("community/", include(("community.urls", "community"), namespace="community")),
    path('dashboard/posts/', include('post.urls', namespace='post_admin')),
    
]

# Chỉ dùng khi DEBUG=True để phục vụ media trong dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    