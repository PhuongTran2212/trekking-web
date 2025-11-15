# articles/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone

class BaiHuongDan(models.Model):
    tieu_de = models.CharField(max_length=255, verbose_name="Tiêu đề")
    noi_dung = models.TextField(verbose_name="Nội dung")
    chuyen_muc = models.CharField(max_length=100, verbose_name="Chuyên mục")
    tac_gia = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='bai_huong_dan_da_viet', verbose_name="Tác giả")
    ngay_dang = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng")
    da_duyet = models.BooleanField(default=False, verbose_name="Đã duyệt")
    nguoi_duyet = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_staff': True}, related_name='bai_huong_dan_da_duyet', verbose_name="Người duyệt")
    ngay_duyet = models.DateTimeField(null=True, blank=True, verbose_name="Ngày duyệt")

    def __str__(self):
        return self.tieu_de

    class Meta:
        db_table = 'kien_thuc_bai_huong_dan'
        verbose_name = "Bài viết kiến thức"
        verbose_name_plural = "Các bài viết kiến thức"
        ordering = ['-ngay_dang']