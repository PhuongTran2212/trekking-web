from django import forms
from .models import CongDongBaiViet, CongDongBinhLuan, CongDongMediaBaiViet
from core.models import The
from core.models import HeThongBaoCao
# Không cần import ChuyenDi nữa vì đã loại bỏ trường đó
# from trips.models import ChuyenDi 

class BaiVietForm(forms.ModelForm):
    """Form tạo/chỉnh sửa bài viết"""

    tags = forms.ModelMultipleChoiceField(
        queryset=The.objects.all().order_by('ten'),
        widget=forms.CheckboxSelectMultiple,
        label="Chọn các thẻ phù hợp",
        required=False
    )
    
    class Meta:
        model = CongDongBaiViet
        # === THAY ĐỔI: Đã loại bỏ 'chuyen_di' khỏi danh sách fields ===
        fields = ['tieu_de', 'noi_dung', 'tags']
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
            # Widget cho 'chuyen_di' đã được xóa
        }
        labels = {
            'tieu_de': 'Tiêu đề',
            'noi_dung': 'Nội dung',
            # Label cho 'chuyen_di' đã được xóa
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
    
class BaoCaoForm(forms.ModelForm):
    """Form để người dùng nhập lý do báo cáo."""
    class Meta:
        model = HeThongBaoCao
        fields = ['ly_do_bao_cao']
        widgets = {
            'ly_do_bao_cao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Vui lòng mô tả chi tiết lý do bạn báo cáo nội dung này...',
                'rows': 5,
                'required': True,
            })
        }
        labels = {
            'ly_do_bao_cao': 'Lý do báo cáo'
        }