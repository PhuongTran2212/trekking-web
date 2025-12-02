from django.db import models
from django.contrib.auth.models import User

class GameHuyHieu(models.Model):
    # --- DANH SÁCH CÁC LOẠI ĐIỀU KIỆN (Logic System) ---
    CONDITION_TYPES = [
        # 1. Nhóm đếm số lượng (Count)
        ('COUNT_TRIPS', 'Số chuyến đi tham gia (Người tham gia)'),
        ('COUNT_HOSTED_TRIPS', 'Số chuyến đi tổ chức (Host)'),
        ('COUNT_POSTS', 'Số bài viết cộng đồng'),
        ('COUNT_COMMENTS', 'Số bình luận đã viết'),
        ('COUNT_MESSAGES', 'Số tin nhắn đã gửi'),
        ('COUNT_PHOTOS', 'Số hình ảnh đã tải lên'),
        ('COUNT_REVIEWS', 'Số đánh giá cung đường đã viết'),
        ('COUNT_CHECKINS', 'Số lần check-in nhật ký hành trình'),
        ('COUNT_ITEMS', 'Số món đồ trong trang bị cá nhân'),
        ('COUNT_COLLECTED_BADGES', 'Số huy hiệu khác đã đạt được'),
        
        # 2. Nhóm tính tổng (Sum)
        ('SUM_DISTANCE', 'Tổng quãng đường trekking (km)'),
        ('SUM_ELEVATION', 'Tổng độ cao đã leo (m)'),
        ('SUM_VOTES_RECEIVED', 'Tổng lượt thích/bình chọn nhận được'),
        ('SUM_REPLIES_RECEIVED', 'Tổng lượt phản hồi nhận được'),

        # 3. Nhóm điều kiện đặc biệt (Special & Parametrized)
        ('HAS_TAG_COUNT', 'Tham gia chuyến đi có Tag cụ thể (Cần nhập biến số phụ)'),
        ('VISIT_PROVINCE_COUNT', 'Số tỉnh thành khác nhau đã đặt chân đến'),
        ('FULL_PROFILE', 'Đã cập nhật đầy đủ hồ sơ (Avatar, SĐT, Giới thiệu...)'),
        ('NO_CANCEL_STREAK', 'Chuỗi chuyến đi tổ chức không bị hủy (cho Host)'),
        ('PUNCTUALITY_STREAK', 'Chuỗi check-in đúng giờ liên tiếp'),
        ('DIFFICULTY_LEVEL', 'Hoàn thành cung đường độ khó cụ thể (Cần nhập biến số phụ)'),
        ('MAX_PARTICIPANTS', 'Tổ chức chuyến đi đạt tối đa số người'),
        ('APPROVED_CONTRIBUTION', 'Đóng góp cung đường mới được duyệt'),
    ]

    # Các toán tử so sánh logic
    OPERATORS = [
        ('GTE', 'Lớn hơn hoặc bằng (>=)'),
        ('EQ', 'Bằng chính xác (==)'),
    ]

    # --- THÔNG TIN CƠ BẢN ---
    ten = models.CharField(max_length=100, unique=True, verbose_name="Tên huy hiệu")
    mo_ta = models.TextField(verbose_name="Mô tả")
    anh_huy_hieu = models.ImageField(
        upload_to='badges/',  # Ảnh sẽ được lưu vào thư mục media/badges/
        verbose_name="Ảnh huy hiệu",
        default='badges/default.png' # Ảnh mặc định nếu không up
    )
    # Lưu ý: Bạn có thể dùng models.ImageField(upload_to='badges/') nếu muốn upload file thật
    
    # --- CẤU HÌNH LOGIC (RULE ENGINE) ---
    loai_dieu_kien = models.CharField(
        max_length=50, 
        choices=CONDITION_TYPES, 
        default='COUNT_TRIPS',
        verbose_name="Loại điều kiện",
        help_text="Hệ thống sẽ dựa vào loại này để tính toán."
    )
    
    gia_tri_muc_tieu = models.IntegerField(
        default=1, 
        verbose_name="Giá trị mục tiêu",
        help_text="Con số cần đạt được (Ví dụ: 5 chuyến, 100km, 1 lần)."
    )
    
    bien_so_phu = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Biến số phụ (Slug/Tag/Code)",
        help_text="Nhập slug của tag (vd: 'san-may'), độ khó (vd: 'kho'), hoặc để trống nếu không cần."
    )

    toan_tu = models.CharField(
        max_length=10, 
        choices=OPERATORS, 
        default='GTE',
        verbose_name="Toán tử so sánh"
    )

    is_active = models.BooleanField(default=True, verbose_name="Đang kích hoạt")

    def __str__(self):
        return f"{self.ten} [{self.loai_dieu_kien} >= {self.gia_tri_muc_tieu}]"

    class Meta:
        verbose_name = "Huy Hiệu"
        verbose_name_plural = "Quản lý Huy Hiệu"


class GameHuyHieuNguoiDung(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    huy_hieu = models.ForeignKey(GameHuyHieu, on_delete=models.CASCADE)
    ngay_dat_duoc = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'huy_hieu')
        verbose_name = "Huy hiệu người dùng"
        verbose_name_plural = "Danh sách người dùng đạt huy hiệu"

    def __str__(self):
        return f"{self.user.username} - {self.huy_hieu.ten}"