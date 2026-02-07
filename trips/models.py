# trips/models.py

import uuid
import os
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from core.models import The
from treks.models import CungDuongTrek
from datetime import timedelta

# ==========================================================
# === HELPER FUNCTIONS & VALIDATORS ===
# ==========================================================

def trip_media_path(instance, filename):
    """
    Lưu file vào thư mục theo ID chuyến đi để ổn định (slug có thể đổi).
    Kết quả: trips/105/filename.jpg
    """
    return f'trips/{instance.chuyen_di_id}/{filename}'

def validate_file_size(value):
    """Giới hạn file upload không quá 10MB."""
    filesize = value.size
    if filesize > 10 * 1024 * 1024:
        raise ValidationError("Kích thước file tối đa là 10MB.")
    return value

def chat_media_path(instance, filename):
    """
    Lưu file chat vào: media/trip_chat_media/ten-chuyen-di/username/filename
    """
    # Slugify tên chuyến đi để đảm bảo tên thư mục an toàn (không dấu, không khoảng trắng)
    trip_name = slugify(instance.tin_nhan.chuyen_di.ten_chuyen_di)
    user_name = instance.tin_nhan.nguoi_gui.username
    return os.path.join('trip_chat_media', trip_name, user_name, filename)

# ==========================================================
# === 1. MODEL CHUYẾN ĐI (CORE MODEL) ===
# ==========================================================
class ChuyenDi(models.Model):
    # --- Thông tin cơ bản ---
    ten_chuyen_di = models.CharField(_("Tên chuyến đi"), max_length=200)
    slug = models.SlugField(_("Slug"), unique=True, max_length=255, blank=True, help_text="URL thân thiện, tự động tạo.")
    mo_ta = models.TextField(_("Mô tả & Kế hoạch"), blank=True, null=True)
    
    # --- Liên kết ---
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.PROTECT, related_name='chuyendi', verbose_name=_("Cung đường gốc"))
    nguoi_to_chuc = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chuyendi_da_to_chuc', verbose_name=_("Người tổ chức"))
    
    # --- Thời gian & Số lượng ---
    ngay_bat_dau = models.DateTimeField(_("Ngày bắt đầu"))
    ngay_ket_thuc = models.DateTimeField(_("Ngày kết thúc"), default=timezone.now)
    so_luong_toi_da = models.PositiveIntegerField(_("Số lượng tối đa"))
    
    # --- Cài đặt & Trạng thái ---
    # --- 1. CẬP NHẬT TRẠNG THÁI ---
    TRANG_THAI_CHOICES = [
        ('CHO_DUYET', 'Chờ duyệt'),          # Mặc định khi mới tạo
        ('DANG_TUYEN', 'Đang tuyển thành viên'), # Sau khi Admin duyệt
        ('BI_TU_CHOI', 'Bị từ chối'),        # Admin từ chối
        ('DA_HUY', 'Đã hủy chuyến'),         # Host hủy khi đã có khách
        ('DA_DONG', 'Đã đóng đăng ký'),      # Host đóng thủ công
        ('TAM_HOAN', 'Tạm hoãn'),            # Ít dùng
    ]

    # 2. Field trạng thái dạng chuỗi (Thay vì ForeignKey)
    trang_thai = models.CharField(
        _("Trạng thái"), 
        max_length=20, 
        choices=TRANG_THAI_CHOICES, 
        default='CHO_DUYET' # <--- Thay đổi default
    )

    CHE_DO_RIENG_TU_CHOICES = [('CONG_KHAI', 'Công khai'), ('RIENG_TU', 'Riêng tư')]
    che_do_rieng_tu = models.CharField(_("Chế độ"), max_length=15, choices=CHE_DO_RIENG_TU_CHOICES, default='CONG_KHAI')
    yeu_cau_ly_do = models.BooleanField(_("Yêu cầu lý do tham gia?"), default=False)
    ma_moi = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # --- Thông tin bổ sung ---
    # Sử dụng Decimal('0') để tránh sai số float
    chi_phi_uoc_tinh = models.DecimalField(_("Chi phí (VND)"), max_digits=12, decimal_places=0, blank=True, null=True)
    dia_diem_tap_trung = models.CharField(_("Địa điểm tập trung"), max_length=255, blank=True, null=True)
    
    # Dùng default=dict để tránh lỗi khi truy cập key của None
    toa_do_tap_trung = models.JSONField(_("Tọa độ tập trung"), blank=True, default=dict) 
    tags = models.ManyToManyField(The, blank=True, verbose_name=_("Hashtag"))

    # --- Snapshot dữ liệu từ Cung đường (Tránh bị ảnh hưởng khi Cung đường gốc thay đổi) ---
    cd_ten = models.CharField(max_length=200, editable=False, default='')
    cd_mo_ta = models.TextField(editable=False, blank=True, null=True)
    cd_tinh_thanh_ten = models.CharField(max_length=100, editable=False, default='')
    cd_do_kho_ten = models.CharField(max_length=50, editable=False, default='')
    cd_do_dai_km = models.DecimalField(max_digits=6, decimal_places=2, editable=False, default=Decimal('0.00'))
    cd_thoi_gian_uoc_tinh_gio = models.IntegerField(editable=False, blank=True, null=True)
    cd_tong_do_cao_leo_m = models.IntegerField(editable=False, blank=True, null=True)
    cd_du_lieu_ban_do_geojson = models.JSONField(editable=False, blank=True, default=dict)
    ly_do_tu_choi = models.TextField(_("Lý do từ chối"), blank=True, null=True)
    nguoi_duyet = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips_approved')
    ngay_duyet = models.DateTimeField(_("Ngày duyệt"), blank=True, null=True)

    # --- Media ---
    anh_bia = models.ForeignKey('ChuyenDiMedia', on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name=_("Ảnh bìa"))
    
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-ngay_bat_dau']
        verbose_name = _("Chuyến đi")
        verbose_name_plural = _("Danh sách Chuyến đi")

    def __str__(self):
        return self.ten_chuyen_di

    def get_absolute_url(self):
        return reverse('trips:chuyen_di_detail', kwargs={'pk': self.pk, 'slug': self.slug})
    def get_chat_url(self):
        try:
            # Trỏ về namespace 'trips' và name 'chat_room'
            return reverse('trips:chat_room', kwargs={'trip_id': self.pk})
        except:
            return None

    def clean(self):
        """Validate logic nghiệp vụ"""
        if self.ngay_ket_thuc and self.ngay_bat_dau:
            if self.ngay_ket_thuc < self.ngay_bat_dau:
                raise ValidationError({'ngay_ket_thuc': _("Ngày kết thúc không thể trước ngày bắt đầu.")})

    def save(self, *args, **kwargs):
        # Tự động tạo slug nếu chưa có
        if not self.slug:
            base_slug = slugify(self.ten_chuyen_di)
            unique_slug = base_slug
            num = 1
            while ChuyenDi.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{base_slug}-{num}'
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)
  # ==========================================================
    # === CÁC HÀM TRỢ GIÚP (STATUS, COVER, THỜI GIAN) ===
    # ==========================================================

    # --- 4. CẬP NHẬT BADGE CONFIG ---
    BADGE_CONFIG = {
        'WAITING':     {'name': 'Chờ duyệt',    'color': '#d97706', 'bg': '#fffbeb'},
        'REJECTED':    {'name': 'Bị từ chối',   'color': '#b91c1c', 'bg': '#fef2f2'},
        'CANCELLED':   {'name': 'Đã hủy',       'color': '#ef4444', 'bg': '#fee2e2'},
        'ENDED':       {'name': 'Đã kết thúc',  'color': '#6b7280', 'bg': '#f3f4f6'},
        'ONGOING':     {'name': 'Đang diễn ra', 'color': '#3b82f6', 'bg': '#dbeafe'},
        'FULL':        {'name': 'Đã đủ người',  'color': '#f59e0b', 'bg': '#fef3c7'},
        'OPEN':        {'name': 'Đang tuyển',   'color': '#10b981', 'bg': '#d1fae5'},
        'CLOSED':      {'name': 'Đã đóng',      'color': '#6b7280', 'bg': '#e5e7eb'},
    }


    @property
    def dynamic_status_info(self):
        # Ưu tiên trạng thái cứng trong DB trước
        if self.trang_thai == 'CHO_DUYET': return self.BADGE_CONFIG['WAITING']
        if self.trang_thai == 'BI_TU_CHOI': return self.BADGE_CONFIG['REJECTED']
        if self.trang_thai == 'DA_HUY': return self.BADGE_CONFIG['CANCELLED']
        if self.trang_thai == 'DA_DONG': return self.BADGE_CONFIG['CLOSED']

        # Nếu đang tuyển thì mới tính toán động
        if self.trang_thai == 'DANG_TUYEN':
            now = timezone.now()
            if self.ngay_ket_thuc and now > self.ngay_ket_thuc:
                return self.BADGE_CONFIG['ENDED']
            if self.ngay_bat_dau and now >= self.ngay_bat_dau:
                return self.BADGE_CONFIG['ONGOING']
            
            # Check full slot
            # Lấy số lượng từ annotate (nếu có) hoặc đếm trực tiếp
            current_members = getattr(self, 'so_thanh_vien_tham_gia', None)
            if current_members is None:
                current_members = self.thanh_vien.filter(trang_thai_tham_gia='DA_THAM_GIA').count()
            
            if current_members >= self.so_luong_toi_da:
                return self.BADGE_CONFIG['FULL']
            
            return self.BADGE_CONFIG['OPEN']
            
        return self.BADGE_CONFIG['OPEN']

    # --- WRAPPER CHO TEMPLATE DỄ GỌI ---
    @property
    def status_name(self):
        return self.dynamic_status_info['name']

    @property
    def status_color(self):
        return self.dynamic_status_info['color']

    @property
    def thoi_gian_display(self):
        """Hiển thị thời gian tiếng Việt (VD: 2 ngày, Trong ngày)"""
        if not self.ngay_bat_dau or not self.ngay_ket_thuc:
            return "Chưa xác định"
            
        delta = self.ngay_ket_thuc - self.ngay_bat_dau
        days = delta.days
        
        # Nếu đi về trong ngày
        if days == 0:
            return "Trong ngày"
        
        # Đi qua đêm tính là ngày tiếp theo
        return f"{days + 1} ngày"

    @property
    def cover_url(self):
        """Tự động lấy link ảnh bìa"""
        # 1. Ưu tiên ảnh bìa riêng của Chuyến đi (nếu người tạo đã upload)
        if self.anh_bia and self.anh_bia.file:
            return self.anh_bia.file.url
        
        # 2. Nếu không có, lấy ảnh từ Cung đường gốc
        if self.cung_duong:
            # Trong treks/models.py bạn đã định nghĩa property 'anh_bia_url'
            # Nó trả về string (URL) luôn rồi, nên không cần .url nữa
            return self.cung_duong.anh_bia_url

        # 3. Ảnh mặc định cuối cùng
        return "https://via.placeholder.com/400x250?text=Trekking+Vietnam"
    @property
    def so_cho_con_lai(self):
        # Nếu view đã annotate số lượng thì dùng luôn, không thì query đếm lại
        da_tham_gia = getattr(self, 'so_thanh_vien_tham_gia', None)
        if da_tham_gia is None:
            da_tham_gia = self.thanh_vien.filter(trang_thai_tham_gia='DA_THAM_GIA').count()
            
        con_lai = self.so_luong_toi_da - da_tham_gia
        return con_lai if con_lai > 0 else 0

    
