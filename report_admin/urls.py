# report_admin/urls.py

from django.urls import path
from . import views

app_name = 'report_admin'

urlpatterns = [
    # URL cho trang danh sách báo cáo
    # VD: /dashboard/reports/manage/
    path('manage/', views.report_list_view, name='report_list'),
    
    # URL cho trang chi tiết và xử lý một báo cáo
    # VD: /dashboard/reports/manage/5/detail/
    path('manage/<int:report_id>/detail/', views.report_detail_view, name='report_detail'),
]