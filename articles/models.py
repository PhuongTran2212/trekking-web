from django.db import models
from django.conf import settings
from django.utils.text import slugify
import itertools

# ==========================================================
# === Đảm bảo class ChuyenMuc này tồn tại ở đầu file ===
# ==========================================================
class ChuyenMuc(models.Model):
    ten = models.CharField(max_length=100, unique=True, verbose_name="Tên chuyên mục")
    slug = models.SlugField(max_length=110, unique=True, blank=True, help_text="Tự động tạo nếu bỏ trống")

    class Meta:
        verbose_name = "Chuyên mục"
        verbose_name_plural = "Các chuyên mục"
        ordering = ['ten']

    def __str__(self):
        return self.ten

    # === THAY THẾ PHƯƠNG THỨC NÀY ===
    def save(self, *args, **kwargs):
        # Luôn tạo slug mới từ 'ten' mỗi khi lưu
        base_slug = slugify(self.ten)
        self.slug = base_slug
        
        # Vòng lặp để đảm bảo slug là duy nhất
        for i in itertools.count(1):
            # Kiểm tra xem có đối tượng nào khác (exclude self.pk) có cùng slug không
            if not ChuyenMuc.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                break
            # Nếu có, thêm hậu tố -1, -2, ...
            self.slug = f'{base_slug}-{i}'
            
        super().save(*args, **kwargs)


class BaiHuongDan(models.Model):
    tieu_de = models.CharField(max_length=255, verbose_name="Tiêu đề")
    noi_dung = models.TextField(verbose_name="Nội dung")

    # TRƯỜNG CŨ: GIỮ NGUYÊN TẠM THỜI
    chuyen_muc_old = models.CharField(max_length=100, verbose_name="Chuyên mục cũ", null=True)

    # TRƯỜNG MỚI: ĐÂY LÀ THAY ĐỔI QUAN TRỌNG
    chuyen_muc = models.ForeignKey(
        ChuyenMuc,
        on_delete=models.SET_NULL,
        null=True,  # CHO PHÉP RỖNG TRONG DATABASE
        blank=True, # CHO PHÉP RỖNG TRONG FORM
        verbose_name="Chuyên mục"
    )

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