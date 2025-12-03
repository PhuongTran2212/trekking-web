# trekking_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from accounts.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tai-khoan/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('', home_view, name='home'),
    path('dashboard/', core_views.admin_dashboard_view, name='admin_dashboard'),

    # Dòng này sẽ trỏ đến file treks/admin_urls.py
    path('dashboard/cung-duong/', include('treks.admin_urls', namespace='treks_admin')),

    # Dòng này sẽ trỏ đến file treks/urls.py
    path('cung-duong/', include('treks.urls', namespace='treks')),
    path('tinymce/', include('tinymce.urls')),
    path('chuyen-di/', include('trips.urls')),
    path('thanh-tuu/', include(('gamification.urls', 'gamification'), namespace='gamification')),
    path('dashboard/trips/', include('trips.admin_urls')),
    path('admin-dashboard/trips/', include('trips.admin_urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)