# ==========================================================
# === 2. MODEL TIMELINE ===
# ==========================================================
class ChuyenDiTimeline(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='timeline')
    ngay = models.PositiveIntegerField(_("Ngày thứ"))
    thoi_gian = models.TimeField(_("Thời gian"))
    hoat_dong = models.CharField(_("Hoạt động"), max_length=255)
    mo_ta_chi_tiet = models.TextField(_("Mô tả chi tiết"), blank=True, null=True)
    thu_tu = models.PositiveIntegerField(default=0, help_text="Dùng để sắp xếp thứ tự hiển thị")
    
    class Meta:
        ordering = ['ngay', 'thoi_gian', 'thu_tu']
        verbose_name = _("Lịch trình")
        verbose_name_plural = _("Lịch trình chi tiết")

# ==========================================================
# === 3. MODEL MEDIA CHUYẾN ĐI ===
# ==========================================================
class ChuyenDiMedia(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='media')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Người tải lên"))
    
    # Thêm validator kiểm tra file size
    file = models.FileField(_("Tập tin"), upload_to=trip_media_path, validators=[validate_file_size])
    
    LOAI_MEDIA_CHOICES = [('ANH', 'Ảnh'), ('VIDEO', 'Video')]
    loai_media = models.CharField(_("Loại media"), max_length=10, choices=LOAI_MEDIA_CHOICES, default='ANH')
    ngay_tai_len = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ngay_tai_len']
        verbose_name = _("Media Chuyến đi")

