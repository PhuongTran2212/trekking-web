# treks/models.py

import os
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from core.models import TinhThanh, DoKho, VatDung
from django.db.models.signals import post_delete
from django.dispatch import receiver


# ==============================================================================
# === HÀM HELPER & LỰA CHỌN (CHOICES)                                      ===
# ==============================================================================

def get_trek_media_path(instance, filename):
    """
    Tạo đường dẫn upload động cho media của CungDuongTrek.
    Kết quả: 'CungDuong/<slug-cung-duong>/<ten-file-goc>'
    """
    trek_slug = instance.cung_duong.slug
    # slugify để đảm bảo tên thư mục an toàn
    return os.path.join('CungDuong', slugify(trek_slug), filename)

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
    slug = models.SlugField(_("Slug"), unique=True, max_length=220, blank=True, help_text=_("Để trống để tự động tạo từ tên."))
    mo_ta = models.TextField(_("Mô tả chi tiết"))
        # MỚI: Thêm trường địa điểm chi tiết để tìm kiếm trên bản đồ
    dia_diem_chi_tiet = models.CharField(
        _("Địa điểm chi tiết (để tìm trên bản đồ)"), 
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_("Ví dụ: Vườn quốc gia Ba Vì, Hà Nội")
    )
    tinh_thanh = models.ForeignKey(TinhThanh, on_delete=models.PROTECT, verbose_name=_("Tỉnh/Thành phố"))
    do_dai_km = models.DecimalField(_("Độ dài (km)"), max_digits=5, decimal_places=2, default=0.00 )
    thoi_gian_uoc_tinh_gio = models.IntegerField(_("Thời gian ước tính (giờ)"),blank=True,null=True )
    tong_do_cao_leo_m = models.IntegerField(_("Tổng độ cao leo (m)"), blank=True, null=True)
    do_kho = models.ForeignKey(
    DoKho, 
    on_delete=models.SET_NULL, # <-- THAY ĐỔI QUAN TRỌNG
    blank=True,                # <-- THÊM
    null=True,                 # <-- THÊM
    verbose_name=_("Độ khó")
)
    mua_dep_nhat = models.CharField(_("Mùa đẹp nhất"), max_length=100, blank=True, null=True)
    du_lieu_ban_do_geojson = models.JSONField(_("Dữ liệu bản đồ GeoJSON"), blank=True, null=True)
    danh_gia_trung_binh = models.DecimalField(_("Điểm đánh giá trung bình"), max_digits=3, decimal_places=2, default=0.00)
    so_luot_danh_gia = models.IntegerField(_("Số lượt đánh giá"), default=0)

    trang_thai = models.CharField(
        _("Trạng thái duyệt"),
        max_length=10,
        choices=TrangThaiDuyet.choices,
        default=TrangThaiDuyet.DA_DUYET  # Mặc định là Đã duyệt cho Admin
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

    class Meta:
        db_table = 'cung_duong_trek'
        verbose_name = _("Cung Đường Trek")
        verbose_name_plural = _("Các Cung Đường Trek")
        ordering = ['-ngay_tao']

    def __str__(self):
        return self.ten

    @property
    def anh_bia_url(self):
        """
        Cung cấp một URL ảnh bìa tiện lợi cho templates và APIs.
        Ưu tiên ảnh được đánh dấu là bìa, nếu không có thì lấy ảnh đầu tiên.
        """
        media_bia = self.media.filter(la_anh_bia=True, loai_media='ANH').first()
        if media_bia:
            try: return media_bia.file.url
            except ValueError: pass

        first_image = self.media.filter(loai_media='ANH').order_by('ngay_tai_len').first()
        if first_image:
            try: return first_image.file.url
            except ValueError: pass

        return '/static/images/default_trek_image.png'
    @property
    def cover_media(self):
        """
        Trả về đối tượng CungDuongMedia đầu tiên được đánh dấu là ảnh bìa.
        Trả về None nếu không có.
        """
        return self.media.filter(la_anh_bia=True).first()
    @property
    def gallery_media(self):
        """
        Trả về queryset chứa tất cả media KHÔNG phải là ảnh bìa.
        Đây chính là "Thư viện Media" mà template cần.
        """
        return self.media.filter(la_anh_bia=False).order_by('ngay_tai_len')

    def save(self, *args, **kwargs):
        # ... hàm save của bạn giữ nguyên ...
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
     if not self.slug:
        # Bước 1: Dùng slugify của Django để chuyển thành dạng chuẩn "deo-hai-van"
        standard_slug = slugify(self.ten)
        
        # Bước 2: Dùng phương thức .replace() của Python để xóa bỏ tất cả dấu gạch ngang
        base_slug = standard_slug.replace('-', '')

        # Logic kiểm tra slug trùng lặp không thay đổi
        unique_slug = base_slug
        num = 1
        while CungDuongTrek.objects.filter(slug=unique_slug).exists():
            # Nếu trùng, slug mới sẽ là "deohaivan-1", "deohaivan-2",...
            unique_slug = f'{base_slug}-{num}'
            num += 1
        self.slug = unique_slug
     super().save(*args, **kwargs)

# ==============================================================================
# === CÁC MODEL PHỤ TRỢ CHO CUNG_DUONG_TREK                                  ===
# ==============================================================================

class CungDuongDuyetLog(models.Model):
    """Lưu lại lịch sử duyệt (phê duyệt, từ chối) đối với một CungDuongTrek."""
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
    class LoaiMedia(models.TextChoices):
        ANH = 'ANH', _('Ảnh')
        VIDEO = 'VIDEO', _('Video')

    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(_("Tập tin media"), upload_to=get_trek_media_path)
    loai_media = models.CharField(_("Loại media"), max_length=5, choices=LoaiMedia.choices, default=LoaiMedia.ANH)
    la_anh_bia = models.BooleanField(_("Là ảnh bìa?"), default=False, help_text=_("Đánh dấu đây là ảnh bìa chính"))
    ngay_tai_len = models.DateTimeField(_("Ngày tải lên"), auto_now_add=True)

    class Meta:
        db_table = 'cung_duong_media'
        verbose_name = _("Media Cung Đường")
        verbose_name_plural = _("Các Media Cung Đường")
        ordering = ['-la_anh_bia', 'ngay_tai_len']

    def __str__(self):
        return f"{self.get_loai_media_display()} cho {self.cung_duong.ten}"

@receiver(post_delete, sender=CungDuongMedia)
def submission_delete(sender, instance, **kwargs):
    """
    Tự động xóa file vật lý khỏi server khi một CungDuongMedia object bị xóa.
    """
    if instance.file:
        instance.file.delete(save=False)



class CungDuongVatDungGoiY(models.Model):
    """Các vật dụng được gợi ý mang theo cho một cung đường cụ thể."""
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='vat_dung_goi_y')
    vat_dung = models.ForeignKey(VatDung, on_delete=models.CASCADE)
    ghi_chu = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'cung_duong_vat_dung_goi_y'
        verbose_name = _("Vật Dụng Gợi Ý")
        verbose_name_plural = _("Các Vật Dụng Gợi Ý")
        constraints = [
            models.UniqueConstraint(fields=['cung_duong', 'vat_dung'], name='unique_trek_equipment_suggestion')
        ]

