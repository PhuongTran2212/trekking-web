# accounts/views.py

<<<<<<< HEAD
import json
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction

# --- IMPORT MODELS ---
# Trips
from trips.models import ChuyenDiThanhVien, ChuyenDi
# Gamification
from gamification.models import GameHuyHieuNguoiDung
# Community
from community.models import CongDongBaiViet
# Core & Accounts
from core.models import The, VatDung
from .models import TaiKhoanHoSo, TaiKhoanThietBiCaNhan, TaiKhoanSoThichNguoiDung

# --- IMPORT FORMS ---
from .forms import (
    DangKyForm,
    UserUpdateForm, 
    ProfileUpdateForm, 
    InterestsUpdateForm, 
    EquipmentForm,
    EquipmentEditForm
)

# ===================================================
# === 1. AUTHENTICATION (Đăng ký / Đăng nhập) ===
# ===================================================

def home_view(request):
    """View cho trang chủ với dữ liệu động."""
    from treks.models import CungDuongTrek
    from trips.models import ChuyenDi
    from community.models import CongDongBaiViet
    from knowledge.models import KienThucBaiHuongDan
    from django.db.models import Count, Q
    from django.utils import timezone
    
    # 1. Featured Treks - Top 4 cung đường có rating cao nhất
    featured_treks = CungDuongTrek.objects.filter(
        trang_thai='DA_DUYET'
    ).select_related(
        'tinh_thanh', 'do_kho'
    ).order_by('-danh_gia_trung_binh', '-so_luot_danh_gia')[:4]
    
    # 2. Upcoming Trips - 6 chuyến đi sắp khởi hành
    now = timezone.now()
    upcoming_trips = ChuyenDi.objects.filter(
        trang_thai='DANG_TUYEN',
        ngay_bat_dau__gte=now,
        che_do_rieng_tu='CONG_KHAI'
    ).select_related(
        'nguoi_to_chuc', 
        'nguoi_to_chuc__taikhoanhoso',
        'cung_duong',
        'cung_duong__tinh_thanh'
    ).annotate(
        so_thanh_vien_tham_gia=Count(
            'thanh_vien',
            filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA')
        )
    )

    # Annotate user_status nếu đã đăng nhập (để hiển thị nút Tham gia/Chờ duyệt đúng)
    if request.user.is_authenticated:
        from django.db.models import OuterRef, Subquery
        status_subquery = ChuyenDiThanhVien.objects.filter(
            chuyen_di=OuterRef('pk'),
            user=request.user
        ).values('trang_thai_tham_gia')[:1]
        
        upcoming_trips = upcoming_trips.annotate(
            user_status=Subquery(status_subquery)
        )
        
    upcoming_trips = upcoming_trips.order_by('ngay_bat_dau')[:6]
    
    # 3. Community Highlights - 3 bài viết mới nhất
    community_posts = CongDongBaiViet.objects.filter(
        trang_thai='DA_DUYET'
    ).select_related(
        'tac_gia',
        'tac_gia__taikhoanhoso'
    ).order_by('-ngay_dang')[:3]
    
    # 4. Knowledge Articles - 4 bài viết kiến thức mới nhất
    knowledge_articles = KienThucBaiHuongDan.objects.select_related(
        'tac_gia', 'tac_gia__taikhoanhoso'
    ).order_by('-ngay_dang')[:4]
    
    context = {
        'featured_treks': featured_treks,
        'upcoming_trips': upcoming_trips,
        'community_posts': community_posts,
        'knowledge_articles': knowledge_articles,
    }
    
    return render(request, 'home.html', context)

def dang_ky_view(request):
    """View xử lý việc đăng ký tài khoản."""
    if request.user.is_authenticated:
        return redirect('home')
    
=======
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .forms import DangKyForm
from django.urls import reverse_lazy

# Thêm một view cho trang chủ
def home_view(request):
    return render(request, 'home.html')

def dang_ky_view(request):
    if request.user.is_authenticated:
        return redirect('home') # Nếu đã đăng nhập, về trang chủ

