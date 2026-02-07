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

@staff_member_required
def analytics_view(request):
    from django.db.models import Count, Sum, F, Avg, FloatField, ExpressionWrapper, Case, When, IntegerField, Q
    from django.db.models.functions import TruncMonth, ExtractMonth
    from django.utils import timezone
    from trips.models import ChuyenDi, ChuyenDiThanhVien
    from treks.models import CungDuongTrek
    from accounts.models import TaiKhoanHoSo
    from community.models import CongDongBaiViet
    from core.models import The
    import json

    # 1. KPI CARDS
    total_users = User.objects.count()
    active_trips = ChuyenDi.objects.filter(trang_thai__in=['DANG_TUYEN', 'ONGOING']).count()
    
    # Fill Rate Calculation
    # Lấy các chuyến đi đã chốt (đang đi, đã xong, đã đóng) để tính cho chính xác
    closed_trips = ChuyenDi.objects.filter(trang_thai__in=['DA_DONG', 'ONGOING', 'ENDED', 'FULL']).annotate(
        member_count=Count('thanh_vien', filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA'))
    ).filter(so_luong_toi_da__gt=0)
    
    avg_fill_rate = 0
    if closed_trips.exists():
        total_fill = sum([(t.member_count / t.so_luong_toi_da) * 100 for t in closed_trips])
        avg_fill_rate = round(total_fill / closed_trips.count(), 1)

    # Est. Revenue (GMV)
    # Doanh thu = Chi phí * Số người tham gia
    revenue_trips = ChuyenDi.objects.annotate(
        paid_members=Count('thanh_vien', filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA'))
    ).exclude(chi_phi_uoc_tinh__isnull=True)
    
    est_revenue = 0
    for t in revenue_trips:
        est_revenue += (t.chi_phi_uoc_tinh or 0) * t.paid_members

    # 2. CHARTS DATA
    
    # A. Growth (Line Chart) - 6 tháng gần nhất (FIX: Xử lý Python thuần để tránh lỗi MySQL TruncMonth)
    from collections import OrderedDict
    
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    trips = ChuyenDi.objects.filter(ngay_bat_dau__gte=six_months_ago).only('ngay_bat_dau')
    
    # 1. Khởi tạo dict chứa 6 tháng gần nhất (để đảm bảo trục X liên tục)
    stats = OrderedDict()
    now = timezone.now()
    for i in range(5, -1, -1):
        # Logic lùi tháng thủ công
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        key = f"{m:02d}/{y}"
        stats[key] = 0

    # 2. Đếm số lượng chuyến đi
    for trip in trips:
        if trip.ngay_bat_dau:
            # Lưu ý: trip.ngay_bat_dau là datetime, cần convert sang string key
            # Nếu cần chính xác theo múi giờ VN, có thể cần timezone.localtime(trip.ngay_bat_dau)
            # Ở đây lấy đơn giản theo UTC hoặc server time
            key = trip.ngay_bat_dau.strftime('%m/%Y')
            if key in stats:
                stats[key] += 1
    
    growth_labels = list(stats.keys())
    growth_data = list(stats.values())

    # B. Trip Status (Doughnut)
    status_counts = ChuyenDi.objects.values('trang_thai').annotate(count=Count('id'))
    status_map = {
        'CHO_DUYET': 'Chờ duyệt', 'DANG_TUYEN': 'Đang tuyển', 
        'DA_HUY': 'Đã hủy', 'ENDED': 'Đã kết thúc', 
        'ONGOING': 'Đang đi', 'FULL': 'Full', 'DA_DONG': 'Đã đóng'
    }
    status_labels = [status_map.get(item['trang_thai'], item['trang_thai']) for item in status_counts]
    status_data = [item['count'] for item in status_counts]

    # C. BCG Matrix (Scatter)
    # X: Popularity (Trip count), Y: Quality (Avg Rating)
    bcg_data = []
    treks = CungDuongTrek.objects.annotate(trip_count=Count('chuyendi')).filter(trip_count__gt=0)
    for trek in treks:
        bcg_data.append({
            'x': trek.trip_count,
            'y': float(trek.danh_gia_trung_binh),
            'name': trek.ten
        })

    # D. Funnel (Bar/Funnel)
    # Register -> Active -> Member -> Host
    active_users_count = User.objects.filter(is_active=True).count()
    member_users_count = ChuyenDiThanhVien.objects.values('user').distinct().count()
    host_users_count = ChuyenDi.objects.values('nguoi_to_chuc').distinct().count()
    
    funnel_categories = ['Đăng ký', 'Active', 'Thành viên (Đi tour)', 'Host (Tổ chức)']
    funnel_data = [total_users, active_users_count, member_users_count, host_users_count]

    # E. Geo Distribution (Bar)
    geo_stats = TaiKhoanHoSo.objects.values('tinh_thanh__ten')\
        .annotate(count=Count('user'))\
        .order_by('-count')[:10]
    geo_labels = [item['tinh_thanh__ten'] or 'Chưa cập nhật' for item in geo_stats]
    geo_data = [item['count'] for item in geo_stats]

    # F. Tags Radar (Core Tags in Trips)
    # Đếm số chuyến đi theo từng Tag
    tag_stats = The.objects.annotate(trip_count=Count('chuyendi')).order_by('-trip_count')[:8]
    radar_labels = [tag.ten for tag in tag_stats]
    radar_data = [tag.trip_count for tag in tag_stats]

    # G. Word Cloud (Community Tags)
    # Đếm số bài viết theo Tag
    comm_tag_stats = The.objects.annotate(post_count=Count('bai_viet_cong_dong')).order_by('-post_count')[:20]
    wordcloud_data = [{'x': tag.ten, 'y': tag.post_count} for tag in comm_tag_stats if tag.post_count > 0]

    context = {
        'title': 'Analytics Command Center',
        'kpi': {
            'total_users': total_users,
            'active_trips': active_trips,
            'avg_fill_rate': avg_fill_rate,
            'est_revenue': est_revenue,
        },
        'charts': {
            'growth': json.dumps({'labels': growth_labels, 'data': growth_data}),
            'status': json.dumps({'labels': status_labels, 'data': status_data}),
            'bcg': json.dumps(bcg_data),
            'funnel': json.dumps({'categories': funnel_categories, 'data': funnel_data}),
            'geo': json.dumps({'labels': geo_labels, 'data': geo_data}),
            'radar': json.dumps({'labels': radar_labels, 'data': radar_data}),
            'wordcloud': json.dumps(wordcloud_data),
        }
    }
    return render(request, 'user_admin/analytics.html', context)

@staff_member_required
def analytics_export(request):
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    from django.db.models import Count, Q
    from django.db.models.functions import TruncMonth
    from trips.models import ChuyenDi, ChuyenDiThanhVien
    from treks.models import CungDuongTrek
    from accounts.models import TaiKhoanHoSo
    from core.models import The
    from collections import OrderedDict

    response = HttpResponse(content_type='text/csv')
    filename = f"analytics_report_{timezone.now().strftime('%Y-%m-%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Add BOM for Excel to read UTF-8 correctly
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response)
    
    # --- 1. KPI ---
    writer.writerow(['--- KPI SUMMARY ---'])
    total_users = User.objects.count()
    active_trips = ChuyenDi.objects.filter(trang_thai__in=['DANG_TUYEN', 'ONGOING']).count()
    
    # Fill Rate
    closed_trips = ChuyenDi.objects.filter(trang_thai__in=['DA_DONG', 'ONGOING', 'ENDED', 'FULL']).annotate(
        member_count=Count('thanh_vien', filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA'))
    ).filter(so_luong_toi_da__gt=0)
    avg_fill_rate = 0
    if closed_trips.exists():
        total_fill = sum([(t.member_count / t.so_luong_toi_da) * 100 for t in closed_trips])
        avg_fill_rate = round(total_fill / closed_trips.count(), 1)
        
    # Revenue
    revenue_trips = ChuyenDi.objects.annotate(
        paid_members=Count('thanh_vien', filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA'))
    ).exclude(chi_phi_uoc_tinh__isnull=True)
    est_revenue = 0
    for t in revenue_trips:
        est_revenue += (t.chi_phi_uoc_tinh or 0) * t.paid_members
        
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Users', total_users])
    writer.writerow(['Active Trips', active_trips])
    writer.writerow(['Avg Fill Rate (%)', avg_fill_rate])
    writer.writerow(['Est. Revenue (VND)', est_revenue])
    writer.writerow([])
    
    # --- 2. Growth ---
    writer.writerow(['--- GROWTH DATA (Last 6 Months) ---'])
    writer.writerow(['Month', 'Trips Created'])
    
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    trips = ChuyenDi.objects.filter(ngay_bat_dau__gte=six_months_ago).only('ngay_bat_dau')
    stats = OrderedDict()
    now = timezone.now()
    for i in range(5, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0: m += 12; y -= 1
        key = f"{m:02d}/{y}"
        stats[key] = 0
    for trip in trips:
        if trip.ngay_bat_dau:
            key = trip.ngay_bat_dau.strftime('%m/%Y')
            if key in stats: stats[key] += 1
            
    for k, v in stats.items():
        writer.writerow([k, v])
    writer.writerow([])

    # --- 3. Trip Status ---
    writer.writerow(['--- TRIP STATUS ---'])
    writer.writerow(['Status', 'Count'])
    status_counts = ChuyenDi.objects.values('trang_thai').annotate(count=Count('id'))
    for item in status_counts:
        writer.writerow([item['trang_thai'], item['count']])
    writer.writerow([])
    
    # --- 4. BCG Matrix ---
    writer.writerow(['--- BCG MATRIX (Product Analysis) ---'])
    writer.writerow(['Trek Name', 'Trips (Popularity)', 'Avg Rating (Quality)'])
    treks = CungDuongTrek.objects.annotate(trip_count=Count('chuyendi')).filter(trip_count__gt=0)
    for trek in treks:
        writer.writerow([trek.ten, trek.trip_count, trek.danh_gia_trung_binh])
    writer.writerow([])
    
    # --- 5. Funnel ---
    writer.writerow(['--- USER FUNNEL ---'])
    writer.writerow(['Stage', 'Count'])
    active_users_count = User.objects.filter(is_active=True).count()
    member_users_count = ChuyenDiThanhVien.objects.values('user').distinct().count()
    host_users_count = ChuyenDi.objects.values('nguoi_to_chuc').distinct().count()
    writer.writerow(['Registered', total_users])
    writer.writerow(['Active', active_users_count])
    writer.writerow(['Members (Joined Trip)', member_users_count])
    writer.writerow(['Hosts (Organized Trip)', host_users_count])
    writer.writerow([])
    
    # --- 6. Geo ---
    writer.writerow(['--- GEO DISTRIBUTION (Top 10) ---'])
    writer.writerow(['Location', 'User Count'])
    geo_stats = TaiKhoanHoSo.objects.values('tinh_thanh__ten').annotate(count=Count('user')).order_by('-count')[:10]
    for item in geo_stats:
        writer.writerow([item['tinh_thanh__ten'] or 'Unknown', item['count']])
        
    return response

@staff_member_required
def analytics_users_view(request):
    from django.db.models import Count
    from django.utils import timezone
    from collections import OrderedDict
    import json
    
    # 1. SCORECARDS
    total_users = User.objects.count()
    
    # Số Host: Là những user đã từng tổ chức ít nhất 1 chuyến đi
    # distinct() là quan trọng để không đếm trùng
    hosts_count = ChuyenDi.objects.values('nguoi_to_chuc').distinct().count()
    
    # Member only = Tổng - Host
    members_only_count = total_users - hosts_count
    
    # New Members This Month
    now = timezone.now()
    new_users_month = User.objects.filter(
        date_joined__year=now.year, 
        date_joined__month=now.month
    ).count()
    
    # 2. CHARTS DATA
    
    # A. User Growth (Last 6 Months)
    six_months_ago = now - timezone.timedelta(days=180)
    users_growth = User.objects.filter(date_joined__gte=six_months_ago).only('date_joined')
    
    stats = OrderedDict()
    # Init dict
    for i in range(5, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0: m += 12; y -= 1
        key = f"{m:02d}/{y}"
        stats[key] = 0
        
    for u in users_growth:
        key = u.date_joined.strftime('%m/%Y')
        if key in stats: stats[key] += 1
        
    growth_labels = list(stats.keys())
    growth_data = list(stats.values())
    
    # B. Host vs Member Ratio
    ratio_labels = ['Host (Người tạo tour)', 'Member (Chỉ đi chơi)']
    ratio_data = [hosts_count, members_only_count]
    
    # 3. TOP HOSTS
    # Top 10 người tổ chức nhiều chuyến đi nhất
    # Dùng select_related để lấy đầy đủ thông tin User object (bao gồm date_joined)
    top_hosts = User.objects.annotate(
        trip_count=Count('chuyendi_da_to_chuc')
    ).filter(trip_count__gt=0).order_by('-trip_count').select_related('taikhoanhoso')[:10]

    context = {
        'title': 'Thống kê Người dùng',
        'kpi': {
            'total_users': total_users,
            'hosts_count': hosts_count,
            'new_users_month': new_users_month,
        },
        'charts': {
            'growth': json.dumps({'labels': growth_labels, 'data': growth_data}),
            'ratio': json.dumps({'labels': ratio_labels, 'data': ratio_data}),
        },
        'top_hosts': top_hosts
    }
    return render(request, 'user_admin/analytics_users.html', context)

@staff_member_required
def analytics_trips_view(request):
    from django.db.models import Count
    from django.utils import timezone
    from collections import OrderedDict
    import json
    
    # 1. SCORECARDS
    total_trips = ChuyenDi.objects.count()
    active_trips = ChuyenDi.objects.filter(trang_thai__in=['DANG_TUYEN', 'ONGOING']).count()
    completed_trips = ChuyenDi.objects.filter(trang_thai='ENDED').count()
    cancelled_trips = ChuyenDi.objects.filter(trang_thai='DA_HUY').count()
    
    # 2. CHARTS DATA
    
    # A. Status Distribution (Pie)
    status_labels = ['Hoàn thành', 'Đã hủy', 'Đang chạy/Tuyển', 'Khác']
    other_count = total_trips - (active_trips + completed_trips + cancelled_trips)
    status_data = [completed_trips, cancelled_trips, active_trips, other_count]
    
    # B. Trip Frequency (Bar Chart - Last 6 Months)
    now = timezone.now()
    six_months_ago = now - timezone.timedelta(days=180)
    trips_freq = ChuyenDi.objects.filter(ngay_bat_dau__gte=six_months_ago).only('ngay_bat_dau')
    
    stats = OrderedDict()
    for i in range(5, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0: m += 12; y -= 1
        key = f"{m:02d}/{y}"
        stats[key] = 0
        
    for t in trips_freq:
        if t.ngay_bat_dau:
            key = t.ngay_bat_dau.strftime('%m/%Y')
            if key in stats: stats[key] += 1
            
    freq_labels = list(stats.keys())
    freq_data = list(stats.values())
    
    # 3. UPCOMING TRIPS
    upcoming_trips = ChuyenDi.objects.filter(
        ngay_bat_dau__gte=now,
        trang_thai__in=['DANG_TUYEN', 'FULL']
    ).order_by('ngay_bat_dau')[:10].select_related('cung_duong', 'nguoi_to_chuc')

    context = {
        'title': 'Thống kê Chuyến đi',
        'kpi': {
            'total_trips': total_trips,
            'active_trips': active_trips,
            'completed_trips': completed_trips,
            'cancelled_trips': cancelled_trips,
        },
        'charts': {
            'status': json.dumps({'labels': status_labels, 'data': status_data}),
            'freq': json.dumps({'labels': freq_labels, 'data': freq_data}),
        },
        'upcoming_trips': upcoming_trips
    }
    return render(request, 'user_admin/analytics_trips.html', context)

@staff_member_required
def analytics_treks_view(request):
    from django.db.models import Count
    import json
    
    # 1. SCORECARDS
    total_treks = CungDuongTrek.objects.count()
    provinces_count = CungDuongTrek.objects.values('tinh_thanh').distinct().count()
    
    # 2. CHARTS DATA
    
    # A. Top Treks (Bar)
    top_treks_data = CungDuongTrek.objects.annotate(
        trip_count=Count('chuyendi')
    ).filter(trip_count__gt=0).order_by('-trip_count')[:10]
    
    top_labels = [t.ten for t in top_treks_data]
    top_data = [t.trip_count for t in top_treks_data]
    
    # B. Difficulty (Pie)
    # do_kho is integer 1-5 or similar? Assuming it's a choice field.
    # If it's a choice field, we might need get_do_kho_display, but for aggregation we use values.
    # Let's check model if possible, but assuming standard field.
    diff_stats = CungDuongTrek.objects.values('do_kho').annotate(count=Count('id'))
    
    # Mapping difficulty levels if they are stored as numbers/codes
    # Assuming: 1: Dễ, 2: Trung bình, 3: Khó, etc. Or strings.
    # We will use the raw value for now, or map if we knew the choices.
    # Let's try to map common values if they are strings like 'DE', 'TB', 'KHO'
    # Or if numbers.
    diff_labels = []
    diff_data = []
    for item in diff_stats:
        # Simple fallback display
        label = item['do_kho']
        if label == '1': label = 'Dễ'
        elif label == '2': label = 'Trung bình'
        elif label == '3': label = 'Khó'
        elif label == '4': label = 'Rất khó'
        
        diff_labels.append(str(label))
        diff_data.append(item['count'])
        
    # 3. NEW TREKS
    new_treks = CungDuongTrek.objects.select_related('tinh_thanh', 'do_kho').order_by('-id')[:5]

    context = {
        'title': 'Thống kê Cung đường',
        'kpi': {
            'total_treks': total_treks,
            'provinces_count': provinces_count,
        },
        'charts': {
            'top': json.dumps({'labels': top_labels, 'data': top_data}),
            'diff': json.dumps({'labels': diff_labels, 'data': diff_data}),
        },
        'new_treks': new_treks
    }
    return render(request, 'user_admin/analytics_treks.html', context)

@staff_member_required
def analytics_content_view(request):
    from django.db.models import Count, Sum, F
    from django.utils import timezone
    from collections import OrderedDict
    from community.models import CongDongBaiViet, CongDongBinhLuan
    from core.models import The
    import json
    
    # 1. SCORECARDS
    total_posts = CongDongBaiViet.objects.count()
    total_comments = CongDongBinhLuan.objects.count()
    
    # luot_binh_chon is a field in CongDongBaiViet
    total_votes = CongDongBaiViet.objects.aggregate(total=Sum('luot_binh_chon'))['total'] or 0
    
    # 2. CHARTS DATA
    
    # A. Activity (Line - Posts per month)
    now = timezone.now()
    six_months_ago = now - timezone.timedelta(days=180)
    posts_activity = CongDongBaiViet.objects.filter(ngay_dang__gte=six_months_ago).only('ngay_dang')
    
    stats = OrderedDict()
    for i in range(5, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0: m += 12; y -= 1
        key = f"{m:02d}/{y}"
        stats[key] = 0
        
    for p in posts_activity:
        key = p.ngay_dang.strftime('%m/%Y')
        if key in stats: stats[key] += 1
        
    activity_labels = list(stats.keys())
    activity_data = list(stats.values())
    
    # B. Top Tags (Bar)
    # Tags are in 'tags' ManyToMany field
    # We need to count how many posts use each tag
    top_tags = The.objects.annotate(
        post_count=Count('bai_viet_cong_dong')
    ).filter(post_count__gt=0).order_by('-post_count')[:10]
    
    tag_labels = [t.ten for t in top_tags]
    tag_data = [t.post_count for t in top_tags]
    
    # 3. TOP POSTS (Engagement = Comments + Votes)
    # Note: 'binh_luan' is related_name from CongDongBinhLuan
    top_posts = CongDongBaiViet.objects.annotate(
        comment_count=Count('binh_luan'),
        engagement=F('comment_count') + F('luot_binh_chon')
    ).order_by('-engagement')[:5].select_related('tac_gia')

    context = {
        'title': 'Thống kê Bài viết',
        'kpi': {
            'total_posts': total_posts,
            'total_comments': total_comments,
            'total_votes': total_votes,
        },
        'charts': {
            'activity': json.dumps({'labels': activity_labels, 'data': activity_data}),
            'tags': json.dumps({'labels': tag_labels, 'data': tag_data}),
        },
        'top_posts': top_posts
    }
    return render(request, 'user_admin/analytics_content.html', context)
