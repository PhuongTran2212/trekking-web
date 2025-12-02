# gamification/services.py
from django.db.models import Count, Sum
from django.utils import timezone
from .models import GameHuyHieu, GameHuyHieuNguoiDung
# Import các model từ các app khác (Dựa trên cấu trúc SQL bạn cung cấp)
from trips.models import ChuyenDiThanhVien, ChuyenDi
from community.models import CongDongBaiViet, CongDongBinhLuan, CongDongMediaBaiViet
from trips.models import ChuyenDiNhatKyHanhTrinh
from accounts.models import TaiKhoanThietBiCaNhan

class BadgeEngine:
    def check_all_badges(self, user):
        """
        Hàm này kiểm tra TẤT CẢ huy hiệu active cho một user.
        Nên gọi hàm này khi user hoàn thành một hành động quan trọng (kết thúc trip, đăng bài...)
        hoặc chạy định kỳ (cronjob).
        """
        active_badges = GameHuyHieu.objects.filter(is_active=True)
        owned_badge_ids = GameHuyHieuNguoiDung.objects.filter(user=user).values_list('huy_hieu_id', flat=True)

        new_badges = []
        for badge in active_badges:
            # Nếu đã có huy hiệu này rồi thì bỏ qua
            if badge.id in owned_badge_ids:
                continue

            # Tính toán chỉ số hiện tại của user
            current_metric = self.calculate_metric(user, badge)
            
            # Kiểm tra điều kiện (Rule Check)
            is_qualified = False
            if badge.toan_tu == 'GTE': # Lớn hơn hoặc bằng
                is_qualified = current_metric >= badge.gia_tri_muc_tieu
            elif badge.toan_tu == 'EQ': # Bằng chính xác
                is_qualified = current_metric == badge.gia_tri_muc_tieu

            # Nếu đủ điều kiện -> Trao huy hiệu
            if is_qualified:
                self.award_badge(user, badge)
                new_badges.append(badge)
        
        return new_badges

    def calculate_metric(self, user, badge):
        """Logic tính toán chi tiết dựa trên 'loai_dieu_kien'"""
        code = badge.loai_dieu_kien

        # --- NHÓM CHUYẾN ĐI ---
        if code == 'COUNT_TRIPS':
            # Đếm số chuyến đi đã tham gia (trạng thái 'DA_THAM_GIA')
            return ChuyenDiThanhVien.objects.filter(user=user, trang_thai_tham_gia='DA_THAM_GIA').count()
        
        elif code == 'COUNT_HOSTED_TRIPS':
            # Đếm số chuyến đi đã tổ chức và hoàn thành
            return ChuyenDi.objects.filter(nguoi_to_chuc=user, trang_thai='HOAN_THANH').count()

        elif code == 'SUM_DISTANCE':
            # Tổng km của các chuyến đã đi
            result = ChuyenDiThanhVien.objects.filter(
                user=user, trang_thai_tham_gia='DA_THAM_GIA'
            ).aggregate(total=Sum('chuyen_di__cd_do_dai_km'))
            return result['total'] or 0

        elif code == 'SUM_ELEVATION':
            # Tổng độ cao leo
            result = ChuyenDiThanhVien.objects.filter(
                user=user, trang_thai_tham_gia='DA_THAM_GIA'
            ).aggregate(total=Sum('chuyen_di__cd_tong_do_cao_leo_m'))
            return result['total'] or 0

        # --- NHÓM ĐỊA LÝ & TAG ---
        elif code == 'HAS_TAG_COUNT':
            # Đếm số chuyến đi có tag cụ thể (biến số phụ = slug tag)
            tag_slug = badge.bien_so_phu
            if not tag_slug: return 0
            return ChuyenDiThanhVien.objects.filter(
                user=user, 
                trang_thai_tham_gia='DA_THAM_GIA',
                chuyen_di__cung_duong__tags__slug=tag_slug # Giả định quan hệ qua Cung Đường hoặc trực tiếp Chuyến đi
            ).count()

        elif code == 'VISIT_PROVINCE_COUNT':
            # Đếm số tỉnh thành khác nhau (Distinct)
            return ChuyenDiThanhVien.objects.filter(
                user=user, 
                trang_thai_tham_gia='DA_THAM_GIA'
            ).values('chuyen_di__cung_duong__tinh_thanh').distinct().count()

        elif code == 'DIFFICULTY_LEVEL':
             # Đếm số chuyến đi có độ khó cụ thể (biến số phụ = tên độ khó hoặc ID)
            difficulty_level = badge.bien_so_phu # Ví dụ: 'Kho', 'De'
            return ChuyenDiThanhVien.objects.filter(
                user=user,
                trang_thai_tham_gia='DA_THAM_GIA',
                chuyen_di__cung_duong__do_kho__ten__icontains=difficulty_level
            ).count()

        # --- NHÓM CỘNG ĐỒNG ---
        elif code == 'COUNT_POSTS':
            return CongDongBaiViet.objects.filter(tac_gia=user).count()
        
        elif code == 'COUNT_COMMENTS':
            return CongDongBinhLuan.objects.filter(user=user).count()
        
        elif code == 'COUNT_PHOTOS':
            # Cộng ảnh trong bài viết + ảnh trong chuyến đi (nếu có bảng media chuyến đi)
            count_post_media = CongDongMediaBaiViet.objects.filter(bai_viet__tac_gia=user).count()
            # Giả sử có model ChuyenDiMedia
            # count_trip_media = ChuyenDiMedia.objects.filter(user=user).count()
            return count_post_media # + count_trip_media

        # --- NHÓM CÁ NHÂN ---
        elif code == 'COUNT_CHECKINS':
            return ChuyenDiNhatKyHanhTrinh.objects.filter(thanh_vien__user=user).count()

        elif code == 'COUNT_ITEMS':
            return TaiKhoanThietBiCaNhan.objects.filter(user=user).count()
        
        elif code == 'COUNT_COLLECTED_BADGES':
             # Đếm số huy hiệu user ĐANG sở hữu (trừ chính nó để tránh loop)
            return GameHuyHieuNguoiDung.objects.filter(user=user).count()

        return 0

    def award_badge(self, user, badge):
        """Lưu huy hiệu vào DB"""
        GameHuyHieuNguoiDung.objects.create(
            user=user, 
            huy_hieu=badge,
            ngay_dat_duoc=timezone.now()
        )
        # TODO: Tại đây có thể bắn Notification cho user
        print(f"🎉 Chúc mừng! User {user.username} nhận huy hiệu: {badge.ten}")