# ==========================================================
# === 4. MODEL THÀNH VIÊN ===
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
    
    # Có thể dùng để đánh giá sau chuyến đi
    ngay_checkin = models.DateTimeField(_("Thời gian Check-in"), blank=True, null=True)

    class Meta:
        # Sử dụng UniqueConstraint thay cho unique_together (Chuẩn mới)
        constraints = [
            models.UniqueConstraint(fields=['chuyen_di', 'user'], name='unique_thanh_vien_chuyen_di')
        ]
        ordering = ['-vai_tro', 'ngay_tham_gia']
        verbose_name = _("Thành viên")

    def __str__(self):
        return f'{self.user.username} - {self.chuyen_di.ten_chuyen_di}'

# ==========================================================
# === 5. MODEL TIN NHẮN (CHAT GROUP) ===
# ==========================================================
class ChuyenDiTinNhan(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='tin_nhan')
    nguoi_gui = models.ForeignKey(User, on_delete=models.CASCADE)
    tra_loi_tin_nhan = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='cac_tra_loi')
    noi_dung = models.TextField(blank=True, null=True)
    thoi_gian_gui = models.DateTimeField(auto_now_add=True)
    # --- MỚI: Tính năng nâng cao ---
    da_xoa = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_messages', blank=True)
    class Meta:
        ordering = ['thoi_gian_gui']
        indexes = [
            models.Index(fields=['chuyen_di', 'thoi_gian_gui']), # Tối ưu load chat
        ]
    def __str__(self):
        return f"Msg {self.id} from {self.nguoi_gui}"

