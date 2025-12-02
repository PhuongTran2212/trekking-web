# gamification/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .services import BadgeEngine

# Import các Model cần theo dõi từ các App khác
from trips.models import ChuyenDiThanhVien
from community.models import CongDongBaiViet, CongDongBinhLuan

# 1. Lắng nghe khi có thay đổi về Thành Viên Chuyến Đi (Tham gia/Hoàn thành)
@receiver(post_save, sender=ChuyenDiThanhVien)
def check_badges_on_trip_update(sender, instance, created, **kwargs):
    # Chỉ kiểm tra nếu trạng thái là 'DA_THAM_GIA' (hoặc trạng thái hoàn thành tùy logic của bạn)
    if instance.trang_thai_tham_gia == 'DA_THAM_GIA':
        print(f"⚡ Signal: Checking badges for user {instance.user.username} (Trip Action)")
        engine = BadgeEngine()
        engine.check_all_badges(instance.user)

# 2. Lắng nghe khi người dùng Đăng Bài Viết
@receiver(post_save, sender=CongDongBaiViet)
def check_badges_on_post(sender, instance, created, **kwargs):
    if created: # Chỉ tính khi tạo mới, không tính khi sửa
        print(f"⚡ Signal: Checking badges for user {instance.tac_gia.username} (New Post)")
        engine = BadgeEngine()
        engine.check_all_badges(instance.tac_gia)

# 3. Lắng nghe khi người dùng Bình Luận
@receiver(post_save, sender=CongDongBinhLuan)
def check_badges_on_comment(sender, instance, created, **kwargs):
    if created:
        print(f"⚡ Signal: Checking badges for user {instance.user.username} (New Comment)")
        engine = BadgeEngine()
        engine.check_all_badges(instance.user)