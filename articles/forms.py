# articles/forms.py
from django import forms
from .models import BaiHuongDan, ChuyenMuc
class BaiHuongDanAdminForm(forms.ModelForm):
    class Meta:
        model = BaiHuongDan
        fields = ['tieu_de', 'chuyen_muc', 'noi_dung']

class ChuyenMucForm(forms.ModelForm):
    class Meta:
        model = ChuyenMuc
        # Slug sẽ được tự động tạo, nên chỉ cần field 'ten'
        fields = ['ten']
        widgets = {
            'ten': forms.TextInput(attrs={
                'placeholder': 'Ví dụ: Kỹ năng sinh tồn, Chuẩn bị vật dụng...'
            })
        }