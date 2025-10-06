# cSpell:disable

from django import forms
from .models import CongDongBaiViet, CongDongBinhLuan
from core.models import The
from trips.models import ChuyenDi
from .models import CongDongMediaBaiViet

class BaiVietForm(forms.ModelForm):
    """Form tạo/chỉnh sửa bài viết"""

    # Trường tags đã được định nghĩa đúng với widget CheckboxSelectMultiple
    tags = forms.ModelMultipleChoiceField(
        queryset=The.objects.all().order_by('ten'), # Lấy tất cả các thẻ từ CSDL
        widget=forms.CheckboxSelectMultiple,
        label="Chọn các thẻ phù hợp",
        required=False
    )
    
    class Meta:
        model = CongDongBaiViet
        # === THAY ĐỔI QUAN TRỌNG: Thêm 'tags' vào danh sách fields ===
        fields = ['tieu_de', 'noi_dung', 'chuyen_di', 'tags']
        # ==============================================================
        widgets = {
            'tieu_de': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tiêu đề bài viết...',
            }),
            'noi_dung': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Chia sẻ trải nghiệm của bạn...',
                'rows': 8,
            }),
            'chuyen_di': forms.Select(attrs={
                'class': 'form-select',
            })
        }
        labels = {
            'tieu_de': 'Tiêu đề',
            'noi_dung': 'Nội dung',
            'chuyen_di': 'Chuyến đi liên quan (nếu có)',
        }
    
    def clean_tieu_de(self):
        tieu_de = self.cleaned_data.get('tieu_de')
        if len(tieu_de) < 10:
            raise forms.ValidationError('Tiêu đề phải có ít nhất 10 ký tự.')
        return tieu_de
    
    def clean_noi_dung(self):
        noi_dung = self.cleaned_data.get('noi_dung')
        if len(noi_dung) < 50:
            raise forms.ValidationError('Nội dung phải có ít nhất 50 ký tự.')
        return noi_dung


class MediaBaiVietForm(forms.ModelForm):
    """Form upload media cho bài viết"""
    
    class Meta:
        model = CongDongMediaBaiViet
        fields = ['loai_media', 'duong_dan_file']
        widgets = {
            'loai_media': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duong_dan_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*'
            })
        }


class BinhLuanForm(forms.ModelForm):
    """Form bình luận"""
    
    class Meta:
        model = CongDongBinhLuan
        fields = ['noi_dung']
        widgets = {
            'noi_dung': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Viết bình luận...',
                'rows': 3,
                'required': True
            })
        }
        labels = {
            'noi_dung': ''
        }
    
    def clean_noi_dung(self):
        noi_dung = self.cleaned_data.get('noi_dung')
        if len(noi_dung) < 5:
            raise forms.ValidationError('Bình luận phải có ít nhất 5 ký tự.')
        return noi_dung