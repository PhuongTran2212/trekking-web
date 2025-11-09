# trips/models.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from core.models import TrangThaiChuyenDi, The
from treks.models import CungDuongTrek

# ==========================================================
# === 1. MODEL CHUYẾN ĐI (ĐÃ HOÀN THIỆN) ===
# ==========================================================
class ChuyenDi(models.Model):
    # --- Thông tin cơ bản ---
    ten_chuyen_di = models.CharField(_("Tên chuyến đi"), max_length=200)
    slug = models.SlugField(_("Slug"), unique=True, max_length=255, blank=True, help_text="Tự động tạo")
    mo_ta = models.TextField(_("Mô tả & Kế hoạch"), blank=True, null=True, help_text='Mô tả chi tiết, lịch trình, yêu cầu cho chuyến đi')
    
    # --- Liên kết & Tổ chức ---
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.PROTECT, related_name='chuyendi', verbose_name=_("Cung đường gốc"))
    nguoi_to_chuc = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chuyendi_da_to_chuc', verbose_name=_("Người tổ chức"))
    
    # --- Thời gian & Số lượng ---
    ngay_bat_dau = models.DateTimeField(_("Ngày bắt đầu"))
    ngay_ket_thuc = models.DateTimeField(_("Ngày kết thúc"), default=timezone.now) # THÊM default
    so_luong_toi_da = models.PositiveIntegerField(_("Số lượng tối đa"))
    
    # --- Cài đặt & Trạng thái ---
    trang_thai = models.ForeignKey(TrangThaiChuyenDi, on_delete=models.PROTECT, verbose_name=_("Trạng thái chuyến đi"))
    CHE_DO_RIENG_TU_CHOICES = [('CONG_KHAI', 'Công khai'), ('RIENG_TU', 'Riêng tư')]
    che_do_rieng_tu = models.CharField(_("Chế độ riêng tư"), max_length=15, choices=CHE_DO_RIENG_TU_CHOICES, default='CONG_KHAI')
    yeu_cau_ly_do = models.BooleanField(_("Yêu cầu lý do tham gia?"), default=False)
    ma_moi = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="Mã mời cho chuyến đi riêng tư")
    
    # --- Thông tin bổ sung ---
    chi_phi_uoc_tinh = models.DecimalField(_("Chi phí ước tính (VND)"), max_digits=10, decimal_places=0, blank=True, null=True)
    dia_diem_tap_trung = models.CharField(_("Địa điểm tập trung"), max_length=255, blank=True, null=True)
    toa_do_tap_trung = models.JSONField(_("Tọa độ tập trung"), blank=True, null=True, help_text="Lưu dưới dạng {'lat': ..., 'lng': ...}")
    tags = models.ManyToManyField(The, blank=True, verbose_name=_("Hashtag"))

    # --- Thông tin "thừa kế" từ Cung đường ---
    cd_ten = models.CharField(max_length=200, editable=False, default='') # THÊM default
    cd_mo_ta = models.TextField(editable=False, blank=True, null=True) # Đã có null=True, an toàn
    cd_tinh_thanh_ten = models.CharField(max_length=100, editable=False, default='') # THÊM default
    cd_do_kho_ten = models.CharField(max_length=50, editable=False, default='') # THÊM default
    cd_do_dai_km = models.DecimalField(max_digits=5, decimal_places=2, editable=False, default=0.0) # THÊM default
    cd_thoi_gian_uoc_tinh_gio = models.IntegerField(editable=False, blank=True, null=True) # Đã có null=True, an toàn
    cd_tong_do_cao_leo_m = models.IntegerField(editable=False, blank=True, null=True) # Đã có null=True, an toàn
    cd_du_lieu_ban_do_geojson = models.JSONField(editable=False, blank=True, null=True) # Đã có null=True, an toàn

    # --- Quản lý Media ---
    anh_bia = models.ForeignKey('ChuyenDiMedia', on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name=_("Ảnh bìa chuyến đi"))
    
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('trips:chuyen_di_detail', kwargs={'pk': self.pk, 'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.ten_chuyen_di)
            # Logic chống trùng slug
            num = 1
            unique_slug = self.slug
            while ChuyenDi.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{self.slug}-{num}'
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ten_chuyen_di

# ==========================================================
# === 2. MODEL TIMELINE (MỚI) ===
# ==========================================================
class ChuyenDiTimeline(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='timeline')
    ngay = models.PositiveIntegerField(_("Ngày thứ"))
    thoi_gian = models.TimeField(_("Thời gian"))
    hoat_dong = models.CharField(_("Hoạt động"), max_length=255)
    mo_ta_chi_tiet = models.TextField(_("Mô tả chi tiết"), blank=True, null=True)
    thu_tu = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['ngay', 'thoi_gian', 'thu_tu']

# ==========================================================
# === 3. MODEL MEDIA CHUYẾN ĐI (MỚI) ===
# ==========================================================
def trip_media_path(instance, filename):
    return f'trips/{instance.chuyen_di.slug or instance.chuyen_di.id}/{filename}'

class ChuyenDiMedia(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='media')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Người tải lên"))
    file = models.FileField(_("Tập tin"), upload_to=trip_media_path)
    LOAI_MEDIA_CHOICES = [('ANH', 'Ảnh'), ('VIDEO', 'Video')]
    loai_media = models.CharField(_("Loại media"), max_length=10, choices=LOAI_MEDIA_CHOICES, default='ANH')
    ngay_tai_len = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ngay_tai_len']

# ==========================================================
# === 4. MODEL THÀNH VIÊN (ĐÃ HOÀN THIỆN) ===
# ==========================================================
class ChuyenDiThanhVien(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='thanh_vien')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cac_chuyen_di')

    VAI_TRO_CHOICES = [('TRUONG_DOAN', 'Trưởng đoàn'), ('THANH_VIEN', 'Thành viên')]
    vai_tro = models.CharField(_("Vai trò"), max_length=15, choices=VAI_TRO_CHOICES, default='THANH_VIEN')

    TRANG_THAI_THAM_GIA_CHOICES = [
        ('DA_GUI_YEU_CAU', 'Đã gửi yêu cầu'),
        ('DA_THAM_GIA', 'Đã tham gia'),
        ('BI_TU_CHOI', 'Bị từ chối'),
        ('DA_ROI_DI', 'Đã rời đi'),
    ]
    trang_thai_tham_gia = models.CharField(_("Trạng thái"), max_length=20, choices=TRANG_THAI_THAM_GIA_CHOICES, default='DA_GUI_YEU_CAU')
    
    ly_do_tham_gia = models.TextField(_("Lý do tham gia"), blank=True, null=True)
    ngay_tham_gia = models.DateTimeField(auto_now_add=True)
    ngay_bat_dau_hanh_trinh = models.DateField(_("Ngày bắt đầu hành trình"), blank=True, null=True)
    ngay_ket_thuc_hanh_trinh = models.DateField(_("Ngày kết thúc hành trình"), blank=True, null=True)

    class Meta:
        unique_together = ('chuyen_di', 'user')
        ordering = ['-vai_tro', 'ngay_tham_gia']

    def __str__(self):
        return f'{self.user.username} - {self.chuyen_di.ten_chuyen_di}'

# ==========================================================
# === 5 & 6. MODELS TIN NHẮN (Giữ nguyên) ===
# ==========================================================
class ChuyenDiTinNhan(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='tin_nhan')
    nguoi_gui = models.ForeignKey(User, on_delete=models.CASCADE)
    tra_loi_tin_nhan = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='cac_tra_loi')
    noi_dung = models.TextField(blank=True, null=True)
    thoi_gian_gui = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['thoi_gian_gui']

class ChuyenDiTinNhanMedia(models.Model):
    tin_nhan = models.ForeignKey(ChuyenDiTinNhan, on_delete=models.CASCADE, related_name='media')
    LOAI_MEDIA_CHOICES = [('ANH', 'Ảnh'), ('VIDEO', 'Video'), ('FILE', 'File')]
    loai_media = models.CharField(max_length=10, choices=LOAI_MEDIA_CHOICES)
    # Đổi CharField thành FileField để Django quản lý file
    duong_dan_file = models.FileField(upload_to='trip_chat_media/') 
    thu_tu = models.PositiveSmallIntegerField(default=0)
    ten_file_goc = models.CharField(max_length=255, blank=True, null=True)
    kich_thuoc_file_kb = models.IntegerField(blank=True, null=True)

# ==========================================================
# === 7. MODEL NHẬT KÝ HÀNH TRÌNH (Giữ nguyên) ===
# ==========================================================
class ChuyenDiNhatKyHanhTrinh(models.Model):
    thanh_vien = models.ForeignKey(ChuyenDiThanhVien, on_delete=models.CASCADE)
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE)
    vi_do = models.DecimalField(max_digits=9, decimal_places=6)
    kinh_do = models.DecimalField(max_digits=9, decimal_places=6)
    do_cao = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    noi_dung_checkin = models.CharField(max_length=255, blank=True, null=True)
    # Đổi CharField thành ImageField
    hinh_anh_checkin = models.ImageField(upload_to='trip_checkins/', blank=True, null=True)
    thoi_gian_checkin = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['thoi_gian_checkin']