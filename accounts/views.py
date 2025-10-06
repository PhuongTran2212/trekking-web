# accounts/views.py

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
    """
    View hiển thị trang hồ sơ chi tiết (CV Trekking).
    Tên hàm này khớp với `urls.py` của bạn.
    """
    profile_user = get_object_or_404(User, username=username)
    is_own_profile = request.user == profile_user

    # Lấy các dữ liệu liên quan
    trips_joined = ChuyenDiThanhVien.objects.filter(user=profile_user, trang_thai_tham_gia='Đã duyệt').order_by('-chuyen_di__ngay_bat_dau')
    badges_earned = GameHuyHieuNguoiDung.objects.filter(user=profile_user).order_by('-ngay_dat_duoc')
    posts_created = CongDongBaiViet.objects.filter(tac_gia=profile_user)
    user_interests = TaiKhoanSoThichNguoiDung.objects.filter(user=profile_user).select_related('the')
    
    # Lấy và gom nhóm thiết bị cá nhân theo loại vật dụng
    # THAY THẾ LOGIC CŨ BẰNG LOGIC GOM NHÓM MỚI
    personal_equipment_list = TaiKhoanThietBiCaNhan.objects.filter(
    ).select_related('vat_dung', 'vat_dung__loai_vat_dung').order_by('vat_dung__loai_vat_dung__ten', 'vat_dung__ten')

    grouped_equipment = {}
    for item in personal_equipment_list:
        category = item.vat_dung.loai_vat_dung
        if category not in grouped_equipment:
            grouped_equipment[category] = []
        grouped_equipment[category].append(item)
    # KẾT THÚC LOGIC GOM NHÓM

    # Lấy danh sách tất cả các tag sở thích (all_tags_list)
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