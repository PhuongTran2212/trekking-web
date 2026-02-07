# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

# Import các Model và Form
from .models import TinhThanh, LoaiVatDung, VatDung, The
from .forms import TinhThanhForm, LoaiVatDungForm, VatDungForm, TheForm

# --- Helper Functions ---
def is_admin_check(user):
    return user.is_staff

# --- Admin Views ---

@login_required
@user_passes_test(is_admin_check)
def admin_dashboard_view(request):
    """
    Dashboard quản trị với KPI Cards, Quick Actions, Recent Activities, Risk List
    """
    from trips.models import ChuyenDi  # Import tại đây để tránh circular import
    from community.models import CongDongBaiViet
    from treks.models import CungDuongTrek
    
    today = timezone.now().date()
    now = timezone.now()
    seven_days_later = now + timedelta(days=7)
    three_days_later = now + timedelta(days=3)
    
    # ==========================================
    # 1. KPI CARDS
    # ==========================================
    
    # Thành viên mới hôm nay
    new_users_today = User.objects.filter(
        date_joined__date=today
    ).count()
    
    # Cần duyệt gấp (Bài viết + Cung đường chờ duyệt)
    pending_posts = CongDongBaiViet.objects.filter(
        trang_thai='CHO_DUYET'
    ).count()
    
    pending_treks = CungDuongTrek.objects.filter(
        trang_thai='CHO_DUYET'
    ).count()
    
    pending_total = pending_posts + pending_treks
    
    # Sắp khởi hành trong 7 ngày
    upcoming_trips_count = ChuyenDi.objects.filter(
        ngay_bat_dau__range=[now, seven_days_later],
        trang_thai__in=['TUYEN_THANH_VIEN', 'CHUAN_BI']
    ).count()
    
    # Chuyến có rủi ro (sắp đi trong 3 ngày nhưng chưa đủ người hoặc chưa có ai)
    risk_trips = ChuyenDi.objects.filter(
        ngay_bat_dau__range=[now, three_days_later],
        trang_thai__in=['TUYEN_THANH_VIEN', 'CHUAN_BI']
    ).annotate(
        member_count=Count('thanh_vien')
    ).filter(
        member_count__lt=2  # Chuyến có ít hơn 2 người
    ).select_related('nguoi_to_chuc', 'cung_duong')[:5]
    
    risk_count = risk_trips.count()
    
    # ==========================================
    # 2. RECENT ACTIVITIES
    # ==========================================
    # Chuyến đi mới tạo
    recent_trips = ChuyenDi.objects.select_related(
        'nguoi_to_chuc', 'cung_duong'
    ).order_by('-ngay_tao')[:5]
    
    # Cung đường mới tạo
    recent_treks = CungDuongTrek.objects.select_related(
        'nguoi_tao', 'tinh_thanh'
    ).order_by('-ngay_tao')[:5]
    
    # Bài viết cộng đồng mới
    recent_posts = CongDongBaiViet.objects.select_related(
        'tac_gia'
    ).order_by('-ngay_dang')[:5]
    
    # ==========================================
    # 3. CONTEXT
    # ==========================================
    context = {
        'title': 'Dashboard',
        
        # KPI Cards
        'kpi': {
            'new_users': new_users_today,
            'pending': pending_total,
            'pending_posts': pending_posts,
            'pending_treks': pending_treks,
            'upcoming': upcoming_trips_count,
        },
        'risk_count': risk_count,
        
        # Recent Activities
        'recent_trips': recent_trips,
        'recent_treks': recent_treks,
        'recent_posts': recent_posts,
        
        # Risk List
        'risk_trips': risk_trips,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin_check)
