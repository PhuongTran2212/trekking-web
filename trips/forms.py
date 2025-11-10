# trips/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import ChuyenDi, ChuyenDiTimeline
from treks.models import CungDuongTrek
from core.models import DoKho, TinhThanh, The

# ==========================================================
# === FORM LỌC CHUYẾN ĐI (TRANG HUB) ===
# ==========================================================
class TripFilterForm(forms.Form):
    q = forms.CharField(
        label="Tìm theo tên", 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Tên chuyến đi, cung đường...',
            'class': 'form-control form-control-sm'
        })
    )
    
    cung_duong = forms.ModelChoiceField(
        label="Cung đường cụ thể",
        queryset=CungDuongTrek.objects.filter(trang_thai='DA_DUYET').order_by('ten'),
        required=False,
        empty_label="Tất cả cung đường",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm select2'})
    )

    tinh_thanh = forms.ModelChoiceField(
        label="Tỉnh thành",
        queryset=TinhThanh.objects.order_by('ten'),
        required=False,
        empty_label="Tất cả tỉnh thành",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm select2'})
    )
    
    start_date = forms.DateField(
        label="Khởi hành từ ngày",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    
    tags = forms.ModelMultipleChoiceField(
        label="Chủ đề (Hashtag)",
        queryset=The.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select form-select-sm select2'})
    )


# ==========================================================
# === FORM CHÍNH ĐỂ TẠO / SỬA CHUYẾN ĐI ===
# ==========================================================
class ChuyenDiForm(forms.ModelForm):
    class Meta:
        model = ChuyenDi
        fields = [
            'ten_chuyen_di', 'mo_ta', 'ngay_bat_dau', 'ngay_ket_thuc', 'so_luong_toi_da', 
            'chi_phi_uoc_tinh', 'che_do_rieng_tu', 'yeu_cau_ly_do', 'dia_diem_tap_trung', 'tags'
        ]
        widgets = {
            'ten_chuyen_di': forms.TextInput(attrs={'class': 'form-control'}),
            'mo_ta': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Giới thiệu về chuyến đi, lịch trình dự kiến, chi phí bao gồm những gì, yêu cầu về thể lực...'}),
            'ngay_bat_dau': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'ngay_ket_thuc': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'so_luong_toi_da': forms.NumberInput(attrs={'class': 'form-control'}),
            'chi_phi_uoc_tinh': forms.NumberInput(attrs={'class': 'form-control'}),
            'che_do_rieng_tu': forms.Select(attrs={'class': 'form-select'}),
            'yeu_cau_ly_do': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dia_diem_tap_trung': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        }
        labels = {
            'ten_chuyen_di': 'Tên Chuyến đi',
            'mo_ta': 'Mô tả chi tiết & Kế hoạch',
            'ngay_bat_dau': 'Thời gian bắt đầu',
            'ngay_ket_thuc': 'Thời gian kết thúc',
            'so_luong_toi_da': 'Số lượng thành viên tối đa',
            'chi_phi_uoc_tinh': 'Chi phí dự kiến (VND / người)',
            'che_do_rieng_tu': 'Chế độ riêng tư',
            'yeu_cau_ly_do': 'Yêu cầu người tham gia điền lý do',
            'dia_diem_tap_trung': 'Địa điểm tập trung',
            'tags': 'Chủ đề (Hashtag)',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("ngay_bat_dau")
        end_date = cleaned_data.get("ngay_ket_thuc")
        if start_date and end_date and end_date < start_date:
            self.add_error('ngay_ket_thuc', "Ngày kết thúc không thể trước ngày bắt đầu.")
        return cleaned_data


# ==========================================================
# === FORM CHO MỖI MỐC TIMELINE ===
# ==========================================================
class ChuyenDiTimelineForm(forms.ModelForm):
    class Meta:
        model = ChuyenDiTimeline
        fields = ['ngay', 'thoi_gian', 'hoat_dong', 'mo_ta_chi_tiet']
        widgets = {
            'ngay': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ngày thứ...'}),
            'thoi_gian': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hoat_dong': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hoạt động chính'}),
            'mo_ta_chi_tiet': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Mô tả thêm (tùy chọn)'}),
        }
        labels = {
            'ngay': 'Ngày',
            'thoi_gian': 'Thời gian',
            'hoat_dong': 'Hoạt động',
            'mo_ta_chi_tiet': 'Mô tả chi tiết',
        }


# ==========================================================
# === FORMSET ĐỂ QUẢN LÝ NHIỀU MỐC TIMELINE ===
# ==========================================================
TimelineFormSet = forms.inlineformset_factory(
    ChuyenDi, 
    ChuyenDiTimeline, 
    form=ChuyenDiTimelineForm,
    extra=1,  # Luôn hiển thị 1 form trống để người dùng thêm mới
    can_delete=True, # Cho phép xóa các mốc đã có
    can_order=False, # Không cần sắp xếp
)
# === FORM MỚI CHO TRANG CHỌN CUNG ĐƯỜNG ===
class SelectTrekFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tìm tên cung đường...'})
    )
    tinh_thanh = forms.ModelChoiceField(
        queryset=TinhThanh.objects.order_by('ten'),
        required=False,
        empty_label="Tất cả tỉnh thành",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    do_kho = forms.ModelChoiceField(
        queryset=DoKho.objects.all(),
        required=False,
        empty_label="Tất cả độ khó",
        widget=forms.Select(attrs={'class': 'form-select'})
    )