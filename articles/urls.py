from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('list/', views.AdminArticleListView.as_view(), name='admin-list'),
    # Dòng này sẽ hết lỗi sau khi bạn thêm AdminArticleCreateView vào views.py
    path('create/', views.AdminArticleCreateView.as_view(), name='admin-create'), 
    path('approve/<int:pk>/', views.approve_article, name='admin-approve'),
    path('update/<int:pk>/', views.AdminArticleUpdateView.as_view(), name='admin-update'),
    path('delete/<int:pk>/', views.AdminArticleDeleteView.as_view(), name='admin-delete'),
]