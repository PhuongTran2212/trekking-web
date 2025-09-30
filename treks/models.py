# treks/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from core.models import TinhThanh, DoKho, VatDung

# ==============================================================================
# === CÁC LỰA CHỌN (CHOICES) CHO CÁC MODEL                                   ===
# ==============================================================================

class TrangThaiDuyet(models.TextChoices):
    """Trạng thái duyệt nội dung do người dùng tạo."""
    CHO_DUYET = 'CHO_DUYET', _('Chờ duyệt')
    DA_DUYET = 'DA_DUYET', _('Đã duyệt')
    TU_CHOI = 'TU_CHOI', _('Từ chối')


# ==============================================================================
# === MODEL CHÍNH: CUNG_DUONG_TREK                                           ===
# ==============================================================================

class CungDuongTrek(models.Model):
    """
    Lưu trữ thông tin chi tiết về một cung đường trekking.
    Đây là model trung tâm của ứng dụng treks.
    """
    ten = models.CharField(_("Tên cung đường"), max_length=200)
    slug = models.CharField(_("Slug"), unique=True, max_length=220)
    mo_ta = models.TextField(_("Mô tả chi tiết"))
    tinh_thanh = models.ForeignKey(TinhThanh, on_delete=models.PROTECT, verbose_name=_("Tỉnh/Thành phố"))
    do_dai_km = models.DecimalField(_("Độ dài (km)"), max_digits=5, decimal_places=2)
    thoi_gian_uoc_tinh_gio = models.IntegerField(_("Thời gian ước tính (giờ)"))
    tong_do_cao_leo_m = models.IntegerField(_("Tổng độ cao leo (m)"), blank=True, null=True)
    do_kho = models.ForeignKey(DoKho, on_delete=models.PROTECT, verbose_name=_("Độ khó"))
    mua_dep_nhat = models.CharField(_("Mùa đẹp nhất"), max_length=100, blank=True, null=True)
    du_lieu_ban_do_geojson = models.JSONField(_("Dữ liệu bản đồ GeoJSON"), blank=True, null=True)
    danh_gia_trung_binh = models.DecimalField(_("Điểm đánh giá trung bình"), max_digits=3, decimal_places=2, default=0.00)
    so_luot_danh_gia = models.IntegerField(_("Số lượt đánh giá"), default=0)
    
    trang_thai = models.CharField(
        _("Trạng thái duyệt"),
        max_length=10, 
        choices=TrangThaiDuyet.choices, 
        default=TrangThaiDuyet.CHO_DUYET
    )

    nguoi_tao = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        verbose_name=_("Người tạo")
    )
    ngay_tao = models.DateTimeField(_("Ngày tạo"), auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(_("Ngày cập nhật"), auto_now=True)
    
    @property
    def anh_bia_url(self):
        """
        Cung cấp một URL ảnh bìa tiện lợi cho templates và APIs.
        Ưu tiên ảnh được đánh dấu là bìa, nếu không có thì lấy ảnh đầu tiên.
        """
        media_bia = self.media.filter(la_anh_bia=True, loai_media='ANH').first()
        if media_bia:
            try:
                return media_bia.file.url
            except ValueError:
                pass 
        
        first_image = self.media.filter(loai_media='ANH').order_by('ngay_tai_len').first()
        if first_image:
            try:
                return first_image.file.url
            except ValueError:
                pass
        
        return '/static/images/default_trek_image.png'

    class Meta:
        db_table = 'cung_duong_trek'
        verbose_name = _("Cung Đường Trek")
        verbose_name_plural = _("Các Cung Đường Trek")
        ordering = ['-ngay_tao']

    def __str__(self):
        return self.ten

# ==============================================================================
# === CÁC MODEL PHỤ TRỢ CHO CUNG_DUONG_TREK                                  ===
# ==============================================================================

class CungDuongDuyetLog(models.Model):
    """Lưu lại lịch sử các hành động duyệt (phê duyệt, từ chối) đối với một CungDuongTrek."""
    class HanhDongDuyet(models.TextChoices):
        DUYET = 'DUYET', _('Duyệt')
        TU_CHOI = 'TU_CHOI', _('Từ chối')

    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='lich_su_duyet')
    nguoi_thuc_hien = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hanh_dong_duyet')
    hanh_dong = models.CharField(max_length=10, choices=HanhDongDuyet.choices)
    ly_do = models.TextField(blank=True, null=True, help_text=_("Ghi rõ lý do nếu từ chối"))
    ngay_thuc_hien = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cung_duong_duyet_log'
        verbose_name = _("Nhật ký Duyệt Cung đường")
        verbose_name_plural = _("Các Nhật ký Duyệt Cung đường")
        ordering = ['-ngay_thuc_hien']

    def __str__(self):
        admin = self.nguoi_thuc_hien.username if self.nguoi_thuc_hien else "[Đã xóa]"
        return f"[{self.get_hanh_dong_display()}] {self.cung_duong.ten} bởi {admin}"

