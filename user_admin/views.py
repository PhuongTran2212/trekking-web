from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from accounts.models import TaiKhoanHoSo

@staff_member_required
def user_list_view(request):
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    role_filter = request.GET.get('role', '')

    users = User.objects.prefetch_related('taikhoanhoso').all().order_by('-date_joined')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(taikhoanhoso__sdt__icontains=search_query)
        )

    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    if role_filter:
        if role_filter == 'staff':
            users = users.filter(is_staff=True)
        elif role_filter == 'user':
            users = users.filter(is_staff=False)

    paginator = Paginator(users, 20) # Show 20 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    locked_users = User.objects.filter(is_active=False).count()
    
    from django.utils import timezone
    today = timezone.now().date()
    new_users_today = User.objects.filter(date_joined__date=today).count()

    context = {
        'users': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'role_filter': role_filter,
        'title': 'Quản lý Người dùng',
        'stats': {
            'total': total_users,
            'active': active_users,
            'locked': locked_users,
            'new_today': new_users_today
        }
    }
    return render(request, 'user_admin/user_list.html', context)

from trips.models import ChuyenDi
from treks.models import CungDuongTrek
from community.models import CongDongBaiViet

@staff_member_required
def user_detail_view(request, user_id):
    user = get_object_or_404(User.objects.prefetch_related('taikhoanhoso'), id=user_id)
    
    # 1. Trips Hosted
    trips_hosted = ChuyenDi.objects.filter(nguoi_to_chuc=user).select_related('cung_duong', 'anh_bia').prefetch_related('thanh_vien').order_by('-ngay_bat_dau')
    
    # 2. Trips Joined
    trips_joined = ChuyenDi.objects.filter(thanh_vien__user=user).exclude(nguoi_to_chuc=user).select_related('cung_duong', 'anh_bia').order_by('-ngay_bat_dau')
    
    # 3. Treks Created
    treks_created = CungDuongTrek.objects.filter(nguoi_tao=user).select_related('tinh_thanh', 'do_kho').prefetch_related('media').order_by('-ngay_tao')
    
    # 4. Posts Created
    posts_created = CongDongBaiViet.objects.filter(tac_gia=user).prefetch_related('media', 'binh_luan', 'binh_chon').order_by('-ngay_dang')

    # 5. Gear & Interests
    from accounts.models import TaiKhoanThietBiCaNhan, TaiKhoanSoThichNguoiDung
    user_gear = TaiKhoanThietBiCaNhan.objects.filter(user=user).select_related('vat_dung', 'vat_dung__loai_vat_dung')
    user_interests = TaiKhoanSoThichNguoiDung.objects.filter(user=user).select_related('the')

    context = {
        'user_obj': user,
        'title': f'Chi tiết người dùng: {user.username}',
        'trips_hosted': trips_hosted,
        'trips_joined': trips_joined,
        'treks_created': treks_created,
        'posts_created': posts_created,
        'user_gear': user_gear,
        'user_interests': user_interests,
        'stats': {
            'trips_hosted_count': trips_hosted.count(),
            'trips_joined_count': trips_joined.count(),
            'treks_count': treks_created.count(),
            'posts_count': posts_created.count(),
        }
    }
    return render(request, 'user_admin/user_detail.html', context)

@staff_member_required
def user_toggle_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            messages.error(request, "Không thể thay đổi trạng thái của Superuser.")
        else:
            user.is_active = not user.is_active
            user.save()
            status_msg = "kích hoạt" if user.is_active else "vô hiệu hóa"
            messages.success(request, f"Đã {status_msg} tài khoản {user.username}.")
    
    return redirect('user_admin:user_list')

@staff_member_required
def user_delete(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
             messages.error(request, "Không thể xóa Superuser.")
        else:
            username = user.username
            user.delete()
            messages.success(request, f"Đã xóa tài khoản {username}.")
    
    return redirect('user_admin:user_list')
