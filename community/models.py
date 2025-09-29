# community/models.py
from django.db import models
from django.contrib.auth.models import User
from trips.models import ChuyenDi

class CongDongBaiViet(models.Model):
    tieu_de = models.CharField(max_length=255)
    noi_dung = models.TextField() # Trong Django, LONGTEXT được đại diện bởi TextField
    tac_gia = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bai_viet')
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.SET_NULL, blank=True, null=True)
    luot_binh_chon = models.IntegerField(default=0)
    ngay_dang = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ngay_dang']

    def __str__(self):
        return self.tieu_de

class CongDongMediaBaiViet(models.Model):
    bai_viet = models.ForeignKey(CongDongBaiViet, on_delete=models.CASCADE, related_name='media')

    ANH = 'Ảnh'
    VIDEO = 'Video'
    LOAI_MEDIA_CHOICES = [
        (ANH, 'Ảnh'),
        (VIDEO, 'Video'),
    ]
    loai_media = models.CharField(max_length=10, choices=LOAI_MEDIA_CHOICES)
    duong_dan_file = models.CharField(max_length=255)
    ngay_tai_len = models.DateTimeField(auto_now_add=True)

class CongDongBinhChonBaiViet(models.Model):
    bai_viet = models.ForeignKey(CongDongBaiViet, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ngay_binh_chon = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('bai_viet', 'user')

class CongDongBinhLuan(models.Model):
    bai_viet = models.ForeignKey(CongDongBaiViet, on_delete=models.CASCADE, related_name='binh_luan')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    noi_dung = models.TextField()
    tra_loi_binh_luan = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='cac_tra_loi')
    ngay_binh_luan = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ngay_binh_luan']