def system_config_view(request):
    """
    Hàm hiển thị trang cấu hình hệ thống với 4 chỉ số thống kê cho MỖI tab.
    """
    # 1. Query dữ liệu cơ bản
    tinh_thanhs = TinhThanh.objects.all().order_by('ten')
    loai_vat_dungs = LoaiVatDung.objects.all().order_by('ten')
    vat_dungs = VatDung.objects.select_related('loai_vat_dung').all().order_by('ten')
    thes = The.objects.all().order_by('ten')

    # ======================================================
    # 1. STATS: TỈNH THÀNH
    # ======================================================
    # Mục tiêu: Đếm số lượng Cung đường Trek thuộc tỉnh đó
    stats_tinh = { 
        'total': tinh_thanhs.count(), 
        'hot_name': '---', 
        'hot_count': 0, 
        'unused': 0 
    }
    try:
        # Dùng 'cungduongtrek_set' vì trong model CungDuongTrek không có related_name="treks"
        tt_data = TinhThanh.objects.annotate(count=Count('cungduongtrek_set'))
        
        # Tỉnh có nhiều cung đường nhất
        top_tt = tt_data.order_by('-count').first()
        if top_tt and top_tt.count > 0:
            stats_tinh['hot_name'] = top_tt.ten
            stats_tinh['hot_count'] = top_tt.count
            
        # Tỉnh chưa có cung đường nào
        stats_tinh['unused'] = tt_data.filter(count=0).count()
    except Exception as e:
        print(f"Lỗi Stats Tỉnh: {e}")

    # ======================================================
    # 2. STATS: LOẠI VẬT DỤNG
    # ======================================================
    # Mục tiêu: Đếm số lượng Vật dụng thuộc loại này
    stats_loai = { 
        'total': loai_vat_dungs.count(), 
        'hot_name': '---', 
        'hot_count': 0, 
        'unused': 0 
    }
    try:
        # Dùng 'vatdung_set' (Mặc định của Django)
        lvd_data = LoaiVatDung.objects.annotate(count=Count('vatdung_set'))
        
        top_lvd = lvd_data.order_by('-count').first()
        if top_lvd and top_lvd.count > 0:
            stats_loai['hot_name'] = top_lvd.ten
            stats_loai['hot_count'] = top_lvd.count
            
        # Loại chưa có vật dụng nào
        stats_loai['unused'] = lvd_data.filter(count=0).count()
    except Exception as e:
        print(f"Lỗi Stats Loại: {e}")

    # ======================================================
    # 3. STATS: VẬT DỤNG
    # ======================================================
    # Mục tiêu: Đếm số lần vật dụng được GỢI Ý trong các Cung đường
    stats_vat_dung = { 
        'total': vat_dungs.count(), 
        'hot_name': '---', 
        'hot_count': 0, 
        'unused': vat_dungs.count()
    }
    try:
        # Model trung gian là CungDuongVatDungGoiY
        # Tên ngược mặc định là: cungduongvatdunggoiy_set
        vd_data = VatDung.objects.annotate(count=Count('cungduongvatdunggoiy_set')) 
        
        top_vd = vd_data.order_by('-count').first()
        if top_vd and top_vd.count > 0:
            stats_vat_dung['hot_name'] = top_vd.ten
            stats_vat_dung['hot_count'] = top_vd.count
            
        stats_vat_dung['unused'] = vd_data.filter(count=0).count()
    except Exception as e:
        print(f"Lỗi Stats Vật dụng: {e}")

    # ======================================================
    # 4. STATS: THẺ (TAGS)
    # ======================================================
    # Mục tiêu: Đếm số lần thẻ được dùng trong Chuyến đi
    stats_the = { 
        'total': thes.count(), 
        'hot_name': '---', 
        'hot_count': 0, 
        'unused': thes.count() 
    }
    try:
        # Trong Trip model có related_name='trips' -> Dùng 'trips'
        # Nếu lỗi, thử đổi thành 'chuyendi_set'
        the_data = The.objects.annotate(count=Count('trips'))
        
        top_the = the_data.order_by('-count').first()
        if top_the and top_the.count > 0:
            stats_the['hot_name'] = top_the.ten
            stats_the['hot_count'] = top_the.count
            
        stats_the['unused'] = the_data.filter(count=0).count()
    except Exception as e:
        print(f"Lỗi Stats Thẻ: {e}")

    # Context
    context = {
        'tinh_thanhs': tinh_thanhs,
        'loai_vat_dungs': loai_vat_dungs,
        'vat_dungs': vat_dungs,
        'thes': thes,
        
        # Truyền stats
        'stats_tinh': stats_tinh,
        'stats_loai': stats_loai,
        'stats_vat_dung': stats_vat_dung, # Lưu ý tên biến này
        'stats_the': stats_the,
        
        'active_tab': request.GET.get('tab', 'tinh-thanh')
    }
    return render(request, 'admin/system_config.html', context)

@login_required
@user_passes_test(is_admin_check)
def save_master_data(request, model_type, pk=None):
    if request.method == 'POST':
        config_map = {
            'tinh-thanh': (TinhThanh, TinhThanhForm, 'tinh-thanh'),
            'loai-vat-dung': (LoaiVatDung, LoaiVatDungForm, 'loai-vat-dung'),
            'vat-dung': (VatDung, VatDungForm, 'vat-dung'),
            'the': (The, TheForm, 'the'),
        }

        if model_type in config_map:
            ModelClass, FormClass, tab = config_map[model_type]
            
            if pk:
                item = get_object_or_404(ModelClass, pk=pk)
                form = FormClass(request.POST, instance=item)
                msg = 'Cập nhật thành công!'
            else:
                form = FormClass(request.POST)
                msg = 'Thêm mới thành công!'

            if form.is_valid():
                instance = form.save(commit=False)
                if hasattr(instance, 'slug') and hasattr(instance, 'ten'):
                    if not instance.slug:
                        instance.slug = slugify(instance.ten)
                instance.save()
                messages.success(request, msg)
            else:
                for field, errors in form.errors.items():
                    messages.error(request, f"Lỗi {field}: {', '.join(errors)}")
        
        return redirect(f'/system-configuration/?tab={tab}')
    return redirect('system_config')

@login_required
@user_passes_test(is_admin_check)
def delete_master_data(request, model_type, pk):
    if request.method == 'POST':
        model_map = {
            'tinh-thanh': (TinhThanh, 'tinh-thanh'),
            'loai-vat-dung': (LoaiVatDung, 'loai-vat-dung'),
            'vat-dung': (VatDung, 'vat-dung'),
            'the': (The, 'the'),
        }

        if model_type in model_map:
            ModelClass, tab = model_map[model_type]
            try:
                item = get_object_or_404(ModelClass, pk=pk)
                item.delete()
                messages.success(request, 'Đã xóa thành công!')
            except Exception as e:
                messages.error(request, f'Lỗi: {str(e)}')
            return redirect(f'/system-configuration/?tab={tab}')
            
    return redirect('system_config')
