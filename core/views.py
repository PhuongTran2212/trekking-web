# core/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
def demo_view(request):
    # Hàm này chỉ có một nhiệm vụ: hiển thị file base.html
    return render(request, 'base.html')

def is_admin_check(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin_check)
def admin_dashboard_view(request):
    # RENDER FILE dashboard.html NẰM TRONG THƯ MỤC templates/admin/
    return render(request, 'admin/dashboard.html')