class CungDuongDanhGia(models.Model):
    """Lưu trữ đánh giá của người dùng cho một cung đường."""
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='danh_gia')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    diem_danh_gia = models.PositiveSmallIntegerField()
    binh_luan = models.TextField(blank=True, null=True)
    ngay_danh_gia = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cung_duong_danh_gia'
        verbose_name = _("Đánh Giá Cung Đường")
        verbose_name_plural = _("Các Đánh Giá Cung Đường")
        ordering = ['-ngay_danh_gia']
        constraints = [
            models.UniqueConstraint(fields=['cung_duong', 'user'], name='unique_user_review_per_trek')
        ]

class CungDuongAnhDanhGia(models.Model):
    """Lưu trữ hình ảnh do người dùng tải lên trong một đánh giá."""
    danh_gia = models.ForeignKey(CungDuongDanhGia, on_delete=models.CASCADE, related_name='anh_danh_gia')
    hinh_anh = models.ImageField(upload_to='reviews_media/')

    class Meta:
        db_table = 'cung_duong_anh_danh_gia'
        verbose_name = _("Ảnh Đánh Giá")
        verbose_name_plural = _("Các Ảnh Đánh Giá")
            # ===================================================================
    # === BẠN CHỈ CẦN THÊM ĐÚNG KHỐI CODE NÀY VÀO MODEL CỦA MÌNH      ===
    # ===================================================================
