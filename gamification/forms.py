from django import forms
from .models import GameHuyHieu

class GameHuyHieuForm(forms.ModelForm):
    class Meta:
        model = GameHuyHieu
        fields = [
            'ten', 'mo_ta', 'anh_huy_hieu', 
            'loai_dieu_kien', 'gia_tri_muc_tieu', 
              'bien_so_phu', 'is_active'
        ]
        widgets = {
            'ten': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên huy hiệu'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'anh_huy_hieu': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'loai_dieu_kien': forms.Select(attrs={'class': 'form-select'}),
            'gia_tri_muc_tieu': forms.NumberInput(attrs={'class': 'form-control'}),
            'bien_so_phu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: san-may, kho (nếu cần)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'anh_huy_hieu': 'Đường dẫn ảnh/Icon',
            'is_active': 'Kích hoạt ngay?'
        }