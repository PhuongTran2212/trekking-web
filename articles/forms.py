# articles/forms.py
from django import forms
from tinymce.widgets import TinyMCE
from .models import BaiHuongDan, ChuyenMuc

class ChuyenMucForm(forms.ModelForm):
    class Meta:
        model = ChuyenMuc
        fields = ['ten']
        widgets = {
            'ten': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BaiHuongDanAdminForm(forms.ModelForm):
    # Ghi đè trường noi_dung để sử dụng widget TinyMCE
    noi_dung = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
        label="Nội dung chi tiết"
    )

    class Meta:
        model = BaiHuongDan
        # Chỉ định các trường sẽ hiển thị trong form
        fields = ['tieu_de', 'chuyen_muc', 'noi_dung']
        labels = {
            'tieu_de': 'Tiêu đề bài viết',
            'chuyen_muc': 'Chọn chuyên mục',
        }
        widgets = {
            'tieu_de': forms.TextInput(attrs={'placeholder': 'Nhập tiêu đề...'}),
            # Select2 có thể được tích hợp để làm đẹp hơn, nhưng tạm thời dùng select mặc định
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tự động thêm class 'form-control' cho các trường
        for field_name, field in self.fields.items():
            if field_name != 'noi_dung': # Bỏ qua trường TinyMCE
                field.widget.attrs['class'] = 'form-control'