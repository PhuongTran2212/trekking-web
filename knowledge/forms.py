# knowledge/forms.py
from django import forms
# Quan trọng: Import model từ app articles
from articles.models import BaiHuongDan

class ContributionForm(forms.ModelForm):
    class Meta:
        model = BaiHuongDan
        # Chỉ cho người dùng nhập 3 trường này
        fields = ['tieu_de', 'chuyen_muc', 'noi_dung']
        widgets = {
            'tieu_de': forms.TextInput(attrs={'placeholder': 'Ví dụ: Kinh nghiệm chuẩn bị trekking Tà Năng'}),
            'chuyen_muc': forms.TextInput(attrs={'placeholder': 'Ví dụ: Kỹ năng sinh tồn, Chuẩn bị vật dụng...'}),
            'noi_dung': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Chia sẻ chi tiết kiến thức của bạn tại đây...'}),
        }