>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
    if request.method == 'POST':
        form = DangKyForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Tạo tài khoản thành công! Chào mừng {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin đăng ký.")
    else:
        form = DangKyForm()
    return render(request, 'accounts/dang_ky.html', {'form': form})

class CustomLoginView(LoginView):
<<<<<<< HEAD
    """View xử lý việc đăng nhập."""
    template_name = 'accounts/dang_nhap.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        messages.success(self.request, f"Đăng nhập thành công! Chào mừng, {user.username}.")
        if user.is_staff:
            return reverse_lazy('admin_dashboard')
        else:
            return reverse_lazy('home')
            
    def form_invalid(self, form):
        messages.error(self.request, "Tên đăng nhập hoặc mật khẩu không đúng.")
        return super().form_invalid(form)


# ===================================================
# === 2. PROFILE VIEW (Xem chi tiết hồ sơ) ===
# ===================================================

@login_required
def profile_view(request, username):
    """
    View hiển thị trang hồ sơ chi tiết (CV Trekking).
    """
    # 1. Lấy user object
    profile_user = get_object_or_404(User, username=username)
    is_own_profile = (request.user == profile_user)

    # 2. Lấy Lịch sử chuyến đi
    # Lưu ý: Kiểm tra lại model ChuyenDiThanhVien của bạn dùng 'Đã duyệt' hay 'DA_DUYET'
    # Ở đây tôi giữ theo code mới nhất bạn gửi là 'Đã duyệt'
    trips_joined = ChuyenDiThanhVien.objects.filter(
        user=profile_user, 
        trang_thai_tham_gia='Đã duyệt'
    ).select_related(
        'chuyen_di', 
        'chuyen_di__cung_duong',
        'chuyen_di__cung_duong__tinh_thanh'
    ).order_by('-chuyen_di__ngay_bat_dau')

    # 3. Lấy Huy hiệu & Thành tích
    badges_earned = GameHuyHieuNguoiDung.objects.filter(
        user=profile_user
    ).select_related('huy_hieu').order_by('-ngay_dat_duoc')

    # 4. Lấy Bài viết đã đăng (Logic mới nhất)
    posts_created = CongDongBaiViet.objects.filter(
        tac_gia=profile_user
    ).order_by('-ngay_dang')

    # 5. Lấy Sở thích
    user_interests = TaiKhoanSoThichNguoiDung.objects.filter(
        user=profile_user
    ).select_related('the')
    
    # 6. Lấy & Gom nhóm Thiết bị cá nhân
    # Sửa lỗi: Thêm filter(user=profile_user) để không lấy nhầm đồ của người khác
    personal_equipment_list = TaiKhoanThietBiCaNhan.objects.filter(
        user=profile_user
    ).select_related(
        'vat_dung', 'vat_dung__loai_vat_dung'
    ).order_by('vat_dung__loai_vat_dung__ten', 'vat_dung__ten')

    grouped_equipment = {}
    for item in personal_equipment_list:
        category = item.vat_dung.loai_vat_dung
        if category not in grouped_equipment:
            grouped_equipment[category] = []
        grouped_equipment[category].append(item)

    # 7. Danh sách Tags cho JS (nếu cần)
    all_tags_list = list(The.objects.values_list('ten', flat=True))

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'trips_joined': trips_joined,
        'badges_earned': badges_earned,
        'posts_created': posts_created,
        'user_interests': user_interests,
        'grouped_equipment': grouped_equipment,
        'all_tags_whitelist': json.dumps(all_tags_list),
        'now': timezone.now(), # Để so sánh ngày tháng trong template
    }
    return render(request, 'accounts/profile_detail.html', context)


# ===================================================
# === 3. PROFILE UPDATE (Cập nhật hồ sơ) ===
# ===================================================

