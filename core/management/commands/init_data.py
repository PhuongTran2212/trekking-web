import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction

# Import Models
from accounts.models import TaiKhoanHoSo
from core.models import TinhThanh, DoKho, The
from treks.models import CungDuongTrek, TrangThaiDuyet, CungDuongDanhGia
from trips.models import (
    ChuyenDi, ChuyenDiThanhVien, ChuyenDiTinNhan, ChuyenDiTimeline
)
from community.models import (
    CongDongBaiViet, CongDongBinhLuan, CongDongBinhChonBaiViet
)

# === DỮ LIỆU GIẢ LẬP ===
FAKE_REVIEWS = [
    ("Cảnh đẹp tuyệt vời, đáng để đi một lần trong đời!", 5),
    ("Đường đi hơi khó, nhiều dốc đứng, anh em nhớ tập thể lực kỹ.", 4),
    ("Mùa này đi hơi nhiều vắt, mọi người nhớ mang thuốc chống côn trùng.", 3),
    ("Săn mây thành công, đẹp ngỡ ngàng. Sẽ quay lại!", 5),
    ("Porter nhiệt tình, đồ ăn ngon. Tuyệt vời.", 5),
    ("Mệt bở hơi tai nhưng lên đỉnh thì phê.", 4),
    ("Không đẹp như ảnh mạng, hơi thất vọng xíu.", 3),
    ("Cung này phù hợp cho người mới (newbie), đi chill chill.", 4),
]

FAKE_CHATS = [
    "Mọi người tập trung ở đâu nhỉ?",
    "Mình đi xe máy lên, có ai đi cùng không?",
    "Nhớ mang theo áo ấm nhé, trên đó lạnh lắm.",
    "Đã chốt danh sách chưa ad ơi?",
    "Hóng quá đi thôi!",
    "Mình xin phép đến muộn 15p nhé.",
    "Có cần mang lều không hay thuê trên đó?",
    "Chuyến này có porter gùi đồ không?",
    "Alo alo 1234",
    "Tối nay off chốt đoàn nhé cả nhà."
]

FAKE_COMMENTS = [
    "Bài viết hay quá, cảm ơn bác đã chia sẻ.",
    "Ảnh đẹp quá, chụp bằng máy gì vậy ạ?",
    "Nhìn mê quá, nhất định phải đi chỗ này.",
    "Xin lịch trình chi tiết với bác ơi.",
    "Chi phí chuyến này khoảng bao nhiêu vậy?",
    "Hóng phần tiếp theo.",
    "Quá đẳng cấp!",
    "Team mình cũng vừa đi về, phê lắm."
]

FAKE_TITLES = [
    "Review chi tiết Lảo Thẩn 2N1Đ",
    "Kinh nghiệm leo Bạch Mộc Lương Tử mùa mưa",
    "Góc tìm bạn đồng hành đi Tà Xùa",
    "Những vật dụng không thể thiếu khi Trekking",
    "Bộ ảnh film chụp tại Hà Giang",
    "Cần pass lại đôi giày trekking size 42",
    "Hỏi về cung đường Tà Năng - Phan Dũng",
    "Nhật ký hành trình chinh phục Fansipan",
]

