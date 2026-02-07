from django.urls import path
from . import views

app_name = 'user_admin'

urlpatterns = [
    path('', views.user_list_view, name='user_list'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('analytics/users/', views.analytics_users_view, name='analytics_users'),
    path('analytics/trips/', views.analytics_trips_view, name='analytics_trips'),
    path('analytics/treks/', views.analytics_treks_view, name='analytics_treks'),
    path('analytics/content/', views.analytics_content_view, name='analytics_content'),
    path('analytics/export/', views.analytics_export, name='analytics_export'),
    path('<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('<int:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    path('<int:user_id>/delete/', views.user_delete, name='user_delete'),
]
