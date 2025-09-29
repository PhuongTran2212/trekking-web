# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import VatDung, The

class TaiKhoanHoSo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    sdt = models.CharField(max_length=15, blank=True, null=True, unique=True)
    anh_dai_dien = models.CharField(max_length=200, blank=True, null=True)
    gioi_thieu = models.TextField(blank=True, null=True)
    diem_thuong = models.IntegerField(default=0)
    
    def __str__(self):
        return self.user.username

class TaiKhoanThietBiCaNhan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vat_dung = models.ForeignKey(VatDung, on_delete=models.CASCADE)
    so_luong = models.IntegerField(default=1)
    ghi_chu = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        unique_together = ('user', 'vat_dung')

class TaiKhoanSoThichNguoiDung(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    the = models.ForeignKey(The, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'the')

@receiver(post_save, sender=User)
def ensure_user_profile_exists(sender, instance, **kwargs):
    TaiKhoanHoSo.objects.get_or_create(user=instance)