class Command(BaseCommand):
    help = 'Khoi tao du lieu mau phong phu va tuong tac cao'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Bắt đầu quy trình tái tạo dữ liệu...'))

        with transaction.atomic():
            # 1. XÓA DỮ LIỆU CŨ (Trừ Admin)
            self.stdout.write('--- Đang xóa dữ liệu cũ ---')
            ChuyenDiTinNhan.objects.all().delete()
            ChuyenDiTimeline.objects.all().delete()
            ChuyenDiThanhVien.objects.all().delete()
            ChuyenDi.objects.all().delete()
            
            CungDuongDanhGia.objects.all().delete()
            CungDuongTrek.objects.all().delete()
            
            CongDongBinhLuan.objects.all().delete()
            CongDongBinhChonBaiViet.objects.all().delete()
            CongDongBaiViet.objects.all().delete()
            
            # Giữ lại admin, xóa user thường
            User.objects.exclude(username='chizk23').delete()

            # 2. TẠO/LẤY ADMIN
            admin_user, created = User.objects.get_or_create(username='chizk23')
            if created:
                admin_user.set_password('123456')
                admin_user.is_superuser = True
                admin_user.is_staff = True
                admin_user.email = 'chizk23@example.com'
                admin_user.save()
            
            # 3. TẠO 9 USER MỚI
            self.stdout.write('--- Đang tạo 9 User mẫu ---')
            new_users = []
            user_info = [
                ('huyen_nguyen', 'Huyền', 'Nguyễn'), ('minh_tuan', 'Tuấn', 'Trần'),
                ('lan_anh', 'Lan', 'Phạm'), ('quoc_bao', 'Bảo', 'Lê'),
                ('thuy_tien', 'Tiên', 'Huỳnh'), ('duc_thang', 'Thắng', 'Ngô'),
                ('hoang_nam', 'Nam', 'Đỗ'), ('phuong_thao', 'Thảo', 'Vũ'),
                ('anh_khoa', 'Khoa', 'Lý')
            ]
            for username, first, last in user_info:
                u = User.objects.create_user(username=username, password='123456', first_name=first, last_name=last, email=f'{username}@example.com')
                # Tạo profile giả (nếu cần)
                try:
                    profile = u.taikhoanhoso
                    profile.gioi_thieu = f"Xin chào, mình là {first}. Mình đam mê xê dịch."
                    profile.save()
                except:
                    pass
                new_users.append(u)
            
            all_users = [admin_user] + new_users

            # 4. TẠO CORE DATA (Nếu chưa có)
            list_tinh = ['Lào Cai', 'Hà Giang', 'Yên Bái', 'Cao Bằng', 'Lâm Đồng', 'Quảng Bình', 'Đà Nẵng', 'Hòa Bình', 'Sơn La', 'Lai Châu', 'Thanh Hóa', 'Nghệ An', 'Bình Thuận', 'Khánh Hòa', 'Vĩnh Phúc']
            all_tinh = []
            for t in list_tinh:
                obj, _ = TinhThanh.objects.get_or_create(ten=t, defaults={'slug': slugify(t)})
                all_tinh.append(obj)

            list_dokho = ['Dễ', 'Trung bình', 'Khó', 'Rất khó', 'Chuyên gia']
            all_dokho = []
            for dk in list_dokho:
                obj, _ = DoKho.objects.get_or_create(ten=dk)
                all_dokho.append(obj)

            list_the = ['Săn mây', 'Cắm trại', 'Suối thác', 'Rừng nguyên sinh', 'Leo núi', 'Team building', 'Check-in', 'Biển đảo', 'Hang động']
            all_the = []
            for t in list_the:
                obj, _ = The.objects.get_or_create(ten=t, defaults={'slug': slugify(t)})
                all_the.append(obj)

            # 5. TẠO 30 CUNG ĐƯỜNG (TREKS) & ĐÁNH GIÁ (REVIEWS)
            self.stdout.write('--- Đang tạo 30 Cung đường & Đánh giá ---')
            trek_bases = ["Lảo Thẩn", "Ky Quan San", "Nhìu Cồ San", "Tà Chì Nhù", "Tà Xùa", "Fansipan", "Putaleng", "Pusilung", "Nam Kang Ho Tao", "Khang Su Văn", "Tả Liên Sơn", "Động Phong Nha", "Langbiang", "Bidoup", "Cực Đông", "Bù Gia Mập", "Chứa Chan", "Bà Đen", "Bạch Mã", "Ngũ Chỉ Sơn"]
            
            created_treks = []
            for i in range(30):
                base_name = random.choice(trek_bases)
                name = f"{base_name} - Tuyến {i+1}" if i > 15 else base_name # Tạo tên biến thể
                if i > 20: name = f"Khám phá {base_name} mở rộng"

                trek = CungDuongTrek.objects.create(
                    ten=name,
                    mo_ta=f"<p>Mô tả chi tiết cho cung đường <strong>{name}</strong>. Địa hình đa dạng, cảnh quan hùng vĩ.</p>",
                    dia_diem_chi_tiet=f"Xã bản {random.randint(1,100)}",
                    tinh_thanh=random.choice(all_tinh),
                    do_dai_km=random.randint(10, 80),
                    thoi_gian_uoc_tinh_gio=random.randint(12, 96),
                    tong_do_cao_leo_m=random.randint(500, 3500),
                    do_kho=random.choice(all_dokho),
                    mua_dep_nhat="Tháng 9 - Tháng 3 năm sau",
                    trang_thai=TrangThaiDuyet.DA_DUYET,
                    nguoi_tao=admin_user,
                )
                created_treks.append(trek)

                # Tạo đánh giá giả cho cung đường này
                # Random 3-7 user vào đánh giá
                reviewers = random.sample(all_users, k=random.randint(3, 8))
                for reviewer in reviewers:
                    content, rating = random.choice(FAKE_REVIEWS)
                    # Rating ngẫu nhiên lệch xíu
                    final_rating = max(1, min(5, rating + random.randint(-1, 1)))
                    CungDuongDanhGia.objects.create(
                        cung_duong=trek,
                        user=reviewer,
                        diem_danh_gia=final_rating,
                        binh_luan=content
                    )
            
            # 6. TẠO 50 CHUYẾN ĐI (TRIPS) & TƯƠNG TÁC (MEMBERS, CHAT, TIMELINE)
            self.stdout.write('--- Đang tạo 50 Chuyến đi & Tương tác ---')
            for i in range(50):
                trek_goc = random.choice(created_treks)
                host = random.choice(all_users)
                
                # Xác định thời gian để set trạng thái
                days_offset = random.randint(-60, 60) # Từ quá khứ 2 tháng đến tương lai 2 tháng
                start_date = timezone.now() + datetime.timedelta(days=days_offset)
                end_date = start_date + datetime.timedelta(days=random.randint(1, 3))
                
                trang_thai = 'CHO_DUYET'
                if days_offset < -2: 
                    trang_thai = 'DA_DONG' # Đã kết thúc
                elif days_offset > 0:
                    trang_thai = 'DANG_TUYEN'
                else:
                    trang_thai = 'DA_DONG' # Đang diễn ra coi như đóng tuyển

                # Tạo chuyến đi
                trip = ChuyenDi.objects.create(
                    ten_chuyen_di=f"Trekking {trek_goc.ten} - Nhóm {host.last_name}",
                    mo_ta="Tuyển thành viên đam mê xê dịch, không ngại khổ. Chi phí campuchia.",
                    cung_duong=trek_goc,
                    nguoi_to_chuc=host,
                    ngay_bat_dau=start_date,
                    ngay_ket_thuc=end_date,
                    so_luong_toi_da=random.randint(8, 20),
                    trang_thai=trang_thai,
                    che_do_rieng_tu='CONG_KHAI',
                    chi_phi_uoc_tinh=random.randint(1000000, 6000000),
                    dia_diem_tap_trung="Cổng BigC Thăng Long / Sân bay Tân Sơn Nhất",
                    
                    # Snapshot
                    cd_ten=trek_goc.ten,
                    cd_tinh_thanh_ten=trek_goc.tinh_thanh.ten,
                    cd_do_kho_ten=trek_goc.do_kho.ten if trek_goc.do_kho else "N/A",
                    cd_do_dai_km=trek_goc.do_dai_km
                )
                trip.tags.set(random.sample(all_the, k=random.randint(2, 4)))

                # Tạo Timeline (Lịch trình)
                ChuyenDiTimeline.objects.create(chuyen_di=trip, ngay=1, thoi_gian="06:00", hoat_dong="Tập trung & Xuất phát", thu_tu=1)
                ChuyenDiTimeline.objects.create(chuyen_di=trip, ngay=1, thoi_gian="12:00", hoat_dong="Ăn trưa tại điểm nghỉ", thu_tu=2)
                ChuyenDiTimeline.objects.create(chuyen_di=trip, ngay=1, thoi_gian="18:00", hoat_dong="Cắm trại & BBQ", thu_tu=3)
                ChuyenDiTimeline.objects.create(chuyen_di=trip, ngay=2, thoi_gian="05:00", hoat_dong="Đón bình minh & Săn mây", thu_tu=4)

                # Add Host vào
                ChuyenDiThanhVien.objects.create(chuyen_di=trip, user=host, vai_tro='TRUONG_DOAN', trang_thai_tham_gia='DA_THAM_GIA')

                # Add Members ngẫu nhiên
                potential_members = [u for u in all_users if u != host]
                # Số lượng đăng ký
                num_regs = random.randint(2, 12)
                reg_users = random.sample(potential_members, k=min(num_regs, len(potential_members)))
                
                for idx, mem in enumerate(reg_users):
                    # Random trạng thái tham gia
                    status_choice = 'DA_THAM_GIA'
                    if idx > 8: status_choice = 'DA_GUI_YEU_CAU' # Người đến sau thì chờ duyệt
                    elif idx == 0: status_choice = 'BI_TU_CHOI' # Xui thì bị từ chối

                    ChuyenDiThanhVien.objects.create(
                        chuyen_di=trip, user=mem, vai_tro='THANH_VIEN', trang_thai_tham_gia=status_choice
                    )

                    # Nếu đã tham gia thì cho Chat 1 câu
                    if status_choice == 'DA_THAM_GIA':
                        if random.choice([True, False]): # 50% cơ hội chat
                            ChuyenDiTinNhan.objects.create(
                                chuyen_di=trip,
                                nguoi_gui=mem,
                                noi_dung=random.choice(FAKE_CHATS)
                            )
                
                # Host chat 1 câu chào
                ChuyenDiTinNhan.objects.create(chuyen_di=trip, nguoi_gui=host, noi_dung="Chào mừng mọi người tham gia nhóm!")

            # 7. TẠO 50 BÀI VIẾT CỘNG ĐỒNG & TƯƠNG TÁC
            self.stdout.write('--- Đang tạo 50 Bài viết Cộng đồng & Tương tác ---')
            for i in range(50):
                author = random.choice(all_users)
                title = random.choice(FAKE_TITLES) + f" #{i+1}"
                
                post = CongDongBaiViet.objects.create(
                    tieu_de=title,
                    noi_dung=f"<p>Đây là nội dung chia sẻ của mình về chủ đề <strong>{title}</strong>. Mọi người cho ý kiến nhé!</p><p>Lorem ipsum dolor sit amet...</p>",
                    tac_gia=author,
                    trang_thai='da_duyet',
                    luot_binh_chon=random.randint(0, 10) # Số ảo ban đầu
                )
                post.tags.set(random.sample(all_the, k=random.randint(1, 3)))

                # Tạo Upvote (Bình chọn thực tế trong bảng)
                voters = random.sample(all_users, k=random.randint(0, 8))
                for voter in voters:
                    CongDongBinhChonBaiViet.objects.create(bai_viet=post, user=voter)
                
                # Cập nhật lại số lượt bình chọn cho khớp
                post.luot_binh_chon = len(voters)
                post.save()

                # Tạo Bình luận (Comments)
                commenters = random.sample(all_users, k=random.randint(0, 6))
                for commenter in commenters:
                    CongDongBinhLuan.objects.create(
                        bai_viet=post,
                        user=commenter,
                        noi_dung=random.choice(FAKE_COMMENTS)
                    )

        self.stdout.write(self.style.SUCCESS('=========================================='))
        self.stdout.write(self.style.SUCCESS(' HOÀN TẤT! DỮ LIỆU ĐÃ ĐƯỢC TẠO THÀNH CÔNG '))
        self.stdout.write(self.style.SUCCESS('=========================================='))
        self.stdout.write(self.style.SUCCESS('1. Admin: chizk23 / 123456'))
        self.stdout.write(self.style.SUCCESS('2. Users: huyen_nguyen, minh_tuan, ... / 123456'))
        self.stdout.write(self.style.SUCCESS('3. Data: 30 Treks, 50 Trips, 50 Posts + Full Reviews, Chats, Comments.'))