@login_required
def profile_update_view(request):
    """
    View xử lý việc cập nhật hồ sơ cá nhân (Thông tin, Sở thích, Thiết bị).
    """
    user = request.user
    profile = user.taikhoanhoso

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # --- Xử lý form Thông tin cơ bản ---
        if form_type == 'basic_info':
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Cập nhật thông tin chung thành công!')
                return redirect('accounts:profile-update')

        # --- Xử lý form Sở thích (Tags) ---
        elif form_type == 'interests':
            interests_form = InterestsUpdateForm(request.POST)
            if interests_form.is_valid():
                interests_json_string = interests_form.cleaned_data.get('interests', '[]')
                try:
                    interests_data = json.loads(interests_json_string)
                    interest_names = [item['value'] for item in interests_data]
                    
                    with transaction.atomic():
                        TaiKhoanSoThichNguoiDung.objects.filter(user=user).delete()
                        new_interests = [
                            TaiKhoanSoThichNguoiDung(user=user, the=The.objects.get_or_create(ten=name)[0])
                            for name in interest_names
                        ]
                        TaiKhoanSoThichNguoiDung.objects.bulk_create(new_interests)
                    messages.success(request, 'Cập nhật sở thích thành công!')
                except json.JSONDecodeError:
                    messages.error(request, 'Dữ liệu sở thích không hợp lệ.')
                return redirect('accounts:profile-update')

        # --- Xử lý form Thêm thiết bị ---
        elif form_type == 'add_equipment':
            equipment_form = EquipmentForm(request.POST)
            if equipment_form.is_valid():
                # Dùng update_or_create để tránh trùng lặp vật dụng
                obj, created = TaiKhoanThietBiCaNhan.objects.update_or_create(
                    user=user, 
                    vat_dung=equipment_form.cleaned_data['vat_dung'],
                    defaults={
                        'so_luong': equipment_form.cleaned_data['so_luong'],
                        'ghi_chu': equipment_form.cleaned_data.get('ghi_chu', '')
                    }
                )
                msg = f'Đã thêm "{obj.vat_dung.ten}".' if created else f'Đã cập nhật "{obj.vat_dung.ten}".'
                messages.success(request, msg)
                return redirect('accounts:profile-update')

    # --- GET REQUEST: Khởi tạo các form ---
    user_form = UserUpdateForm(instance=user)
    profile_form = ProfileUpdateForm(instance=profile)
    
    # Chuẩn bị dữ liệu Tags cho Tagify
    all_tags_list = list(The.objects.values_list('ten', flat=True))
    current_user_tags = TaiKhoanSoThichNguoiDung.objects.filter(user=user).select_related('the')
    current_user_tags_json = json.dumps([{'value': item.the.ten} for item in current_user_tags])
    interests_form = InterestsUpdateForm(initial={'interests': current_user_tags_json})
    
    # Form thiết bị & Danh sách hiện có
    equipment_form = EquipmentForm()
    personal_equipment = TaiKhoanThietBiCaNhan.objects.filter(user=user).select_related('vat_dung') 
    
    context = {
        'user_form': user_form, 
        'profile_form': profile_form,
        'interests_form': interests_form, 
        'equipment_form': equipment_form,
        'personal_equipment': personal_equipment,
        'all_tags_whitelist': json.dumps(all_tags_list),
    }
    return render(request, 'accounts/profile_update.html', context)


# ===================================================
# === 4. EQUIPMENT ACTIONS (Xóa / Sửa thiết bị) ===
# ===================================================

@login_required
def delete_equipment_view(request, pk):
    """View xử lý việc xóa một món đồ."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")
    
    equipment_item = get_object_or_404(TaiKhoanThietBiCaNhan, pk=pk, user=request.user)
    item_name = equipment_item.vat_dung.ten
    equipment_item.delete()
    
    messages.success(request, f'Đã xóa "{item_name}" khỏi kho đồ của bạn.')
    return redirect('accounts:profile-update')


@login_required
def edit_equipment_view(request, pk):
    """View xử lý việc cập nhật thông tin một món đồ qua Modal."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")
    
    equipment_item = get_object_or_404(TaiKhoanThietBiCaNhan, pk=pk, user=request.user)
    form = EquipmentEditForm(request.POST, instance=equipment_item)
    
    if form.is_valid():
        form.save()
        messages.success(request, f'Đã cập nhật thành công "{equipment_item.vat_dung.ten}".')
    else:
        error_field, error_messages = next(iter(form.errors.items()))
        messages.error(request, f"Lỗi cập nhật: {error_messages[0]}")
        
    return redirect('accounts:profile-update')


# ===================================================
# === 5. API VIEWS (AJAX) ===
# ===================================================

@login_required
def get_equipment_by_category(request):
    """
    API trả về danh sách vật dụng theo loại (dùng cho dropdown phụ thuộc).
    """
    category_id = request.GET.get('category_id')
    if category_id:
        try:
            equipment = VatDung.objects.filter(
                loai_vat_dung_id=category_id
            ).values('id', 'ten').order_by('ten')
            return JsonResponse(list(equipment), safe=False)
        except (ValueError, TypeError):
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)
=======
    template_name = 'accounts/dang_nhap.html'
    redirect_authenticated_user = True

   
    def get_success_url(self):
        user = self.request.user
        messages.success(self.request, f"Đăng nhập thành công! Chào mừng trở lại, {user.username}.")

        # Nếu user là staff/admin, chuyển hướng đến trang Dashboard
        if user.is_staff:
            return reverse_lazy('admin_dashboard')
        
        # THAY ĐỔI TẠI ĐÂY: Nếu là người dùng thường, chuyển hướng về trang chủ
        else:
            return reverse_lazy('home')
        
    def form_invalid(self, form):
        messages.error(self.request, "Tên đăng nhập hoặc mật khẩu không đúng.")
        return super().form_invalid(form)
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
