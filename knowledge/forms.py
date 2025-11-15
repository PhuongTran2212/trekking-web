# knowledge/forms.py
from django import forms
from articles.models import BaiHuongDan

class ContributionForm(forms.ModelForm):
    class Meta:
        model = BaiHuongDan
        # 'chuyen_muc' giờ sẽ là một dropdown
        fields = ['tieu_de', 'chuyen_muc', 'noi_dung']
        widgets = {
            'tieu_de': forms.TextInput(attrs={'placeholder': 'Ví dụ: Kinh nghiệm chuẩn bị trekking Tà Năng'}),
            # không cần widget cho chuyen_muc nữa, Django sẽ tự tạo dropdown
            'noi_dung': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Chia sẻ chi tiết kiến thức của bạn tại đây...'}),
        }

    # Thêm hàm này để có dòng chữ "--- Chọn chuyên mục ---"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chuyen_muc'].empty_label = "--- Vui lòng chọn một chuyên mục ---"