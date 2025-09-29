# treks/models.py
from django.db import models
from django.contrib.auth.models import User
from core.models import TinhThanh, DoKho, VatDung

class CungDuongTrek(models.Model):
    ten = models.CharField(max_length=200)
    slug = models.CharField(unique=True, max_length=220)
    mo_ta = models.TextField()
    anh_bia = models.CharField(max_length=200)
    tinh_thanh = models.ForeignKey(TinhThanh, on_delete=models.PROTECT)
    do_dai_km = models.DecimalField(max_digits=5, decimal_places=2)
    thoi_gian_uoc_tinh_gio = models.IntegerField()
    tong_do_cao_leo_m = models.IntegerField(blank=True, null=True)
    do_kho = models.ForeignKey(DoKho, on_delete=models.PROTECT)
    mua_dep_nhat = models.CharField(max_length=100, blank=True, null=True)
    du_lieu_ban_do_geojson = models.JSONField(blank=True, null=True)
    danh_gia_trung_binh = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    so_luot_danh_gia = models.IntegerField(default=0)
    da_duyet = models.BooleanField(default=True)
    nguoi_tao = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cung_duong_trek'
        verbose_name = "Cung Đường Trek"
        verbose_name_plural = "Các Cung Đường Trek"

    def __str__(self):
        return self.ten

class CungDuongDanhGia(models.Model):
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    diem_danh_gia = models.PositiveSmallIntegerField()
    binh_luan = models.TextField(blank=True, null=True)
    ngay_danh_gia = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cung_duong_danh_gia'
        unique_together = (('cung_duong', 'user'),)
        verbose_name = "Đánh Giá Cung Đường"
        verbose_name_plural = "Các Đánh Giá Cung Đường"

class CungDuongAnhDanhGia(models.Model):
    danh_gia = models.ForeignKey(CungDuongDanhGia, on_delete=models.CASCADE)
    hinh_anh = models.CharField(max_length=200)

    class Meta:
        db_table = 'cung_duong_anh_danh_gia'
        verbose_name = "Ảnh Đánh Giá"
        verbose_name_plural = "Các Ảnh Đánh Giá"

class CungDuongVatDungGoiY(models.Model):
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.CASCADE)
    vat_dung = models.ForeignKey(VatDung, on_delete=models.CASCADE)
    ghi_chu = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'cung_duong_vat_dung_goi_y'
        verbose_name = "Vật Dụng Gợi Ý"
        verbose_name_plural = "Các Vật Dụng Gợi Ý"