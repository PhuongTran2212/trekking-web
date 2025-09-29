# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction

# === THAY ĐỔI: Import 'GioiTinh' trực tiếp để tái sử dụng ===
from .models import TaiKhoanHoSo, TaiKhoanThietBiCaNhan, GioiTinh
from core.models import The # Giả định bạn sẽ cần cho InterestsForm sau này

# ==============================================================================
# FORM ĐĂNG KÝ TÀI KHOẢN MỚI
# ==============================================================================
class DangKyForm(UserCreationForm):
    """
    Form tùy chỉnh để đăng ký người dùng mới, bao gồm các thông tin
    mở rộng cho hồ sơ (TaiKhoanHoSo) ngay từ đầu.
    """
    email = forms.EmailField(
        required=True,
        help_text='Bắt buộc. Dùng để xác thực và khôi phục tài khoản.'
    )
    sdt = forms.CharField(
        label='Số điện thoại',
        max_length=15,
        required=True
    )
    ngay_sinh = forms.DateField(
        label='Ngày sinh',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    gioi_tinh = forms.ChoiceField(
        label='Giới tính',
        required=False,
        # === TINH CHỈNH: Tham chiếu trực tiếp tới class GioiTinh ===
        choices=GioiTinh.choices, 
        widget=forms.RadioSelect
    )
    first_name = forms.CharField(
        label='Tên',
        max_length=150,
        required=True
    )
    last_name = forms.CharField(
        label='Họ',
        max_length=150,
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_sdt(self):
        sdt_data = self.cleaned_data.get('sdt')
        if sdt_data and TaiKhoanHoSo.objects.filter(sdt=sdt_data).exists():
            raise forms.ValidationError("Số điện thoại này đã được sử dụng.")
        return sdt_data

    def clean_email(self):
        email_data = self.cleaned_data.get('email')
        if User.objects.filter(email=email_data).exists():
            raise forms.ValidationError("Địa chỉ email này đã được sử dụng.")
        return email_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile = user.taikhoanhoso
            profile.sdt = self.cleaned_data.get('sdt')
            profile.ngay_sinh = self.cleaned_data.get('ngay_sinh')
            profile.gioi_tinh = self.cleaned_data.get('gioi_tinh')
            profile.save()
        return user
# --- CÁC FORM MỚI CHO VIỆC CẬP NHẬT PROFILE ---

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

# === THAY ĐỔI TẠI ĐÂY: Sửa lại ProfileUpdateForm ===
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = TaiKhoanHoSo
        # Thêm 'ngay_sinh' và 'gioi_tinh' vào danh sách fields
        fields = ['anh_dai_dien', 'sdt', 'ngay_sinh', 'gioi_tinh', 'gioi_thieu', 'tinh_thanh']
        widgets = {
            'gioi_thieu': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Chia sẻ về kinh nghiệm trekking của bạn...'}),
            # Thêm widgets cho các trường mới để có giao diện tốt hơn
            'ngay_sinh': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tinh_thanh'].empty_label = "--- Chọn Tỉnh/Thành phố ---"
        self.fields['gioi_tinh'].empty_label = "--- Chọn giới tính ---"
# === KẾT THÚC THAY ĐỔI ===


# === THAY ĐỔI TẠI ĐÂY: Form sở thích sẽ nhận chuỗi JSON từ Tagify ===
class InterestsUpdateForm(forms.Form):
    interests = forms.CharField(
        label="Sở thích của bạn",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nhập và chọn các sở thích...'})
    )

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = TaiKhoanThietBiCaNhan
        fields = ['vat_dung', 'so_luong', 'ghi_chu']
        labels = {
            'vat_dung': 'Chọn thiết bị',
            'so_luong': 'Số lượng',
            'ghi_chu': 'Ghi chú (ví dụ: size, màu sắc...)'
        }
        # === THÊM FORM MỚI NÀY VÀO CUỐI FILE ===
class EquipmentEditForm(forms.ModelForm):
    """Form chuyên dụng để SỬA một món đồ đã có."""
    class Meta:
        model = TaiKhoanThietBiCaNhan
        # Chỉ cho phép sửa số lượng và ghi chú
        fields = ['so_luong', 'ghi_chu']
        labels = {
            'so_luong': 'Số lượng mới',
            'ghi_chu': 'Ghi chú mới'
        }