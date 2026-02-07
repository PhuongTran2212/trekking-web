import os
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from core.models import TinhThanh, DoKho, VatDung
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from django.templatetags.static import static
from django.utils import timezone

# ==============================================================================
# === HÀM HELPER & VALIDATORS ===
# ==============================================================================

def validate_image_size(value):
    """Giới hạn kích thước file upload không quá 5MB."""
    filesize = value.size
    if filesize > 5 * 1024 * 1024: # 5MB
        raise ValidationError("Kích thước ảnh không được vượt quá 5MB.")
    return value

def get_trek_media_path(instance, filename):
    """
    Tạo đường dẫn upload cho media chính của cung đường.
    Kết quả: 'CungDuong/<slug>/<filename>'
    """
    trek_slug = instance.cung_duong.slug or slugify(instance.cung_duong.ten).replace('-', '')
    return os.path.join('CungDuong', trek_slug, filename)

def get_review_media_path(instance, filename):
    """
    Tạo đường dẫn upload cho ảnh của review.
    Kết quả: 'reviews_media/<slug>/<filename>'
    """
    trek_slug = instance.danh_gia.cung_duong.slug or str(instance.danh_gia.cung_duong.pk)
    return os.path.join('reviews_media', trek_slug, filename)

# ==============================================================================
# === ENUMS / CHOICES ===
# ==============================================================================

class TrangThaiDuyet(models.TextChoices):
    CHO_DUYET = 'CHO_DUYET', _('Chờ duyệt')
    DA_DUYET = 'DA_DUYET', _('Đã duyệt')
    TU_CHOI = 'TU_CHOI', _('Từ chối')

# ==============================================================================
# === MODELS ===
# ==============================================================================

class CungDuongTrek(models.Model):
    ten = models.CharField(_("Tên cung đường"), max_length=200)
    slug = models.SlugField(_("Slug"), unique=True, max_length=220, blank=True)
    mo_ta = models.TextField(_("Mô tả chi tiết"), blank=True, null=True)
    dia_diem_chi_tiet = models.CharField(_("Địa điểm chi tiết"), max_length=255, blank=True, null=True)
    tinh_thanh = models.ForeignKey(TinhThanh, on_delete=models.PROTECT, verbose_name=_("Tỉnh/Thành phố"))
    do_dai_km = models.DecimalField(_("Độ dài (km)"), max_digits=5, decimal_places=2, default=0.00)
    thoi_gian_uoc_tinh_gio = models.IntegerField(_("Thời gian ước tính (giờ)"), blank=True, null=True)
    tong_do_cao_leo_m = models.IntegerField(_("Tổng độ cao leo (m)"), blank=True, null=True)
    do_kho = models.ForeignKey(DoKho, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Độ khó"))
    mua_dep_nhat = models.CharField(_("Mùa đẹp nhất"), max_length=100, blank=True, null=True)
    du_lieu_ban_do_geojson = models.JSONField(_("Dữ liệu bản đồ GeoJSON"), blank=True, null=True)
    danh_gia_trung_binh = models.DecimalField(_("Điểm đánh giá trung bình"), max_digits=3, decimal_places=2, default=0.00)
    so_luot_danh_gia = models.IntegerField(_("Số lượt đánh giá"), default=0)
    trang_thai = models.CharField(_("Trạng thái duyệt"), max_length=10, choices=TrangThaiDuyet.choices, default=TrangThaiDuyet.DA_DUYET)
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Người tạo"))
    ngay_tao = models.DateTimeField(_("Ngày tạo"), auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(_("Ngày cập nhật"), auto_now=True)

    class Meta:
        db_table = 'cung_duong_trek'
        verbose_name = _("Cung Đường Trek")
        verbose_name_plural = _("Các Cung Đường Trek")
        ordering = ['-ngay_tao']

    def __str__(self):
        return self.ten
        
    def get_absolute_url(self):
        return reverse('treks:cung_duong_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            standard_slug = slugify(self.ten)
            base_slug = standard_slug.replace('-', '')
            unique_slug = base_slug
            num = 1
            while CungDuongTrek.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{base_slug}-{num}'
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    @property
    def anh_bia_url(self):
        media_bia = self.media.filter(la_anh_bia=True).first()
        if media_bia and hasattr(media_bia, 'file') and media_bia.file:
            return media_bia.file.url
        first_image = self.media.filter(loai_media='ANH').first()
        if first_image and hasattr(first_image, 'file') and first_image.file:
            return first_image.file.url
        return static('images/default_trek_image.png')

    @property
    def cover_media(self):
        return self.media.filter(la_anh_bia=True).first()
    
    @property
    def gallery_media(self):
        return self.media.filter(la_anh_bia=False).order_by('ngay_tai_len')

class CungDuongDuyetLog(models.Model):
    class HanhDongDuyet(models.TextChoices):
        DUYET = 'DUYET', _('Duyệt')
        TU_CHOI = 'TU_CHOI', _('Từ chối')
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='lich_su_duyet')
    nguoi_thuc_hien = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hanh_dong_duyet')
    hanh_dong = models.CharField(max_length=10, choices=HanhDongDuyet.choices)
    ly_do = models.TextField(blank=True, null=True)
    ngay_thuc_hien = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'cung_duong_duyet_log'
        verbose_name = _("Nhật ký Duyệt Cung đường")
        verbose_name_plural = _("Các Nhật ký Duyệt Cung đường")
        ordering = ['-ngay_thuc_hien']

class CungDuongMedia(models.Model):
    class LoaiMedia(models.TextChoices):
        ANH = 'ANH', _('Ảnh')
        VIDEO = 'VIDEO', _('Video')
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(_("Tập tin media"), upload_to=get_trek_media_path)
    loai_media = models.CharField(_("Loại media"), max_length=5, choices=LoaiMedia.choices, default=LoaiMedia.ANH)
    la_anh_bia = models.BooleanField(_("Là ảnh bìa?"), default=False)
    ngay_tai_len = models.DateTimeField(_("Ngày tải lên"), auto_now_add=True)
    class Meta:
        db_table = 'cung_duong_media'
        verbose_name = _("Media Cung Đường")
        verbose_name_plural = _("Các Media Cung Đường")
        ordering = ['-la_anh_bia', 'ngay_tai_len']

class CungDuongVatDungGoiY(models.Model):
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='vat_dung_goi_y')
    vat_dung = models.ForeignKey(VatDung, on_delete=models.CASCADE)
    ghi_chu = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        db_table = 'cung_duong_vat_dung_goi_y'
        verbose_name = _("Vật Dụng Gợi Ý")
        verbose_name_plural = _("Các Vật Dụng Gợi Ý")
        constraints = [ models.UniqueConstraint(fields=['cung_duong', 'vat_dung'], name='unique_trek_equipment_suggestion') ]

class CungDuongDanhGia(models.Model):
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE, related_name='danh_gia')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    diem_danh_gia = models.PositiveSmallIntegerField()
    binh_luan = models.TextField(blank=True, null=True)
    ngay_danh_gia = models.DateTimeField(_("Ngày đánh giá"), default=timezone.now)
    class Meta:
        db_table = 'cung_duong_danh_gia'
        verbose_name = _("Đánh Giá Cung Đường")
        verbose_name_plural = _("Các Đánh Giá Cung Đường")
        ordering = ['-ngay_danh_gia']
        constraints = [ models.UniqueConstraint(fields=['cung_duong', 'user'], name='unique_user_review_per_trek') ]

