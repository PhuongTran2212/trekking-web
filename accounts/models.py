<<<<<<< HEAD
=======
# accounts/models.py

>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
<<<<<<< HEAD
from core.models import VatDung, The, TinhThanh

# === DI CHUYỂN RA NGOÀI: Định nghĩa class lựa chọn ở cấp cao nhất của file ===
class GioiTinh(models.TextChoices):
    NAM = 'M', 'Nam'
    NU = 'F', 'Nữ'
    KHAC = 'O', 'Khác'
=======
from core.models import VatDung, The
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43

class TaiKhoanHoSo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    sdt = models.CharField(max_length=15, blank=True, null=True, unique=True)
<<<<<<< HEAD
    gioi_thieu = models.TextField(blank=True, null=True)
    diem_thuong = models.IntegerField(default=0)
    
    ngay_sinh = models.DateField(blank=True, null=True, verbose_name="Ngày sinh")
    gioi_tinh = models.CharField(
        max_length=1,
        choices=GioiTinh.choices, # Tham chiếu tới class GioiTinh độc lập
        blank=True,
        null=True,
        verbose_name="Giới tính"
    )

    tinh_thanh = models.ForeignKey(
        TinhThanh, 
        on_delete=models.SET_NULL,
        blank=True, 
        null=True,
        verbose_name="Tỉnh/Thành phố"
    )
    anh_dai_dien = models.ImageField(
        upload_to='avatars/',
        blank=True, 
        null=True,
        default='avatars/default_avatar.png' 
    )
    
    def __str__(self):
        return self.user.username
        
    @property
    def avatar_url(self):
        try:
            url = self.anh_dai_dien.url
        except (ValueError, AttributeError):
            url = '/static/images/default_avatar.png'
        return url
=======
    anh_dai_dien = models.CharField(max_length=200, blank=True, null=True)
    gioi_thieu = models.TextField(blank=True, null=True)
    diem_thuong = models.IntegerField(default=0)
    
    def __str__(self):
        return self.user.username
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43

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