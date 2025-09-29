# trips/models.py
from django.db import models
from django.contrib.auth.models import User
from core.models import TrangThaiChuyenDi
from treks.models import CungDuongTrek

class ChuyenDi(models.Model):
    ten_chuyen_di = models.CharField(max_length=200)
    mo_ta = models.TextField(blank=True, null=True, help_text='Mô tả chi tiết, lịch trình, yêu cầu cho chuyến đi')
    cung_duong = models.ForeignKey(CungDuongTrek, on_delete=models.RESTRICT)
    nguoi_to_chuc = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chuyen_di_da_to_chuc')
    ngay_bat_dau = models.DateTimeField()
    so_luong_toi_da = models.IntegerField()
    trang_thai = models.ForeignKey(TrangThaiChuyenDi, on_delete=models.PROTECT)
    
    # ENUM Fields
    CONG_KHAI = 'Công khai'
    RIENG_TU = 'Riêng tư'
    CHE_DO_RIENG_TU_CHOICES = [
        (CONG_KHAI, 'Công khai'),
        (RIENG_TU, 'Riêng tư'),
    ]
    che_do_rieng_tu = models.CharField(max_length=15, choices=CHE_DO_RIENG_TU_CHOICES, default=CONG_KHAI)
    
    ma_moi = models.CharField(max_length=20, unique=True, blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ten_chuyen_di

class ChuyenDiThanhVien(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='thanh_vien')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chuyen_di_da_tham_gia')

    # ENUM Fields
    TRUONG_DOAN = 'Trưởng đoàn'
    THANH_VIEN = 'Thành viên'
    VAI_TRO_CHOICES = [
        (TRUONG_DOAN, 'Trưởng đoàn'),
        (THANH_VIEN, 'Thành viên'),
    ]
    vai_tro = models.CharField(max_length=15, choices=VAI_TRO_CHOICES, default=THANH_VIEN)

    CHO_DUYET = 'Chờ duyệt'
    DA_DUYET = 'Đã duyệt'
    TU_CHOI = 'Từ chối'
    TRANG_THAI_THAM_GIA_CHOICES = [
        (CHO_DUYET, 'Chờ duyệt'),
        (DA_DUYET, 'Đã duyệt'),
        (TU_CHOI, 'Từ chối'),
    ]
    trang_thai_tham_gia = models.CharField(max_length=15, choices=TRANG_THAI_THAM_GIA_CHOICES, default=CHO_DUYET)
    
    ngay_tham_gia = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('chuyen_di', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.chuyen_di.ten_chuyen_di}'

class ChuyenDiTinNhan(models.Model):
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE, related_name='tin_nhan')
    nguoi_gui = models.ForeignKey(User, on_delete=models.CASCADE)
    tra_loi_tin_nhan = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='cac_tra_loi')
    noi_dung = models.TextField(blank=True, null=True)
    thoi_gian_gui = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['thoi_gian_gui']

class ChuyenDiTinNhanMedia(models.Model):
    tin_nhan = models.ForeignKey(ChuyenDiTinNhan, on_delete=models.CASCADE, related_name='media')
    
    ANH = 'Ảnh'
    VIDEO = 'Video'
    FILE = 'File'
    LOAI_MEDIA_CHOICES = [
        (ANH, 'Ảnh'),
        (VIDEO, 'Video'),
        (FILE, 'File'),
    ]
    loai_media = models.CharField(max_length=10, choices=LOAI_MEDIA_CHOICES)
    
    duong_dan_file = models.CharField(max_length=255)
    thu_tu = models.PositiveSmallIntegerField(default=0)
    ten_file_goc = models.CharField(max_length=255, blank=True, null=True)
    kich_thuoc_file_kb = models.IntegerField(blank=True, null=True)

class ChuyenDiNhatKyHanhTrinh(models.Model):
    thanh_vien = models.ForeignKey(ChuyenDiThanhVien, on_delete=models.CASCADE)
    chuyen_di = models.ForeignKey(ChuyenDi, on_delete=models.CASCADE)
    vi_do = models.DecimalField(max_digits=9, decimal_places=6)
    kinh_do = models.DecimalField(max_digits=9, decimal_places=6)
    do_cao = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    noi_dung_checkin = models.CharField(max_length=255, blank=True, null=True)
    hinh_anh_checkin = models.CharField(max_length=255, blank=True, null=True)
    thoi_gian_checkin = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['thoi_gian_checkin']