class CungDuongMedia(models.Model):
    """Quản lý nhiều ảnh/video cho một cung đường."""
    class LoaiMedia(models.TextChoices):
        ANH = 'ANH', _('Ảnh')
        VIDEO = 'VIDEO', _('Video')

    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(_("Tập tin media"), upload_to='treks_media/') 
    loai_media = models.CharField(_("Loại media"), max_length=5, choices=LoaiMedia.choices, default=LoaiMedia.ANH)
    la_anh_bia = models.BooleanField(_("Là ảnh bìa?"), default=False, help_text=_("Đánh dấu đây là ảnh bìa chính"))
    ngay_tai_len = models.DateTimeField(_("Ngày tải lên"), auto_now_add=True)

    class Meta:
        db_table = 'cung_duong_media'
        verbose_name = _("Media Cung Đường")
        verbose_name_plural = _("Các Media Cung Đường")
        ordering = ['-la_anh_bia', 'ngay_tai_len'] # Ưu tiên hiển thị ảnh bìa lên đầu

    def __str__(self):
        return f"{self.get_loai_media_display()} cho {self.cung_duong.ten}"

class CungDuongVatDungGoiY(models.Model):
    """Các vật dụng được gợi ý mang theo cho một cung đường cụ thể."""
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='vat_dung_goi_y')
    vat_dung = models.ForeignKey(VatDung, on_delete=models.CASCADE)
    ghi_chu = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'cung_duong_vat_dung_goi_y'
        unique_together = (('cung_duong', 'vat_dung'),)
        verbose_name = _("Vật Dụng Gợi Ý")
        verbose_name_plural = _("Các Vật Dụng Gợi Ý")

class CungDuongDanhGia(models.Model):
    """Lưu trữ đánh giá của người dùng cho một cung đường."""
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='danh_gia')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    diem_danh_gia = models.PositiveSmallIntegerField()
    binh_luan = models.TextField(blank=True, null=True)
    ngay_danh_gia = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cung_duong_danh_gia'
        unique_together = (('cung_duong', 'user'),)
        verbose_name = _("Đánh Giá Cung Đường")
        verbose_name_plural = _("Các Đánh Giá Cung Đường")
        ordering = ['-ngay_danh_gia']

class CungDuongAnhDanhGia(models.Model):
    """Lưu trữ hình ảnh do người dùng tải lên trong một đánh giá."""
    danh_gia = models.ForeignKey(CungDuongDanhGia, on_delete=models.CASCADE, related_name='anh_danh_gia')
    hinh_anh = models.ImageField(upload_to='reviews_media/')

    class Meta:
        db_table = 'cung_duong_anh_danh_gia'
        verbose_name = _("Ảnh Đánh Giá")
        verbose_name_plural = _("Các Ảnh Đánh Giá")