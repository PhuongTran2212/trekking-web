# knowledge/urls.py
from django.urls import path
from . import views

app_name = 'knowledge'

urlpatterns = [
    path('', views.KnowledgeListView.as_view(), name='list'),
    path('article/<int:pk>/', views.KnowledgeDetailView.as_view(), name='detail'),
    path('contribute/', views.ContributionCreateView.as_view(), name='contribute'),
]