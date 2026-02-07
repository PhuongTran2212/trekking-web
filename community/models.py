<<<<<<< HEAD
import os
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify # Import để xử lý tên file
from core.models import The
from trips.models import ChuyenDi

# --- HÀM TẠO ĐƯỜNG DẪN MEDIA ---
def tao_duong_dan_media(instance, filename):
    """
    Tạo đường dẫn: community/slug-tieu-de/id-bai-viet/filename
    Giúp quản lý file gọn gàng và tránh trùng lặp.
    """
    # Chuyển tiêu đề thành slug (ví dụ: "Ảnh Đẹp" -> "anh-dep")
    # Nếu bài viết chưa có tiêu đề (lúc tạo mới chưa save), dùng 'unsaved'
    tieu_de = instance.bai_viet.tieu_de if instance.bai_viet.tieu_de else "unsaved"
    slug = slugify(tieu_de)[:50] # Lấy tối đa 50 ký tự slug
    
    # ID bài viết
    bai_viet_id = str(instance.bai_viet.id)
    
    return os.path.join('community', slug, bai_viet_id, filename)
# -------------------------------

class CongDongBaiViet(models.Model):
    """Model cho bài viết trong cộng đồng"""
    def get_absolute_url(self):
        return reverse('community:chi-tiet-bai-viet', args=[self.id])

    def get_edit_url(self):
        return reverse('community:sua-bai-viet', args=[self.id])
       
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
    tags = models.ManyToManyField(
        The,
        related_name='bai_viet_cong_dong',
        blank=True,
        verbose_name="Các thẻ"
    )
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
    # SỬ DỤNG HÀM TẠO ĐƯỜNG DẪN MỚI TẠI ĐÂY
    duong_dan_file = models.FileField(
        upload_to=tao_duong_dan_media, 
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
=======
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
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