class CungDuongAnhDanhGia(models.Model):
    danh_gia = models.ForeignKey(CungDuongDanhGia, on_delete=models.CASCADE, related_name='anh_danh_gia')
    hinh_anh = models.ImageField(upload_to=get_review_media_path, validators=[validate_image_size])
    class Meta:
        db_table = 'cung_duong_anh_danh_gia'
        verbose_name = _("Ảnh Đánh Giá")
        verbose_name_plural = _("Các Ảnh Đánh Giá")

# ==============================================================================
# === SIGNALS ĐỂ TỰ ĐỘNG HÓA ===
# ==============================================================================

@receiver([post_save, post_delete], sender=CungDuongDanhGia)
def update_trek_rating_on_review_change(sender, instance, **kwargs):
    """
    Tự động cập nhật điểm trung bình và số lượt đánh giá của CungDuongTrek
    mỗi khi một đánh giá được tạo, sửa, hoặc xóa.
    """
    trek = instance.cung_duong
    aggregates = CungDuongDanhGia.objects.filter(cung_duong=trek).aggregate(
        avg_rating=Avg('diem_danh_gia'), 
        count_rating=Count('id')
    )
    trek.danh_gia_trung_binh = aggregates.get('avg_rating') or 0.00
    trek.so_luot_danh_gia = aggregates.get('count_rating') or 0
    trek.save(update_fields=['danh_gia_trung_binh', 'so_luot_danh_gia'])

@receiver(post_delete, sender=CungDuongMedia)
def delete_cungduong_media_file(sender, instance, **kwargs):
    """Tự động xóa file media chính khi object bị xóa."""
    if instance.file:
        instance.file.delete(save=False)

@receiver(post_delete, sender=CungDuongAnhDanhGia)
def delete_review_image_file(sender, instance, **kwargs):
    """Tự động xóa file ảnh review khi object bị xóa."""
    if instance.hinh_anh:
        instance.hinh_anh.delete(save=False)