class ChuyenDiTinNhanMedia(models.Model):
    tin_nhan = models.ForeignKey(ChuyenDiTinNhan, on_delete=models.CASCADE, related_name='media')
    LOAI_MEDIA_CHOICES = [('ANH', 'Ảnh'), ('VIDEO', 'Video'), ('FILE', 'File')]
    loai_media = models.CharField(max_length=10, choices=LOAI_MEDIA_CHOICES, default='ANH')
    
    # Sử dụng hàm chat_media_path để lưu file vào cấu trúc thư mục mong muốn
    duong_dan_file = models.FileField(upload_to=chat_media_path, validators=[validate_file_size]) 
    
    thu_tu = models.PositiveSmallIntegerField(default=0)
    ten_file_goc = models.CharField(max_length=255, blank=True, null=True)
    kich_thuoc_file_kb = models.FloatField(default=0, blank=True, null=True)

    def __str__(self):
        return f"Media for msg {self.tin_nhan.id}"

# ==========================================================
# === 6. MODEL NHẬT KÝ HÀNH TRÌNH (GPS TRACKING) ===
# ==========================================================
class ChuyenDiNhatKyHanhTrinh(models.Model):
    thanh_vien = models.ForeignKey(ChuyenDiThanhVien, on_delete=models.CASCADE)
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE)
    
    # Tọa độ GPS
    vi_do = models.DecimalField(max_digits=9, decimal_places=6)
    kinh_do = models.DecimalField(max_digits=9, decimal_places=6)
    do_cao = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    noi_dung_checkin = models.CharField(max_length=255, blank=True, null=True)
    hinh_anh_checkin = models.ImageField(upload_to='trip_checkins/', blank=True, null=True)
    thoi_gian_checkin = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['thoi_gian_checkin']
        # Tối ưu truy vấn theo tọa độ và thời gian
        indexes = [
            models.Index(fields=['chuyen_di', 'thoi_gian_checkin']),
            models.Index(fields=['vi_do', 'kinh_do']),
        ]