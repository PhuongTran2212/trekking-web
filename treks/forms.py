# treks/forms.py (PHIÊN BẢN TỐI GIẢN & CHUẨN XÁC)

from django import forms
from .models import CungDuongTrek, CungDuongDanhGia, CungDuongVatDungGoiY
from core.models import TinhThanh, DoKho, VatDung

class CungDuongTrekAdminForm(forms.ModelForm):
    """
    Form dùng riêng cho trang Admin để tạo và cập nhật CungDuongTrek,
    bao gồm cả việc quản lý các Vật dụng gợi ý.
    """
    vat_dung_goi_y = forms.ModelMultipleChoiceField(
        # =======================================================
        # === ĐÂY LÀ DÒNG ĐÃ ĐƯỢC SỬA LỖI ======================
        # =======================================================
        queryset=VatDung.objects.all().order_by('loai_vat_dung__ten', 'ten'),
        
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Vat dụng gợi ý"
    )

    class Meta:
        model = CungDuongTrek
        # Liệt kê tất cả các trường sẽ hiển thị trên form.
        # 'trang_thai' được bỏ qua vì sẽ được xử lý tự động trong view.
        fields = [
            'ten', 'mo_ta', 'dia_diem_chi_tiet', 'tinh_thanh', 'do_dai_km', 
            'thoi_gian_uoc_tinh_gio', 'tong_do_cao_leo_m', 'do_kho', 
            'mua_dep_nhat', 'du_lieu_ban_do_geojson', 'vat_dung_goi_y'
        ]
        # Tùy chỉnh các widget để thêm class CSS và ID cho JavaScript.
        widgets = {
            'ten': forms.TextInput(attrs={'class': 'form-control'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
                        'dia_diem_chi_tiet': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_dia_diem_chi_tiet', 'placeholder': 'VD: Vườn quốc gia Ba Vì, Hà Nội'}),
            'tinh_thanh': forms.Select(attrs={'class': 'form-control'}),
            'do_dai_km': forms.NumberInput(attrs={'class': 'form-control'}),
            'thoi_gian_uoc_tinh_gio': forms.NumberInput(attrs={'class': 'form-control'}),
            'tong_do_cao_leo_m': forms.NumberInput(attrs={'class': 'form-control'}),
            'do_kho': forms.Select(attrs={'class': 'form-control'}),
            'mua_dep_nhat': forms.TextInput(attrs={'class': 'form-control'}),
            'du_lieu_ban_do_geojson': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'id_geojson', 'readonly': True}),
        }

    def __init__(self, *args, **kwargs):
        """
        Ghi đè __init__ để gán giá trị ban đầu cho trường vật dụng khi chỉnh sửa.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['vat_dung_goi_y'].initial = self.instance.vat_dung_goi_y.all().values_list('vat_dung__pk', flat=True)

    def save(self, commit=True):
        """
        Ghi đè phương thức save để xử lý việc lưu quan hệ many-to-many 
        thông qua model trung gian CungDuongVatDungGoiY.
        """
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            instance.vat_dung_goi_y.all().delete()
            for vat_dung in self.cleaned_data['vat_dung_goi_y']:
                CungDuongVatDungGoiY.objects.create(cung_duong=instance, vat_dung=vat_dung)
            
        return instance

# Form 2: Dùng cho người dùng lọc cung đường (KHÔNG THAY ĐỔI)
class CungDuongFilterForm(forms.Form):
    q = forms.CharField(label="Tìm kiếm", required=False, widget=forms.TextInput(attrs={'placeholder': 'Tên cung đường...'}))
    tinh_thanh = forms.ModelChoiceField(queryset=TinhThanh.objects.all().order_by('ten'), required=False, label="Tỉnh/Thành", empty_label="Tất cả địa phương")
    do_kho = forms.ModelChoiceField(queryset=DoKho.objects.all(), required=False, label="Độ khó", empty_label="Tất cả độ khó")
    min_do_dai = forms.IntegerField(label="Độ dài từ (km)", required=False, min_value=0)
    max_do_dai = forms.IntegerField(label="Đến (km)", required=False, min_value=0)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields: self.fields[field].widget.attrs.update({'class': 'form-control'})

# Form 3: Dùng cho người dùng gửi đánh giá (CHỈ GIỮ LẠI CÁC TRƯỜNG CẦN VALIDATE)
class CungDuongDanhGiaForm(forms.ModelForm):
    diem_danh_gia = forms.ChoiceField(label="Chấm điểm", choices=[(i, f"{i} sao") for i in range(5, 0, -1)], widget=forms.RadioSelect)
    binh_luan = forms.CharField(label="Bình luận của bạn", widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Chia sẻ cảm nhận của bạn...'}))
    
    class Meta:
        model = CungDuongDanhGia
        fields = ['diem_danh_gia', 'binh_luan']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if not isinstance(self.fields[field].widget, forms.RadioSelect): 
                self.fields[field].widget.attrs.update({'class': 'form-control'})

# XÓA BỎ CÁC FORM UPLOAD (MediaUploadForm, ReviewImageUploadForm)