from django.db.models import Count, Sum
from django.utils import timezone
from django.contrib.auth.models import User
from .models import GameHuyHieu, GameHuyHieuNguoiDung

# Import Models khác
from trips.models import ChuyenDiThanhVien, ChuyenDi, ChuyenDiTinNhan, ChuyenDiMedia
from community.models import CongDongBaiViet, CongDongBinhLuan, CongDongMediaBaiViet
from treks.models import CungDuongDanhGia
from accounts.models import TaiKhoanThietBiCaNhan

class BadgeEngine:
    def check_all_badges(self, user):
        if not user or not user.is_authenticated:
            return []
        active_badges = GameHuyHieu.objects.filter(is_active=True)
        owned_badge_ids = GameHuyHieuNguoiDung.objects.filter(user=user).values_list('huy_hieu_id', flat=True)
        new_badges = []
        for badge in active_badges:
            if badge.id in owned_badge_ids: continue
            if self.calculate_metric(user, badge) >= badge.gia_tri_muc_tieu:
                self.award_badge(user, badge)
                new_badges.append(badge)
        return new_badges

    def calculate_metric(self, user, badge):
        code = badge.loai_dieu_kien
        sub = badge.bien_so_phu
        
        if code == 'COUNT_TRIPS': return ChuyenDiThanhVien.objects.filter(user=user, trang_thai_tham_gia='DA_THAM_GIA').count()
        elif code == 'COUNT_HOSTED_TRIPS': return ChuyenDi.objects.filter(nguoi_to_chuc=user).exclude(trang_thai='DA_HUY').count()
        elif code == 'COUNT_POSTS': return CongDongBaiViet.objects.filter(tac_gia=user).count()
        elif code == 'COUNT_COMMENTS': return CongDongBinhLuan.objects.filter(user=user).count()
        elif code == 'COUNT_MESSAGES': return ChuyenDiTinNhan.objects.filter(nguoi_gui=user, da_xoa=False).count()
        elif code == 'COUNT_PHOTOS':
            return ChuyenDiMedia.objects.filter(user=user).count() + CongDongMediaBaiViet.objects.filter(bai_viet__tac_gia=user).count()
        elif code == 'COUNT_REVIEWS': return CungDuongDanhGia.objects.filter(user=user).count()
        elif code == 'COUNT_ITEMS': return TaiKhoanThietBiCaNhan.objects.filter(user=user).count()
        elif code == 'COUNT_COLLECTED_BADGES': return GameHuyHieuNguoiDung.objects.filter(user=user).count()
        
        elif code == 'SUM_DISTANCE':
            res = ChuyenDiThanhVien.objects.filter(user=user, trang_thai_tham_gia='DA_THAM_GIA').aggregate(t=Sum('chuyen_di__cd_do_dai_km'))
            return res['t'] or 0
        elif code == 'SUM_ELEVATION':
            res = ChuyenDiThanhVien.objects.filter(user=user, trang_thai_tham_gia='DA_THAM_GIA').aggregate(t=Sum('chuyen_di__cd_tong_do_cao_leo_m'))
            return res['t'] or 0
            
        elif code == 'HAS_TAG_COUNT':
            return ChuyenDiThanhVien.objects.filter(user=user, trang_thai_tham_gia='DA_THAM_GIA', chuyen_di__tags__slug=sub).count() if sub else 0
        elif code == 'DIFFICULTY_LEVEL':
            return ChuyenDiThanhVien.objects.filter(user=user, trang_thai_tham_gia='DA_THAM_GIA', chuyen_di__cung_duong__do_kho__ten__icontains=sub).count() if sub else 0
        elif code == 'VISIT_PROVINCE_COUNT':
            return ChuyenDiThanhVien.objects.filter(user=user, trang_thai_tham_gia='DA_THAM_GIA').values('chuyen_di__cung_duong__tinh_thanh').distinct().count()
        return 0

    def award_badge(self, user, badge):
        GameHuyHieuNguoiDung.objects.create(user=user, huy_hieu=badge, ngay_dat_duoc=timezone.now())
        print(f"🎉 [GAMIFICATION] Trao huy hiệu '{badge.ten}' cho {user.username}")

    # --- HÀM MỚI QUAN TRỌNG ĐỂ ĐỒNG BỘ ---
    def sync_badge_for_all_users(self, badge):
        users = User.objects.all()
        added, removed = 0, 0
        for user in users:
            metric = self.calculate_metric(user, badge)
            is_owned = GameHuyHieuNguoiDung.objects.filter(user=user, huy_hieu=badge).exists()
            
            if metric >= badge.gia_tri_muc_tieu:
                if not is_owned: # Đủ đk mà chưa có -> Trao
                    self.award_badge(user, badge)
                    added += 1
            else:
                if is_owned: # Có rồi mà giờ không đủ đk -> Thu hồi
                    GameHuyHieuNguoiDung.objects.filter(user=user, huy_hieu=badge).delete()
                    print(f"❌ Thu hồi huy hiệu '{badge.ten}' của {user.username}")
                    removed += 1
        return added, removed