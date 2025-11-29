# articles/urls.py
from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    # URLs cho quản lý bài viết
    path('list/', views.AdminArticleListView.as_view(), name='admin-list'),
    path('create/', views.AdminArticleCreateView.as_view(), name='admin-create'),
    path('approve/<int:pk>/', views.approve_article, name='admin-approve'),
    path('update/<int:pk>/', views.AdminArticleUpdateView.as_view(), name='admin-update'),
    path('delete/<int:pk>/', views.AdminArticleDeleteView.as_view(), name='admin-delete'),
    path('detail/<int:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),

    # ==========================================================
    # === THÊM CÁC URL QUẢN LÝ CHUYÊN MỤC VÀO ĐÂY ===
    # ==========================================================
    path('categories/list/', views.ChuyenMucListView.as_view(), name='admin-category-list'),
    path('categories/create/', views.ChuyenMucCreateView.as_view(), name='admin-category-create'),
    path('categories/update/<int:pk>/', views.ChuyenMucUpdateView.as_view(), name='admin-category-update'),
    path('categories/delete/<int:pk>/', views.ChuyenMucDeleteView.as_view(), name='admin-category-delete'),
]