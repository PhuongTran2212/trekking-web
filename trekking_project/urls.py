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
     path('', include('core.urls')), 

    # Admin Treks
    path('dashboard/cung-duong/', include('treks.admin_urls', namespace='treks_admin')),

    # Public Treks
    path('cung-duong/', include('treks.urls', namespace='treks')),
    
    path('tinymce/', include('tinymce.urls')),
    
    # Public Trips (Người dùng) - Thêm namespace cho rõ ràng
    path('chuyen-di/', include('trips.urls', namespace='trips')), 
    
    path('thanh-tuu/', include(('gamification.urls', 'gamification'), namespace='gamification')),
    
    # Admin Trips (Dashboard) - GIỮ DÒNG NÀY (Có namespace)
    path('dashboard/trips/', include('trips.admin_urls', namespace='trips_admin')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)