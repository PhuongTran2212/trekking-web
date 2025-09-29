# treks/forms.py

from django import forms
from core.models import TinhThanh, DoKho
from treks.models import CungDuongTrek

class TrekFilterForm(forms.Form):
    # Dùng CharField cho ô tìm kiếm
    q = forms.CharField(
        label='Tìm kiếm',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Tên, mô tả cung đường...'})
    )

    # Dùng ModelChoiceField để tạo dropdown từ model TinhThanh
    tinh_thanh = forms.ModelChoiceField(
        label='Địa điểm',
        queryset=TinhThanh.objects.all(),
        required=False,
        empty_label="Tất cả địa điểm" # Lựa chọn mặc định
    )

    # Tương tự cho Độ khó
    do_kho = forms.ModelChoiceField(
        label='Độ khó',
        queryset=DoKho.objects.all(),
        required=False,
        empty_label="Tất cả độ khó"
    )

    # Dùng ChoiceField cho các lựa chọn sắp xếp
    SORT_CHOICES = (
        ('', 'Mặc định'),
        ('danh_gia', 'Đánh giá cao nhất'),
        ('do_dai_asc', 'Độ dài tăng dần'),
        ('do_dai_desc', 'Độ dài giảm dần'),
    )
    sort_by = forms.ChoiceField(
        label='Sắp xếp',
        choices=SORT_CHOICES,
        required=False
    )
    # --- FORM MỚI CHO VIỆC THÊM/SỬA ---
class CungDuongTrekForm(forms.ModelForm):
    class Meta:
        model = CungDuongTrek
        # Liệt kê tất cả các trường bạn muốn admin có thể sửa
        fields = [
            'ten', 'slug', 'mo_ta', 'anh_bia', 'tinh_thanh', 'do_dai_km', 
            'thoi_gian_uoc_tinh_gio', 'tong_do_cao_leo_m', 'do_kho', 
            'mua_dep_nhat', 'da_duyet'
        ]
        
        # Thêm class CSS để form đẹp hơn
        widgets = {
            'ten': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'anh_bia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dán URL hình ảnh...'}),
            'tinh_thanh': forms.Select(attrs={'class': 'form-control'}),
            'do_dai_km': forms.NumberInput(attrs={'class': 'form-control'}),
            'thoi_gian_uoc_tinh_gio': forms.NumberInput(attrs={'class': 'form-control'}),
            'tong_do_cao_leo_m': forms.NumberInput(attrs={'class': 'form-control'}),
            'do_kho': forms.Select(attrs={'class': 'form-control'}),
            'mua_dep_nhat': forms.TextInput(attrs={'class': 'form-control'}),
            'da_duyet': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }