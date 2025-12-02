from django.db.models.signals import post_save
from django.dispatch import receiver
from .services import BadgeEngine
import logging

logger = logging.getLogger(__name__)

# Import Models
from .models import GameHuyHieu, GameHuyHieuNguoiDung
from trips.models import ChuyenDiThanhVien, ChuyenDi, ChuyenDiTinNhan, ChuyenDiMedia
from community.models import CongDongBaiViet, CongDongBinhLuan, CongDongMediaBaiViet
from treks.models import CungDuongDanhGia
from accounts.models import TaiKhoanThietBiCaNhan

def run_badge_check_safely(user, action_name):
    try:
        if user:
            # print(f"⚡ Checking: {user.username} - {action_name}")
            BadgeEngine().check_all_badges(user)
    except Exception as e:
        logger.error(f"❌ Error {action_name}: {e}")
        # ==========================================================
# PHẦN 1: TỰ ĐỘNG QUÉT KHI ADMIN TẠO HOẶC SỬA HUY HIỆU
# ==========================================================
@receiver(post_save, sender=GameHuyHieu)
def auto_sync_on_admin_save(sender, instance, created, **kwargs):
    """
    Hàm này chạy ngay lập tức khi Admin bấm nút LƯU (SAVE).
    - Nếu Tạo mới: Quét xem ai đủ điều kiện thì trao luôn (Truy lĩnh).
    - Nếu Sửa: Quét lại xem ai thiếu thì thu hồi, ai đủ thì trao thêm.
    """
    action_type = "Tạo mới" if created else "Cập nhật"
    print(f"⚙️ [AUTO SYNC] Admin vừa {action_type} huy hiệu '{instance.ten}'. Đang rà soát toàn bộ User...")
    
    try:
        # Gọi hàm đồng bộ trong services.py
        added, removed = BadgeEngine().sync_badge_for_all_users(instance)
        print(f"✅ [KẾT QUẢ] Đã trao: {added} người | Đã thu hồi: {removed} người.")
    except Exception as e:
        logger.error(f"❌ Lỗi Auto Sync: {e}")

# --- NHÓM 1: CHUYẾN ĐI ---
@receiver(post_save, sender=ChuyenDiThanhVien)
def on_trip_member_update(sender, instance, created, **kwargs):
    if instance.trang_thai_tham_gia == 'DA_THAM_GIA':
        run_badge_check_safely(instance.user, "Trip Joined")

@receiver(post_save, sender=ChuyenDi)
def on_trip_host_update(sender, instance, created, **kwargs):
    if instance.trang_thai != 'DA_HUY' and instance.nguoi_to_chuc:
        run_badge_check_safely(instance.nguoi_to_chuc, "Host Trip")

@receiver(post_save, sender=ChuyenDiTinNhan)
def on_trip_message(sender, instance, created, **kwargs):
    if created: run_badge_check_safely(instance.nguoi_gui, "Sent Message")

# --- NHÓM 2: CỘNG ĐỒNG ---
@receiver(post_save, sender=CongDongBaiViet)
def on_post_created(sender, instance, created, **kwargs):
    if created: run_badge_check_safely(instance.tac_gia, "New Post")

@receiver(post_save, sender=CongDongBinhLuan)
def on_comment_created(sender, instance, created, **kwargs):
    if created: run_badge_check_safely(instance.user, "New Comment")

@receiver(post_save, sender=CongDongMediaBaiViet)
def on_media_uploaded(sender, instance, created, **kwargs):
    if created: 
        try: run_badge_check_safely(instance.bai_viet.tac_gia, "Media Upload")
        except: pass

@receiver(post_save, sender=ChuyenDiMedia)
def on_trip_media_uploaded(sender, instance, created, **kwargs):
    if created: run_badge_check_safely(instance.user, "Trip Photo")

# --- NHÓM 3: KHÁC ---
@receiver(post_save, sender=CungDuongDanhGia)
def on_trek_review(sender, instance, created, **kwargs):
    run_badge_check_safely(instance.user, "Review Trek")

@receiver(post_save, sender=TaiKhoanThietBiCaNhan)
def on_item_update(sender, instance, created, **kwargs):
    run_badge_check_safely(instance.user, "Equipment")

@receiver(post_save, sender=GameHuyHieuNguoiDung)
def on_badge_earned(sender, instance, created, **kwargs):
    if created: run_badge_check_safely(instance.user, "Badge Collection")

# --- PHẦN MỚI: TỰ ĐỘNG ĐỒNG BỘ KHI ADMIN SỬA HUY HIỆU ---
@receiver(post_save, sender=GameHuyHieu)
def auto_sync_on_badge_change(sender, instance, created, **kwargs):
    print(f"⚙️ [AUTO SYNC] Huy hiệu '{instance.ten}' thay đổi -> Quét lại toàn bộ User...")
    try:
        added, removed = BadgeEngine().sync_badge_for_all_users(instance)
        print(f"✅ Kết quả: +{added} người nhận mới, -{removed} người bị thu hồi.")
    except Exception as e:
        logger.error(f"❌ Auto Sync Failed: {e}")