from django.urls import path
from . import views

app_name = 'user_admin'

urlpatterns = [
    path('', views.user_list_view, name='user_list'),
    path('<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('<int:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    path('<int:user_id>/delete/', views.user_delete, name='user_delete'),
]
