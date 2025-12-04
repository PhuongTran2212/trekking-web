# accounts/views.py
from django.utils import timezone
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction

# Import Models
from trips.models import ChuyenDiThanhVien
from gamification.models import GameHuyHieuNguoiDung
from community.models import CongDongBaiViet
from .models import TaiKhoanThietBiCaNhan, TaiKhoanSoThichNguoiDung
from core.models import The, VatDung
from .models import TaiKhoanHoSo, TaiKhoanThietBiCaNhan
# Giả sử app trips của bạn tên là 'trips'
from trips.models import ChuyenDiThanhVien, ChuyenDi
# Import Forms
from .forms import (
    DangKyForm,
    UserUpdateForm, 
    ProfileUpdateForm, 
    InterestsUpdateForm, 
    EquipmentForm,
    EquipmentEditForm
)

# ===================================================
# === CÁC VIEW CƠ BẢN ĐÃ ĐƯỢC THÊM LẠI VÀO ĐÂY ===
# ===================================================

def home_view(request):
    """
    View cho trang chủ.
    """
    return render(request, 'home.html')

def dang_ky_view(request):
    """
    View xử lý việc đăng ký tài khoản.
    """
    if request.user.is_authenticated:
        return redirect('home')
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
    """
    View xử lý việc đăng nhập.
    """
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
# === CÁC VIEW CHO CHỨC NĂNG PROFILE ===
# ===================================================

@login_required
def profile_view(request, username):
    # 1. Lấy user object từ username trên URL
    profile_user = get_object_or_404(User, username=username)
    
    # 2. Kiểm tra xem người xem có phải là chủ sở hữu hồ sơ không
    is_own_profile = (request.user == profile_user)
    
    # =========================================================
    # PHẦN 1: LỊCH SỬ CHUYẾN ĐI (Trips History)
    # =========================================================
    # Lấy danh sách các chuyến đi mà user đã tham gia (STATUS = DA_THAM_GIA)
    # select_related: Tối ưu query để lấy thông tin Chuyến đi, Cung đường, Người tổ chức cùng lúc
    trips_joined = ChuyenDiThanhVien.objects.filter(
        user=profile_user,
        trang_thai_tham_gia='DA_THAM_GIA'
    ).select_related(
        'chuyen_di',
        'chuyen_di__cung_duong',
        'chuyen_di__cung_duong__tinh_thanh',  # Để hiển thị địa điểm
        'chuyen_di__nguoi_to_chuc__taikhoanhoso' # Để hiển thị avatar host (nếu cần)
    ).order_by('-chuyen_di__ngay_bat_dau')  # Sắp xếp chuyến mới nhất lên đầu

    # =========================================================
    # PHẦN 2: THIẾT BỊ CÁ NHÂN (Equipment)
    # =========================================================
    # Lấy danh sách thiết bị và gom nhóm theo loại (Ba lô, Lều, v.v.)
    personal_equipment = TaiKhoanThietBiCaNhan.objects.filter(
        user=profile_user
    ).select_related('vat_dung', 'vat_dung__loai_vat_dung').order_by('vat_dung__loai_vat_dung__ten', 'vat_dung__ten')

    # Gom nhóm thiết bị để hiển thị đẹp hơn
    grouped_equipment = {}
    for item in personal_equipment:
        category = item.vat_dung.loai_vat_dung
        if category not in grouped_equipment:
            grouped_equipment[category] = []
        grouped_equipment[category].append(item)

    # =========================================================
    # PHẦN 3: SỞ THÍCH (Interests)
    # =========================================================
    # Giả sử sở thích được lưu trong TaiKhoanHoSo thông qua ManyToManyField (VD: tags)
    # Hoặc nếu bạn dùng model riêng, hãy query tương tự
    user_interests = []
    if hasattr(profile_user, 'taikhoanhoso') and profile_user.taikhoanhoso:
        # Ví dụ: user_interests = profile_user.taikhoanhoso.so_thich.all()
        # Dựa trên template của bạn, có vẻ bạn dùng tags
        pass 

    # =========================================================
    # PHẦN 4: DỮ LIỆU KHÁC (Badges, Posts - Placeholder)
    # =========================================================
    # Nếu bạn chưa có model Badge hay Post, tạm thời để trống để tránh lỗi template
    badges_earned = [] # UserBadge.objects.filter(user=profile_user)...
    posts_created = [] # Post.objects.filter(author=profile_user)...

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'trips_joined': trips_joined,      # <-- Dữ liệu quan trọng cho tab Trips
        'grouped_equipment': grouped_equipment,
        'personal_equipment': personal_equipment, # Dùng cho form edit nếu cần
        'user_interests': user_interests,
        'badges_earned': badges_earned,
        'posts_created': posts_created,
        'now': timezone.now(), # Để so sánh ngày tháng (Sắp tới/Đã qua)
    }
    
    return render(request, 'accounts/profile_detail.html', context)


@login_required
def profile_update_view(request):
    """
    View xử lý việc cập nhật hồ sơ cá nhân.
    """
    user = request.user
    profile = user.taikhoanhoso

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'basic_info':
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Cập nhật thông tin chung thành công!')
                return redirect('accounts:profile-update')

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

        elif form_type == 'add_equipment':
            equipment_form = EquipmentForm(request.POST)
            if equipment_form.is_valid():
                obj, created = TaiKhoanThietBiCaNhan.objects.update_or_create(
                    user=user, vat_dung=equipment_form.cleaned_data['vat_dung'],
                    defaults={
                        'so_luong': equipment_form.cleaned_data['so_luong'],
                        'ghi_chu': equipment_form.cleaned_data.get('ghi_chu', '')
                    }
                )
                msg = f'Đã thêm "{obj.vat_dung.ten}".' if created else f'Đã cập nhật "{obj.vat_dung.ten}".'
                messages.success(request, msg)
                return redirect('accounts:profile-update')

    user_form = UserUpdateForm(instance=user)
    profile_form = ProfileUpdateForm(instance=profile)
    
    all_tags_list = list(The.objects.values_list('ten', flat=True))
    current_user_tags = TaiKhoanSoThichNguoiDung.objects.filter(user=user).select_related('the')
    current_user_tags_json = json.dumps([{'value': item.the.ten} for item in current_user_tags])
    interests_form = InterestsUpdateForm(initial={'interests': current_user_tags_json})
    
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


@login_required
def delete_equipment_view(request, pk):
    """
    View xử lý việc xóa một món đồ trong kho cá nhân.
    Tên hàm này khớp với `urls.py` của bạn.
    """
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")
    equipment_item = get_object_or_404(TaiKhoanThietBiCaNhan, pk=pk, user=request.user)
    item_name = equipment_item.vat_dung.ten
    equipment_item.delete()
    messages.success(request, f'Đã xóa "{item_name}" khỏi kho đồ của bạn.')
    return redirect('accounts:profile-update')


@login_required
def edit_equipment_view(request, pk):
    """
    View xử lý việc CẬP NHẬT thông tin một món đồ qua Modal.
    Tên hàm này khớp với `urls.py` của bạn.
    """
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
# === API VIEW CHO AJAX ===
# ===================================================

@login_required
def get_equipment_by_category(request):
    """
    API endpoint trả về danh sách vật dụng (JSON) dựa trên ID loại vật dụng.
    Dùng cho dropdown phụ thuộc.
    """
    category_id = request.GET.get('category_id')
    if category_id:
        try:
            equipment = VatDung.objects.filter(loai_vat_dung_id=category_id).values('id', 'ten').order_by('ten')
            return JsonResponse(list(equipment), safe=False)
        except (ValueError, TypeError):
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)