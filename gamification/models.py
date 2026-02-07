<<<<<<< HEAD
=======
# gamification/models.py
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
from django.db import models
from django.contrib.auth.models import User

class GameHuyHieu(models.Model):
<<<<<<< HEAD
    # --- DANH SÁCH ĐIỀU KIỆN ---
    CONDITION_TYPES = [
        ('COUNT_TRIPS', 'Số chuyến đi tham gia'),
        ('COUNT_HOSTED_TRIPS', 'Số chuyến đi tổ chức'),
        ('COUNT_POSTS', 'Số bài viết cộng đồng'),
        ('COUNT_COMMENTS', 'Số bình luận'),
        ('COUNT_MESSAGES', 'Số tin nhắn'),
        ('COUNT_PHOTOS', 'Số hình ảnh tải lên'),
        ('COUNT_REVIEWS', 'Số đánh giá cung đường'),
        ('COUNT_ITEMS', 'Số món đồ trang bị'),
        ('COUNT_COLLECTED_BADGES', 'Số huy hiệu đã đạt'),
        ('SUM_DISTANCE', 'Tổng quãng đường (km)'),
        ('SUM_ELEVATION', 'Tổng độ cao leo (m)'),
        ('HAS_TAG_COUNT', 'Tham gia chuyến đi có Tag (slug)'),
        ('VISIT_PROVINCE_COUNT', 'Số tỉnh thành đã đến'),
        ('DIFFICULTY_LEVEL', 'Độ khó cung đường (tên độ khó)'),
    ]

    # --- THÔNG TIN CƠ BẢN ---
    ten = models.CharField(max_length=100, unique=True, verbose_name="Tên huy hiệu")
    mo_ta = models.TextField(verbose_name="Mô tả")
    anh_huy_hieu = models.ImageField(
        upload_to='badges/', 
        verbose_name="Ảnh huy hiệu",
        default='badges/default.png'
    )
    
    # --- CẤU HÌNH LOGIC ---
    loai_dieu_kien = models.CharField(
        max_length=50, 
        choices=CONDITION_TYPES, 
        default='COUNT_TRIPS',
        verbose_name="Loại điều kiện"
    )
    
    gia_tri_muc_tieu = models.IntegerField(
        default=1, 
        verbose_name="Giá trị mục tiêu",
        help_text="Con số cần đạt được (>=)"
    )
    
    bien_so_phu = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Biến số phụ",
        help_text="Nhập slug tag hoặc tên độ khó nếu cần."
    )

    # ĐÃ XÓA TRƯỜNG toan_tu TẠI ĐÂY

    is_active = models.BooleanField(default=True, verbose_name="Đang kích hoạt")

    def __str__(self):
        return f"{self.ten} [{self.loai_dieu_kien} >= {self.gia_tri_muc_tieu}]"

    class Meta:
        verbose_name = "Huy Hiệu"
        verbose_name_plural = "Quản lý Huy Hiệu"

class GameHuyHieuNguoiDung(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
=======
    ten = models.CharField(max_length=100, unique=True)
    mo_ta = models.TextField()
    anh_huy_hieu = models.CharField(max_length=200)

    def __str__(self):
        return self.ten

class GameHuyHieuNguoiDung(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
    huy_hieu = models.ForeignKey(GameHuyHieu, on_delete=models.CASCADE)
    ngay_dat_duoc = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'huy_hieu')
<<<<<<< HEAD
        verbose_name = "Huy hiệu người dùng"
        verbose_name_plural = "Danh sách người dùng đạt huy hiệu"

    def __str__(self):
        return f"{self.user.username} - {self.huy_hieu.ten}"
=======
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
