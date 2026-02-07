# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class TinhThanh(models.Model):
    ten = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.ten

class The(models.Model):
    ten = models.CharField(max_length=50, unique=True)
    slug = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.ten

class LoaiVatDung(models.Model):
    ten = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.ten

class VatDung(models.Model):
    ten = models.CharField(max_length=150)
    mo_ta = models.TextField(blank=True, null=True)
    loai_vat_dung = models.ForeignKey(LoaiVatDung, on_delete=models.CASCADE)
    def __str__(self): return self.ten

class DoKho(models.Model):
    ten = models.CharField(max_length=50, unique=True)
    mo_ta = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self): return self.ten

<<<<<<< HEAD
# class TrangThaiChuyenDi(models.Model):
#     ten = models.CharField(max_length=100, unique=True)
#     def __str__(self): return self.ten
=======
class TrangThaiChuyenDi(models.Model):
    ten = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.ten
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
# =================================================================================
# === KHỐI 10 & 12: HỆ THỐNG THÔNG BÁO & BÁO CÁO ===
# =================================================================================

class HeThongThongBao(models.Model):
    nguoi_nhan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='thong_bao')
    tieu_de = models.CharField(max_length=150, default="Thông báo mới")
    noi_dung = models.CharField(max_length=255)
    lien_ket = models.CharField(max_length=255, null=True, blank=True)
    da_doc = models.BooleanField(default=False)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'he_thong_thong_bao'
        ordering = ['-ngay_tao']
        indexes = [models.Index(fields=['nguoi_nhan', '-ngay_tao'])]
        verbose_name = "Thông báo Hệ thống"
        verbose_name_plural = "Các Thông báo Hệ thống"

    def __str__(self):
        # Cập nhật lại để hiển thị tiêu đề
        return f"Thông báo cho {self.nguoi_nhan.username}: {self.tieu_de}"

class HeThongBaoCao(models.Model):
    class TrangThaiBaoCao(models.TextChoices):
        MOI = 'Mới', 'Mới'
        DANG_XU_LY = 'Đang xử lý', 'Đang xử lý'
        DA_XU_LY = 'Đã xử lý', 'Đã xử lý'

    nguoi_bao_cao = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bao_cao_da_gui')
    ly_do_bao_cao = models.TextField()
    ngay_bao_cao = models.DateTimeField(auto_now_add=True)

    # GenericForeignKey để báo cáo được nhiều loại đối tượng
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    trang_thai = models.CharField(max_length=20, choices=TrangThaiBaoCao.choices, default=TrangThaiBaoCao.MOI)
    nguoi_xu_ly = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bao_cao_da_xu_ly')
    ghi_chu_xu_ly = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'he_thong_bao_cao'
        ordering = ['-ngay_bao_cao']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['trang_thai']),
        ]

    def __str__(self):
        return f"Báo cáo từ {self.nguoi_bao_cao.username}"