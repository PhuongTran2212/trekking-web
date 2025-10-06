# knowledge/models.py
from django.db import models
from django.contrib.auth.models import User

class KienThucBaiHuongDan(models.Model):
    tieu_de = models.CharField(max_length=255)
    noi_dung = models.TextField()
    chuyen_muc = models.CharField(max_length=100)
    tac_gia = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    ngay_dang = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ngay_dang']

    def __str__(self):
        return self.tieu_de