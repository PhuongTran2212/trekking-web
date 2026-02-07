# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
<<<<<<< HEAD

from .models import TaiKhoanHoSo, TaiKhoanThietBiCaNhan, GioiTinh
from core.models import The, LoaiVatDung, VatDung

# ==============================================================================
# FORM ĐĂNG KÝ (KHÔNG THAY ĐỔI)
# ==============================================================================
class DangKyForm(UserCreationForm):
    """
    Form tùy chỉnh để đăng ký người dùng mới, bao gồm các thông tin
    mở rộng cho hồ sơ (TaiKhoanHoSo) ngay từ đầu.
    """
=======
from .models import TaiKhoanHoSo

class DangKyForm(UserCreationForm):
    # Định nghĩa lại thứ tự các trường sẽ hiển thị trên form
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
    email = forms.EmailField(
        required=True,
        help_text='Bắt buộc. Dùng để xác thực và khôi phục tài khoản.'
    )
<<<<<<< HEAD
=======
    # <-- Di chuyển trường sdt lên đây, ngay sau email
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
    sdt = forms.CharField(
        label='Số điện thoại',
        max_length=15,
        required=True
    )
<<<<<<< HEAD
    ngay_sinh = forms.DateField(
        label='Ngày sinh',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    gioi_tinh = forms.ChoiceField(
        label='Giới tính',
        required=False,
        choices=GioiTinh.choices, 
        widget=forms.RadioSelect
    )
    first_name = forms.CharField(
        label='Tên',
        max_length=150,
        required=True
=======
    first_name = forms.CharField(
        label='Tên',
        max_length=150,
        required=False
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
    )
    last_name = forms.CharField(
        label='Họ',
        max_length=150,
<<<<<<< HEAD
        required=True
=======
        required=False
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_sdt(self):
        sdt_data = self.cleaned_data.get('sdt')
<<<<<<< HEAD
        if sdt_data and TaiKhoanHoSo.objects.filter(sdt=sdt_data).exists():
            raise forms.ValidationError("Số điện thoại này đã được sử dụng.")
=======
        if TaiKhoanHoSo.objects.filter(sdt=sdt_data).exists():
            raise forms.ValidationError("Số điện thoại này đã được sử dụng bởi một tài khoản khác.")
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
        return sdt_data

    def clean_email(self):
        email_data = self.cleaned_data.get('email')
        if User.objects.filter(email=email_data).exists():
<<<<<<< HEAD
            raise forms.ValidationError("Địa chỉ email này đã được sử dụng.")
=======
            raise forms.ValidationError("Địa chỉ email này đã được sử dụng bởi một tài khoản khác.")
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
        return email_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
<<<<<<< HEAD
            profile = user.taikhoanhoso
            profile.sdt = self.cleaned_data.get('sdt')
            profile.ngay_sinh = self.cleaned_data.get('ngay_sinh')
            profile.gioi_tinh = self.cleaned_data.get('gioi_tinh')
            profile.save()
        return user

# ==============================================================================
# CÁC FORM CẬP NHẬT (KHÔNG THAY ĐỔI)
# ==============================================================================
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = TaiKhoanHoSo
        fields = ['anh_dai_dien', 'sdt', 'ngay_sinh', 'gioi_tinh', 'gioi_thieu', 'tinh_thanh']
        widgets = {
            'gioi_thieu': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Chia sẻ về kinh nghiệm trekking của bạn...'}),
            'ngay_sinh': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tinh_thanh'].empty_label = "--- Chọn Tỉnh/Thành phố ---"
        self.fields['gioi_tinh'].empty_label = "--- Chọn giới tính ---"

class InterestsUpdateForm(forms.Form):
    interests = forms.CharField(
        label="Sở thích của bạn",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nhập và chọn các sở thích...'})
    )
    
# ==============================================================================
# === SỬA LẠI FORM THIẾT BỊ Ở ĐÂY ===
# ==============================================================================
class EquipmentForm(forms.ModelForm):
    # Thêm trường này để người dùng chọn loại trước
    loai_vat_dung = forms.ModelChoiceField(
        queryset=LoaiVatDung.objects.all(),
        label="Chọn loại vật dụng",
        required=True # Bắt buộc phải chọn loại trước
    )

    class Meta:
        model = TaiKhoanThietBiCaNhan
        # Sắp xếp lại thứ tự fields cho logic
        fields = ['loai_vat_dung', 'vat_dung', 'so_luong', 'ghi_chu']
        labels = {
            'vat_dung': 'Chọn thiết bị',
            'so_luong': 'Số lượng',
            'ghi_chu': 'Ghi chú (ví dụ: size, màu sắc...)'
        }
        
    # === HÀM __init__ ĐÃ ĐƯỢC DI CHUYỂN RA ĐÚNG VỊ TRÍ ===
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ban đầu, dropdown vật dụng sẽ trống, chờ người dùng chọn loại
        self.fields['vat_dung'].queryset = VatDung.objects.none()

        # Nếu form được post đi (có data), chúng ta cần đảm bảo
        # dropdown vật dụng có các lựa chọn đúng để validation hoạt động
        if 'loai_vat_dung' in self.data:
            try:
                category_id = int(self.data.get('loai_vat_dung'))
                self.fields['vat_dung'].queryset = VatDung.objects.filter(loai_vat_dung_id=category_id).order_by('ten')
            except (ValueError, TypeError):
                pass  # Bỏ qua nếu có lỗi (ví dụ người dùng chưa chọn)
        elif self.instance.pk:
            # Nếu đang sửa một instance đã có (ít dùng cho form này nhưng vẫn nên có)
            self.fields['vat_dung'].queryset = self.instance.vat_dung.loai_vat_dung.vatdung_set.order_by('ten')


class EquipmentEditForm(forms.ModelForm):
    """Form chuyên dụng để SỬA một món đồ đã có."""
    class Meta:
        model = TaiKhoanThietBiCaNhan
        fields = ['so_luong', 'ghi_chu']
        labels = {
            'so_luong': 'Số lượng mới',
            'ghi_chu': 'Ghi chú mới'
        }
=======

        sdt = self.cleaned_data.get('sdt')
        if sdt:
            user.taikhoanhoso.sdt = sdt
            user.taikhoanhoso.save()

        return user
  
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
