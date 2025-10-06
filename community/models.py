# cSpell:disable

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import The  # Đảm bảo đã import model The
from trips.models import ChuyenDi

class CongDongBaiViet(models.Model):
    """Model cho bài viết trong cộng đồng"""
    
    class TrangThaiBaiViet(models.TextChoices):
        CHO_DUYET = 'cho_duyet', 'Chờ duyệt'
        DA_DUYET = 'da_duyet', 'Đã duyệt'
        TU_CHOI = 'tu_choi', 'Từ chối'
    
    tieu_de = models.CharField(max_length=255, verbose_name="Tiêu đề")
    noi_dung = models.TextField(verbose_name="Nội dung")
    tac_gia = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='bai_viet_cong_dong',
        verbose_name="Tác giả"
    )
    # === THÊM TRƯỜNG TAGS VÀO ĐÂY ===
    tags = models.ManyToManyField(
        The,
        related_name='bai_viet_cong_dong',
        blank=True,
        verbose_name="Các thẻ"
    )
    # ==================================
    
    luot_binh_chon = models.IntegerField(default=0, verbose_name="Lượt bình chọn")
    ngay_dang = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng")
    ngay_cap_nhat = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    
    trang_thai = models.CharField(
        max_length=20,
        choices=TrangThaiBaiViet.choices,
        default=TrangThaiBaiViet.CHO_DUYET,
        verbose_name="Trạng thái"
    )
    
    chuyen_di = models.ForeignKey(
        ChuyenDi,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bai_viet_lien_quan',
        verbose_name="Chuyến đi"
    )
    
    class Meta:
        db_table = 'community_congdongbaiviet'
        ordering = ['-ngay_dang']
        verbose_name = "Bài viết cộng đồng"
        verbose_name_plural = "Các bài viết cộng đồng"
        indexes = [
            models.Index(fields=['-ngay_dang']),
            models.Index(fields=['trang_thai']),
        ]
    
    def __str__(self):
        return self.tieu_de
    
    def so_luong_binh_luan(self):
        return self.binh_luan.count()
    
    def da_binh_chon(self, user):
        if not user.is_authenticated:
            return False
        return self.binh_chon.filter(user=user).exists()

class CongDongMediaBaiViet(models.Model):
    # ... các model còn lại giữ nguyên ...
    """Model cho media (ảnh/video) của bài viết"""
    
    class LoaiMedia(models.TextChoices):
        ANH = 'anh', 'Ảnh'
        VIDEO = 'video', 'Video'
    
    bai_viet = models.ForeignKey(
        CongDongBaiViet,
        on_delete=models.CASCADE,
        related_name='media',
        verbose_name="Bài viết"
    )
    loai_media = models.CharField(
        max_length=10,
        choices=LoaiMedia.choices,
        verbose_name="Loại media"
    )
    duong_dan_file = models.FileField(
        upload_to='community/',
        verbose_name="File"
    )
    ngay_tai_len = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tải lên")
    
    class Meta:
        db_table = 'community_congdongmediabaiviet'
        ordering = ['ngay_tai_len']
        verbose_name = "Media bài viết"
        verbose_name_plural = "Media các bài viết"
    
    def __str__(self):
        return f"{self.loai_media} - {self.bai_viet.tieu_de}"


class CongDongBinhChonBaiViet(models.Model):
    """Model cho upvote bài viết"""
    
    bai_viet = models.ForeignKey(
        CongDongBaiViet,
        on_delete=models.CASCADE,
        related_name='binh_chon',
        verbose_name="Bài viết"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='binh_chon_bai_viet',
        verbose_name="Người dùng"
    )
    ngay_binh_chon = models.DateTimeField(auto_now_add=True, verbose_name="Ngày bình chọn")
    
    class Meta:
        db_table = 'community_congdongbinhchonbaiviet'
        unique_together = ['bai_viet', 'user']
        verbose_name = "Bình chọn bài viết"
        verbose_name_plural = "Các bình chọn bài viết"
    
    def __str__(self):
        return f"{self.user.username} - {self.bai_viet.tieu_de}"


class CongDongBinhLuan(models.Model):
    """Model cho bình luận"""
    
    bai_viet = models.ForeignKey(
        CongDongBaiViet,
        on_delete=models.CASCADE,
        related_name='binh_luan',
        verbose_name="Bài viết"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='binh_luan_cong_dong',
        verbose_name="Người dùng"
    )
    noi_dung = models.TextField(verbose_name="Nội dung")
    ngay_binh_luan = models.DateTimeField(auto_now_add=True, verbose_name="Ngày bình luận")
    
    tra_loi_binh_luan = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cac_tra_loi',
        verbose_name="Trả lời bình luận"
    )
    
    class Meta:
        db_table = 'community_congdongbinhluan'
        ordering = ['ngay_binh_luan']
        verbose_name = "Bình luận"
        verbose_name_plural = "Các bình luận"
    
    def __str__(self):
        return f"{self.user.username} - {self.bai_viet.tieu_de}"
    
    def so_luong_tra_loi(self):
        return self.cac_tra_loi.count()